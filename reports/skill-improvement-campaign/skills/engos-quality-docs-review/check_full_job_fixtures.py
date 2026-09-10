#!/usr/bin/env python3
"""Check PUBLIC source/example integrity, never model quality or promotion."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from check_fixtures import link_ok

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "full-job-fixtures/journey"


def digest(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def main():
    before = digest(SOURCE)
    cases = json.loads((ROOT / "full-job-cases.json").read_text())["cases"]
    assert len(cases) == len({c["id"] for c in cases}) == 16
    for case in cases:
        assert case["request"] and case["required_outcomes"] and case["answers_public"]
        assert case["fixture"] is None or (ROOT / case["fixture"]).is_dir()
    draft = (ROOT / "full-job-fixtures/public-quickstart-example.md").read_text()
    commands = re.findall(r"```sh\n(.*?)\n```", draft, re.DOTALL)
    assert commands == ["python3 cli.py init --workspace demo",
                        "python3 cli.py summarize --workspace demo --input samples/events.csv"]
    for target in re.findall(r"\]\(([^)]+)\)", draft):
        assert (SOURCE / "docs" / target).is_file(), target
    with tempfile.TemporaryDirectory(prefix="docs-reader-control-") as temp:
        repo = Path(temp) / "repo"
        shutil.copytree(SOURCE, repo)
        def run(args):
            return subprocess.run([sys.executable, "-B", "cli.py", *args], cwd=repo,
                                  capture_output=True, text=True, timeout=10)
        summarize = ["summarize", "--workspace", "demo", "--input", "samples/events.csv"]
        fail = run(summarize)
        assert fail.returncode == 2 and "workspace is not initialized" in fail.stderr
        assert not (repo / "demo").exists()
        setup = run(["init", "--workspace", "demo"])
        success = run(summarize)
        assert setup.returncode == success.returncode == 0
        assert setup.stdout.strip() == "Workspace ready" and success.stdout.strip() == "events=3"
        # Deliberately wrong documented output must disagree with actual output.
        assert success.stdout.strip() != "events=4"
        # Hidden setup makes the old example pass: distinguish this from first use.
        repeated = run(summarize)
        assert repeated.returncode == 0
    assert before == digest(SOURCE), "source fixture changed"
    navigation = ROOT / "full-job-fixtures/navigation"
    navigation_before = digest(navigation)
    with tempfile.TemporaryDirectory(prefix="docs-navigation-control-") as temp:
        repo = Path(temp) / "repo"
        shutil.copytree(navigation, repo)
        prior = repo / "reports/docs-review/assessment.md"
        prior_bytes = prior.read_bytes()
        try:
            with prior.open("x") as report:
                report.write("must not overwrite")
        except FileExistsError:
            pass
        else:
            raise AssertionError("collision control did not fire")
        assert prior.read_bytes() == prior_bytes
        new = repo / "reports/docs-review/nav-review-new-assessment.md"
        with new.open("x") as report:
            report.write("Task: nav-review-new\nPublic example only.\n")
        same = repo / "reports/docs-review/ongoing-assessment.md"
        assert "Task: same-task-positive-control" in same.read_text()
        same.write_text(same.read_text() + "\nSame-task public update.\n")
        assert prior.read_bytes() == prior_bytes
        reference = repo / "docs/REFERENCE.md"
        facts, explanation = reference.read_text().split("## Why workspaces\n", 1)
        reference.write_text(facts.rstrip() + "\n")
        design = repo / "docs/DESIGN.md"
        design.write_text(design.read_text() + "\n## Why workspaces\n" + explanation)
        # Moving content alone breaks both incoming references; the fault fires.
        assert not link_ok(repo, "README.md", "docs/REFERENCE.md#why-workspaces")
        assert not link_ok(repo, "docs/OPS.md", "REFERENCE.md#why-workspaces")
        for filename in ("README.md", "docs/OPS.md"):
            path = repo / filename
            path.write_text(path.read_text().replace("REFERENCE.md#why-workspaces",
                                                     "DESIGN.md#why-workspaces"))
        assert link_ok(repo, "README.md", "docs/DESIGN.md#why-workspaces")
        assert link_ok(repo, "docs/OPS.md", "DESIGN.md#why-workspaces")
        assert link_ok(repo, "README.md", "docs/REFERENCE.md#commands")
        assert explanation in design.read_text()
        assert reference.read_text() == facts.rstrip() + "\n"
        assert (repo / "docs/LOCAL.md").read_bytes() == (navigation / "docs/LOCAL.md").read_bytes()
    assert navigation_before == digest(navigation)
    naming = ROOT / "full-job-fixtures/naming-workflow"
    metadata = json.loads((naming / "metadata.json").read_text())
    assert metadata["entrypoint"] == "python3 tools/pebble.py"
    assert (naming / "tools/pebble.py").is_file() and not (naming / "cli.py").exists()
    assert "python3 cli.py --help" in (naming / "README.md").read_text()
    assert "on: pull_request" in (naming / ".github/workflows/docs.yml").read_text()
    assert "only at release" in (naming / "README.md").read_text()
    print(json.dumps({"kind": "public_full_job_fixture_integrity", "status": "pass",
        "public_cases": len(cases), "missing_init_exit": fail.returncode,
        "documented_repair_exit": success.returncode, "observed_output": success.stdout.strip(),
        "wrong_output_control_rejected": True, "hidden_setup_control_passes": True,
        "source_tree_unchanged": True, "draft_relative_links_pass": True,
        "collision_rejected_prior_bytes_preserved": True,
        "noncolliding_new_report_and_explicit_same_task_update": True,
        "move_without_incoming_link_repairs_fails": True,
        "move_with_both_incoming_link_repairs_passes": True,
        "reference_facts_explanation_and_user_choices_preserved": True,
        "naming_metadata_workflow_seeds_present": True,
        "model_outcomes": "unrun; public example and fixture checks only",
        "model_calls": 0, "behavioral_claim": "none"}, indent=2))


if __name__ == "__main__":
    main()
