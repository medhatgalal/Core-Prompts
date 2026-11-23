"""The expanded skill files remain the byte and line-reference inputs to UAC."""
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from intent_pipeline.review_fragment import (
    FRAGMENT, RULES, authored_fragment, check_candidate, check_materializations, consumers,
)

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_repo(tmp_path):
    root = tmp_path.resolve()
    fragment = root / FRAGMENT
    fragment.parent.mkdir(parents=True)
    fragment.write_bytes(authored_fragment(ROOT))
    rules = root / RULES
    rules.parent.mkdir()
    rules.write_text(json.dumps({"review_fragment_consumers": ["first", "second"]}))
    prefix = b"# Local skill\n\n## Recommendation Artifact Review\n\nLocal trigger.\n\n"
    for slug, suffix in [("first", b""), ("second", b"\n## Another section\nRetained.\n")]:
        (root / "ssot" / f"{slug}.md").write_bytes(prefix + fragment.read_bytes() + suffix)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "--", FRAGMENT.as_posix()], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=fixture@example.invalid", "-c", "user.name=Fixture",
                    "-c", "commit.gpgSign=false", "-c", "core.hooksPath=/dev/null",
                    "commit", "-qm", "prior fragment"], cwd=root, check=True)
    return root


def test_repository_consumers_embed_the_same_bytes_in_every_provider():
    fragment = authored_fragment(ROOT)
    inventory = consumers(ROOT)
    assert len(inventory) == 12
    assert set(inventory) == {p.stem for p in (ROOT / "ssot").glob("*.md") if fragment in p.read_bytes()}
    check_materializations(ROOT)
    for provider in ("codex", "claude", "gemini", "grok", "kiro"):
        for slug in inventory:
            path = ROOT / f".{provider}/skills/{slug}/SKILL.md"
            assert path.read_bytes().count(fragment) == 1, str(path)


def test_sync_preserves_neighbors_and_is_retryable(source_repo):
    sync = load_script("sync-review-fragment").synchronize
    previous = authored_fragment(source_repo)
    paths = [source_repo / "ssot" / f"{s}.md" for s in consumers(source_repo)]
    originals = [p.read_bytes() for p in paths]
    updated = previous.replace(b"dispatches and counts", b"assigns and counts")
    (source_repo / FRAGMENT).write_bytes(updated)
    with pytest.raises(ValueError, match="first: shared review text differs"):
        sync(source_repo, write=False)
    # An interrupted previous sync already completed the first file.
    paths[0].write_bytes(originals[0].replace(previous, updated))
    assert sync(source_repo, write=True) == 1
    assert [p.read_bytes() for p in paths] == [s.replace(previous, updated) for s in originals]
    assert sync(source_repo, write=True) == 0
    check_materializations(source_repo)


@pytest.mark.parametrize("damage", ["drift", "duplicate", "missing", "misplaced"])
def test_sync_refuses_ambiguous_or_modified_copies_before_writes(source_repo, damage):
    sync = load_script("sync-review-fragment").synchronize
    fragment = authored_fragment(source_repo)
    (source_repo / FRAGMENT).write_bytes(fragment.replace(b"dispatches and counts", b"assigns and counts"))
    first = source_repo / "ssot/first.md"
    before = first.read_bytes()
    second = source_repo / "ssot/second.md"
    damaged = {
        "drift": fragment.replace(b"no round cap", b"a round cap"),
        "duplicate": fragment + fragment,
        "missing": b"Missing\n",
        "misplaced": b"## Other section\n" + fragment,
    }[damage]
    second.write_bytes(second.read_bytes().replace(fragment, damaged))
    with pytest.raises(ValueError, match="second"):
        sync(source_repo, write=True)
    assert first.read_bytes() == before


def test_uac_checks_the_selected_candidate_before_canonical_writes(source_repo, monkeypatch):
    uac = load_script("uac-import")
    monkeypatch.setattr(uac, "ROOT", source_repo)
    path = source_repo / "ssot/first.md"
    original = path.read_bytes()
    local_edit = original.decode().replace("Local trigger.", "### Local scope\nNew local trigger.")
    local_edit = "# Independent task\n### Three Roles\nLocal definitions.\n" + local_edit
    check_candidate(source_repo, "first", local_edit.rstrip("\n"))
    check_candidate(source_repo, "unregistered", "Its own contract.")
    check_candidate(source_repo / "isolated", "new-skill", "Fresh standalone input.")
    drift = local_edit.replace("no round cap", "a one-round limit")
    monkeypatch.setattr(uac, "_safe_apply_ssot_text", lambda *a, **kw: (drift, None))
    payload = {"status": "accepted", "source": {"normalized_source": str(path)},
               "cross_analysis": {"fit_assessment": "fits_cleanly"},
               "manifest": {"slug": "first", "layers": {"minimal": {"capability_type": "skill",
                            "summary": "Review", "required_inputs": [], "expected_outputs": []},
                            "expanded": {"adjustment_recommendations": []}}},
               "benchmark_sources": []}
    result = uac._apply_payload(payload, SimpleNamespace(yes=True, quality_loop="off"), [str(path)])
    assert result["status"] == "manual_review"
    assert "first: shared review text differs" in result["detail"]
    assert path.read_bytes() == original
    assert not (source_repo / ".meta/capabilities/first.json").exists()
