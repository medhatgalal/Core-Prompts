from pathlib import Path
import hashlib
import importlib.util
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "sources/capability-resources/engos-route-intent"
spec = importlib.util.spec_from_file_location(
    "routing_catalog_inspector", RESOURCES / "scripts/inspect_catalog.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(tmp_path):
    root = tmp_path / "core"
    directory = root / ".meta/capabilities"
    directory.mkdir(parents=True)
    hashes = {}
    for slug in ["alpha-skill", "beta-skill"]:
        p = directory / (slug + ".json")
        p.write_text(
            json.dumps(
                {"slug": slug, "layers": {"minimal": {"summary": "Fixture " + slug}}}
            )
        )
        hashes[slug] = hashlib.sha256(p.read_bytes()).hexdigest()
    table = tmp_path / "routing-relations.json"
    table.write_text(
        json.dumps(
            {
                "schema_version": "SkillRoutingRelations.v1",
                "catalog": {},
                "relationships": [
                    {
                        "id": "conditional",
                        "from": "alpha-skill",
                        "to": "beta-skill",
                        "kind": "sequence",
                        "when": "A result actually needs the other job",
                        "handoff": "Current artifact and scope",
                        "stop": "Required input or authority is missing",
                        "source_refs": [
                            {"slug": slug, "descriptor_sha256": sha}
                            for slug, sha in hashes.items()
                        ],
                    }
                ],
            }
        )
    )
    return root, table


def test_current_inventory_is_dynamic_and_relationship_drift_does_not_remove_a_skill(
    tmp_path,
):
    root, table = fixture(tmp_path)
    first = m.inspect(root, table_path=table)
    assert first["relationships"][0]["binding_status"] == "matched"
    descriptor = root / ".meta/capabilities/beta-skill.json"
    data = json.loads(descriptor.read_text())
    data["layers"]["minimal"]["summary"] = "Updated contract"
    descriptor.write_text(json.dumps(data))
    (root / ".meta/capabilities/new-skill.json").write_text(
        json.dumps({"slug": "new-skill", "layers": {"minimal": {"summary": "New job"}}})
    )
    result = m.inspect(root, table_path=table)
    assert set(result["skills"]) == {"alpha-skill", "beta-skill", "new-skill"}
    assert result["relationships"][0]["binding_status"] == "stale_or_missing"
    assert all(s["availability"] == "catalog_only" for s in result["skills"].values())
    assert result["native_discovery_verified"] is False
    descriptor.unlink()
    assert "beta-skill" not in m.inspect(root, table_path=table)["skills"]


def test_explicit_entry_observation_is_not_native_discovery_or_authority(tmp_path):
    root, table = fixture(tmp_path)
    packages = tmp_path / "session-skills"
    entry = packages / "custom-job/SKILL.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("Custom complete entry")
    result = m.inspect(root, [packages], table, ["custom-job", "missing-job"])
    assert (
        result["skills"]["custom-job"]["availability"]
        == "entry_observed_not_native_discovery"
    )
    assert result["unknown_requested_skills"] == ["missing-job"]
    assert result["grants_authority"] is False
    assert not (packages / ".meta").exists()


@pytest.mark.parametrize(
    "fault", ["missing-condition", "missing-binding", "unknown-kind"]
)
def test_malformed_relationships_are_rejected(tmp_path, fault):
    root, table = fixture(tmp_path)
    data = json.loads(table.read_text())
    edge = data["relationships"][0]
    if fault == "missing-condition":
        edge["when"] = ""
    if fault == "missing-binding":
        edge["source_refs"].pop()
    if fault == "unknown-kind":
        edge["kind"] = "execute-without-review"
    table.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        m.inspect(root, table_path=table)


def test_explicit_broken_root_is_not_silently_replaced_by_bundled_snapshot(tmp_path):
    _, table = fixture(tmp_path)
    with pytest.raises(ValueError):
        m.inspect(tmp_path / "missing", table_path=table)


def test_bundled_relationships_cover_each_current_descriptor_without_fixed_count():
    result = m.inspect(ROOT, table_path=RESOURCES / "routing-relations.json")
    assert set(result["skills"]) == {
        p.stem for p in (ROOT / ".meta/capabilities").glob("*.json")
    }
    assert {e["kind"] for e in result["relationships"]} >= {
        "sequence",
        "return",
        "iterate",
        "parallel",
    }
    assert all(e["binding_status"] == "matched" for e in result["relationships"])


@pytest.mark.parametrize("route,expected", [
    ("intake", {"references/intake-method.md"}),
    ("question_tools", {"references/question-tools.md"}),
    ("relationships", {"references/relationship-method.md", "routing-relations.json"}),
    ("catalog_inspection", {"scripts/inspect_catalog.py", "references/relationship-method.md", "routing-relations.json"}),
])
def test_resource_routes_are_complete_and_do_not_load_unrelated_methods(route, expected):
    from intent_pipeline.capability_resources import load_resource_bundle

    bundle = load_resource_bundle(RESOURCES, route)
    assert {r["path"] for r in bundle["resources"]} == expected
    for resource in bundle["resources"]:
        assert resource["content"].encode() == (RESOURCES / resource["path"]).read_bytes()
