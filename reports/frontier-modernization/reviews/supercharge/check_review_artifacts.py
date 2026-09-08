"""Repeatable static verification for this independent preservation review."""
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / "src"))
from intent_pipeline.capability_resources import effective_capability_text, load_resource_bundle
from intent_pipeline.uac_baselines import text_sha256, validate_requirement_review

out = Path(__file__).resolve().parent
slug = "engos-meta-supercharge"
res = root / "sources/capability-resources" / slug
entry = (root / "reports/frontier-modernization/candidates" / f"{slug}.md").read_text()
effective = effective_capability_text(root, slug, entry)
current = (root / "reports/frontier-modernization/baseline" / f"{slug}.md").read_text()
historical = (root / "reports/frontier-modernization/baseline" / f"{slug}.historical.md").read_text()

def block(text, marker):
    start = text.index(marker)
    end = text.index("\n```", start) + 4
    return text[start:end]

def table(text):
    start = text.index("| Section | Content |")
    return text[start:text.index("\n\n", start)]

contract = (res / "references/modules/contract.md").read_text()
catchup = (res / "references/modules/catchup.md").read_text()
gaslight = (res / "references/modules/gaslight.md").read_text()
assert block(current, "```json") == block(contract, "```json") == block(historical, "```json")
assert block(current, "```text\n/VALIDATE-CATCHUP") == block(catchup, "```text\n/VALIDATE-CATCHUP")
assert table(current) == table(catchup)
pattern = r"^\| (\d+) \| ([^|]+)\|"
base_tech = {int(i): name.strip() for i, name in re.findall(pattern, current, re.M)}
new_tech = {int(i): name.strip() for i, name in re.findall(pattern, gaslight, re.M)}
assert base_tech == new_tech and sorted(new_tech) == list(range(1, 14))
assert not re.search(r"/stop(?![-\w])", effective)
manifest = json.loads((res / "resource-map.json").read_text())
routes = {r: [x["path"] for x in load_resource_bundle(res, r)["resources"]] for r in manifest["routes"]}
assert set(routes) == {
    "/ult", "/catchup", "/basis", "/simple", "/invert", "/adversarial", "/contract", "/grade",
    "/full", "/gaslight", "/stop-ult", "/debate", "/debate /deep", "/adversarial /debate",
    "/adversarial /debate /deep", "help", "examples", "details", "model-guidance",
}
assert "references/modules/basis.md" not in routes["/full"]
assert routes["details"][1:] == ["references/modules/" + m + ".md" for m in (
    "ult", "catchup", "basis", "simple", "invert", "adversarial", "contract", "grade", "full", "gaslight", "stop-ult")]
results = {}
for label, original in (("current", current), ("historical", historical)):
    review = json.loads((out / f"{label}-requirement-review.json").read_text())
    failures = validate_requirement_review(review, slug=slug, original_text=original, candidate_text=entry, effective_text=effective)
    assert not failures, failures
    results[label] = {
        "mapped_lines": sum(r["source_end_line"] - r["source_start_line"] + 1 for r in review["requirements"]),
        "requirements": len(review["requirements"]), "validation_failures": failures,
    }
texts = {"current_baseline": current, "historical_baseline": historical, "candidate_entry": entry, "candidate_effective": effective}
payload = {
    "schema_version": "IndependentSuperchargeReviewChecks.v1",
    "checks": {
        "contract_json_exact_both_baselines": True, "catchup_table_exact_current": True,
        "catchup_validation_exact_current": True, "gaslight_ids_and_names_exact": True,
        "global_stop_absent": True, "all_declared_routes_assemble": True,
        "full_basis_opt_in": True, "details_module_order_exact": True,
    },
    "reviews": results, "routes": routes,
    "sizes": {k: {"lines": len(v.splitlines()), "words": len(v.split()), "bytes": len(v.encode()),
                  "estimated_tokens_characters_div_4": round(len(v) / 4), "sha256": text_sha256(v)} for k, v in texts.items()},
    "limits": ["Static assembly and shape checks only; no model experiment or runtime behavioral promotion.",
               "Provider source claims were not independently fact-checked by this semantic reviewer."],
}
(out / "review-checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"checks": payload["checks"], "reviews": results, "sizes": payload["sizes"]}, indent=2))
