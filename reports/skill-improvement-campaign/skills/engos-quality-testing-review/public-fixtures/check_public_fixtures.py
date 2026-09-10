"""Validate this fixed PUBLIC fixture pack; never execute submitted model code."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
CHILD = r'''
import json
import unittest
suite = unittest.defaultTestLoader.discover("tests")
result = unittest.TestResult()
suite.run(result)
print(json.dumps({
    "tests": result.testsRun,
    "failures": sorted(test.id() for test, _ in result.failures),
    "errors": sorted(test.id() for test, _ in result.errors),
    "skipped": len(result.skipped),
    "successful": result.wasSuccessful(),
}, sort_keys=True))
'''
ALWAYS_FAIL = '''import unittest
class Broken(unittest.TestCase):
    def test_false_failure(self):
        self.assertEqual(1, 2)
'''


def run_suite(source, existing, example=None):
    # Trusted authored snippets only. This process is not an untrusted-code sandbox.
    compile(source, "sut.py", "exec")
    with tempfile.TemporaryDirectory(prefix="testing-public-control-") as name:
        folder = Path(name)
        (folder / "tests").mkdir()
        (folder / "sut.py").write_text(source)
        (folder / "tests/test_existing.py").write_text(existing)
        if example is not None:
            (folder / "tests/test_example.py").write_text(example)
        proc = subprocess.run(
            [sys.executable, "-B", "-c", CHILD], cwd=folder,
            capture_output=True, text=True, timeout=10, check=True,
        )
        if proc.stderr:
            raise AssertionError(proc.stderr)
        return json.loads(proc.stdout)


def main():
    manifest = json.loads((ROOT / "mutants.json").read_text())
    observations = []
    for repetition in range(2):
        for case in ("lease", "retry"):
            folder = ROOT / case
            source = (folder / "sut.py").read_text()
            existing = (folder / "tests/test_existing.py").read_text()
            example = (folder / "public-controls/test_example.py").read_text()
            safe = (folder / "public-controls/safe_alternative.py").read_text()
            for variant, code in (("reference", source), ("safe_alternative", safe)):
                result = run_suite(code, existing, example)
                assert result["successful"] and result["tests"] > 1 and not result["skipped"], result
                observations.append(dict(repetition=repetition, case=case, variant=variant,
                                         control="correct_implementation", result=result))
            for mutant in (m for m in manifest["mutants"] if m["case"] == case):
                code = source
                for edit in mutant["edits"]:
                    assert code.count(edit["before"]) == 1, mutant["id"]
                    code = code.replace(edit["before"], edit["after"], 1)
                compile(code, mutant["id"], "exec")
                assert code != source
                result = run_suite(code, existing, example)
                assert not result["errors"] and not result["skipped"], result
                assert any(t.endswith("." + mutant["expected_failure"])
                           for t in result["failures"]), (mutant["id"], result)
                observations.append(dict(repetition=repetition, case=case, variant=mutant["id"],
                                         control="assertion_detects_public_mutant", result=result))
                weak = run_suite(code, existing)
                assert weak["successful"] and weak["tests"] == 1, weak
                observations.append(dict(repetition=repetition, case=case, variant=mutant["id"],
                                         control="existing_suite_misses_public_mutant", result=weak))
            broken = run_suite(source, existing, ALWAYS_FAIL)
            assert not broken["errors"] and len(broken["failures"]) == 1, broken
            observations.append(dict(repetition=repetition, case=case, variant="reference",
                                     control="false_failure_is_observed", result=broken))
            invalid = run_suite(source, existing, "import nonexistent_public_fixture_dependency\n")
            assert invalid["errors"] and not invalid["failures"], invalid
            observations.append(dict(repetition=repetition, case=case, variant="reference",
                                     control="collection_error_is_not_mutant_detection", result=invalid))
    first = [{k: v for k, v in r.items() if k != "repetition"}
             for r in observations if r["repetition"] == 0]
    second = [{k: v for k, v in r.items() if k != "repetition"}
              for r in observations if r["repetition"] == 1]
    assert first == second, "Public control observations are not reproducible"
    inputs = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    print(json.dumps({
        "purpose": "public_fixture_integrity_only",
        "model_calls": 0,
        "promotion_evidence": False,
        "python": sys.version.split()[0],
        "repetitions": 2,
        "normalized_reproducible": True,
        "input_sha256": inputs,
        "observations": observations,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
