"""Fixed public fixture checks only; not an evaluator for model submissions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
helper_path = ROOT.parent / "public-fixtures/check_public_fixtures.py"
spec = importlib.util.spec_from_file_location("public_controls", helper_path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def coverage_observation():
    # The current host has coverage.py already. No package install or network.
    with tempfile.TemporaryDirectory(prefix="testing-coverage-public-") as name:
        target = Path(name)
        for file in ("sut.py", "test_existing.py"):
            (target / file).write_bytes((ROOT / "coverage" / file).read_bytes())
        code = '''import coverage, json, unittest
cov = coverage.Coverage(branch=True, source=["sut"])
cov.start()
result = unittest.TestResult()
unittest.defaultTestLoader.discover(".", pattern="test_existing.py").run(result)
cov.stop()
assert result.wasSuccessful()
cov.json_report(outfile="coverage.json")
print(json.dumps({"version":coverage.__version__, "tests":result.testsRun}))
'''
        run = subprocess.run([sys.executable, "-B", "-c", code], cwd=target,
                             capture_output=True, text=True, timeout=15, check=True)
        report = json.loads((target / "coverage.json").read_text())
        file_report = report["files"]["sut.py"]
        assert file_report["summary"]["percent_covered"] == 100, file_report
        return {
            "disclosure": "actual authored-fixture coverage observation, not model evidence",
            "tool": json.loads(run.stdout),
            "measurement": "coverage.Coverage(branch=True, source=['sut']); unittest discovery; json_report",
            "source_sha256": hashlib.sha256((ROOT / "coverage/sut.py").read_bytes()).hexdigest(),
            "test_sha256": hashlib.sha256((ROOT / "coverage/test_existing.py").read_bytes()).hexdigest(),
            "scope": "sut.py only; no exclusions configured",
            "file_report": file_report,
        }


def main():
    observations = []
    mutations = {
        "orders": ("        db.commit()\n        return", "        # PUBLIC MUTANT: no commit\n        return",
                   "test_response_corresponds_to_persisted_row"),
        "coverage": ('return status != "settled"', 'return True',
                     "test_owner_cannot_cancel_settled_order"),
    }
    for repetition in range(2):
        for case, (before, after, failure) in mutations.items():
            folder = ROOT / case
            source = (folder / "sut.py").read_text()
            existing = (folder / "test_existing.py").read_text()
            example = (folder / "public-controls/test_example.py").read_text()
            assert source.count(before) == 1
            mutant = source.replace(before, after, 1)
            correct = helper.run_suite(source, existing, example)
            weak = helper.run_suite(mutant, existing)
            detected = helper.run_suite(mutant, existing, example)
            assert correct["successful"] and weak["successful"]
            assert not detected["errors"] and any(t.endswith(failure) for t in detected["failures"])
            observations.append(dict(repetition=repetition, case=case,
                                     correct=correct, weak=weak, detected=detected))
        with tempfile.TemporaryDirectory(prefix="testing-node-public-") as name:
            folder = Path(name)
            source = (ROOT / "intervals/sut.mjs").read_text()
            for file, origin in (("test_existing.mjs", "test_existing.mjs"),
                                 ("test_example.mjs", "public-controls/test_example.mjs")):
                (folder / file).write_bytes((ROOT / "intervals" / origin).read_bytes())
            before = "return a < d && c < b;"
            assert source.count(before) == 1
            results = {}
            for kind, code, tests in (
                ("correct", source, ["test_existing.mjs", "test_example.mjs"]),
                ("weak", source.replace(before, "return a <= d && c <= b;"), ["test_existing.mjs"]),
                ("detected", source.replace(before, "return a <= d && c <= b;"), ["test_existing.mjs", "test_example.mjs"]),
            ):
                (folder / "sut.mjs").write_text(code)
                run = subprocess.run(["node", "--test", "--test-reporter=tap", *tests],
                                     cwd=folder, capture_output=True, text=True, timeout=10)
                assert run.returncode == (1 if kind == "detected" else 0), run.stderr
                assert "SyntaxError" not in run.stdout and "ReferenceError" not in run.stdout
                if kind == "detected":
                    assert re.search(r"not ok \d+ - touching endpoints are disjoint", run.stdout)
                results[kind] = {"exit_code": run.returncode,
                                 "passes": int(re.search(r"# pass (\d+)", run.stdout)[1]),
                                 "failures": int(re.search(r"# fail (\d+)", run.stdout)[1])}
            observations.append(dict(repetition=repetition, case="intervals", **results))
    first = [{k: v for k, v in x.items() if k != "repetition"} for x in observations[:3]]
    second = [{k: v for k, v in x.items() if k != "repetition"} for x in observations[3:]]
    assert first == second
    html = (ROOT / "checkout/checkout.html").read_text()
    assert '<button type="button">Pay</button>' in html and 'role="status"' in html
    script = re.search(r"<script>(.*?)</script>", html, re.S)[1]
    with tempfile.TemporaryDirectory(prefix="testing-checkout-syntax-") as name:
        script_file = Path(name) / "checkout.js"
        script_file.write_text(script)
        subprocess.run(["node", "--check", str(script_file)], check=True, capture_output=True, timeout=10)
    observed_coverage = coverage_observation()
    expected_path = ROOT / "coverage/coverage-report.json"
    if expected_path.exists():
        assert json.loads(expected_path.read_text()) == observed_coverage, "Coverage input drift; review before replacing"
    else:
        raise AssertionError("Missing authored coverage-report.json; materialize it explicitly before fixture checks")
    cases = json.loads((ROOT / "cases.json").read_text())["cases"]
    assert len(cases) == 15 and len({x["id"] for x in cases}) == 15
    for case in cases:
        for path in case["input_files"]:
            assert (ROOT / path).is_file(), (case["id"], path)
    print(json.dumps({"purpose": "public_scenario_integrity_only", "model_calls": 0,
                      "promotion_evidence": False, "reproducible": True,
                      "observations": observations, "measured_coverage": observed_coverage,
                      "checkout": "markup_and_javascript_syntax_only_not_browser_execution",
                      "case_count": len(cases)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
