from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import calibrate_static, compare, compile_all, compile_skill, report_run
from .runtime import probe_runtime


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="capability-eval")
    root.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = root.add_subparsers(dest="command", required=True)
    compile_cmd = sub.add_parser("compile", help="compile Goal Contracts and capability topologies")
    compile_cmd.add_argument("--skill")
    compile_cmd.add_argument("--all", action="store_true")
    compile_cmd.add_argument("--write", action="store_true")
    compile_cmd.add_argument("--check", action="store_true")
    calibrate_cmd = sub.add_parser("calibrate", help="run deterministic evaluator controls")
    calibrate_cmd.add_argument("--static-only", action="store_true")
    compare_cmd = sub.add_parser("compare", help="compare canonical baseline and candidate")
    compare_cmd.add_argument("--skill", required=True)
    compare_cmd.add_argument("--candidate", required=True, type=Path)
    compare_cmd.add_argument("--baseline", type=Path)
    compare_cmd.add_argument("--run-plan", type=Path)
    compare_cmd.add_argument("--profile", required=True)
    compare_cmd.add_argument("--allow-model-calls", action="store_true")
    compare_cmd.add_argument("--max-tokens", type=int)
    report_cmd = sub.add_parser("report", help="validate and render an immutable run summary")
    report_cmd.add_argument("--run", required=True)
    report_cmd.add_argument("--promotion-trust-root", type=Path)
    report_cmd.add_argument("--approved-trust-policy-sha256")
    report_cmd.add_argument("--approved-trust-policy-revision")
    sub.add_parser("probe", help="probe local runtimes without model calls")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command == "compile":
        if args.all == bool(args.skill):
            raise SystemExit("choose exactly one of --all or --skill")
        payload = compile_all(repo_root, write=args.write) if args.all else compile_skill(repo_root, args.skill, write=args.write)
        if args.check:
            results = payload["results"] if args.all else [payload]
            drift: list[str] = []
            for result in results:
                slug = result["slug"]
                for kind, generated in (("contract", result["goal_contract"]), ("topology", result["topology"])):
                    directory = "contracts" if kind == "contract" else "topologies"
                    path = repo_root / "evals" / directory / f"{slug}.json"
                    if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != generated:
                        drift.append(f"{kind}:{slug}")
            payload["check_result"] = "drift" if drift else "pass"
            payload["drift"] = drift
            if drift:
                json.dump(payload, sys.stdout, indent=2)
                sys.stdout.write("\n")
                return 2
    elif args.command == "calibrate":
        payload = calibrate_static(repo_root)
    elif args.command == "compare":
        payload = compare(
            repo_root,
            args.skill,
            args.candidate.resolve(),
            args.profile,
            allow_model_calls=args.allow_model_calls,
            max_tokens=args.max_tokens,
            baseline=args.baseline.resolve() if args.baseline else None,
            run_plan=args.run_plan.resolve() if args.run_plan else None,
        )
    elif args.command == "report":
        payload = report_run(
            repo_root,
            args.run,
            trust_root=args.promotion_trust_root.resolve() if args.promotion_trust_root else None,
            approved_trust_policy_sha256=args.approved_trust_policy_sha256,
            approved_trust_policy_revision=args.approved_trust_policy_revision,
        )
    else:
        payload = probe_runtime(repo_root)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
