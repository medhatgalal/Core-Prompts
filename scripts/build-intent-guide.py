#!/usr/bin/env python3
# Build the portable intent guide from the shared catalog. Standard library only.
from __future__ import annotations
import argparse, hashlib, html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "https://gitlab.appian-stratus.com/medhat.galal/core-prompts"
MIRROR = "https://github.com/medhatgalal/Core-Prompts"


def payload(root=ROOT):
    path = root / ".meta/intent-routing.json"
    raw = path.read_bytes()
    catalog = json.loads(raw)
    jobs = json.loads((root / ".meta/skill-job-map.json").read_text())["skills"]
    if catalog.get("schema_version") != "IntentRouting.v1":
        raise ValueError("Unsupported intent catalog schema")
    if not catalog.get("routes") or not isinstance(
        catalog.get("selection_rules"), list
    ):
        raise ValueError("Routes and selection rules are required")
    seen = set()
    for route in catalog["routes"]:
        if not re.fullmatch(r"[a-z][a-z0-9-]+", route["id"]) or route["id"] in seen:
            raise ValueError("Duplicate or unsafe route id")
        seen.add(route["id"])
        for key in ["title", "intent", "why", "output", "prompt", "next"]:
            if not isinstance(route.get(key), str) or not route[key].strip():
                raise ValueError("Missing route text: " + key)
        for slug in [route["entry_skill"]] + [
            s["skill"] for s in route.get("steps", [])
        ]:
            if slug not in jobs or not (root / "ssot" / f"{slug}.md").is_file():
                raise ValueError("Unknown canonical skill: " + slug)
        for step in route.get("steps", []):
            if not all(
                isinstance(step.get(k), str) and step[k].strip()
                for k in ["label", "when", "skip_when", "output", "next"]
            ):
                raise ValueError("Incomplete step contract")
    intake = catalog.get("intake")
    if not isinstance(intake, dict) or not isinstance(intake.get("questions"), list):
        raise ValueError("Intake questions are required")
    questions = {q["id"]: q for q in intake["questions"]}
    if (
        len(questions) != len(intake["questions"])
        or intake.get("start") not in questions
    ):
        raise ValueError("Duplicate or missing intake question")
    for question in questions.values():
        if (
            not question.get("question")
            or not question.get("why")
            or not question.get("options")
        ):
            raise ValueError("Incomplete intake question")
        if not any(
            o.get("allow_text") and o.get("ask_assistant") for o in question["options"]
        ):
            raise ValueError("Every intake question requires an Other/free-text answer")
        choices = set()
        for option in question["options"]:
            if option["id"] in choices:
                raise ValueError("Duplicate intake choice")
            choices.add(option["id"])
            destinations = sum(
                bool(option.get(k)) for k in ("next_question", "route", "ask_assistant")
            )
            if destinations != 1 or not option.get("label") or not option.get("detail"):
                raise ValueError("Incomplete or ambiguous intake choice")
            if option.get("next_question") and option["next_question"] not in questions:
                raise ValueError("Unknown next intake question")
            if option.get("route") and option["route"] not in seen:
                raise ValueError("Unknown intake route")
            if not option.get("next_question") and not option.get("rationale"):
                raise ValueError("Intake outcome requires an explanation")
    visited = set()

    def visit(key, active):
        if key in active:
            raise ValueError("Intake question cycle")
        visited.add(key)
        for option in questions[key]["options"]:
            if option.get("next_question"):
                visit(option["next_question"], active | {key})

    visit(intake["start"], set())
    if visited != set(questions):
        raise ValueError("Unreachable intake question")
    skills = [
        {"slug": slug, "primary_job": v["primary_job"], "use_when": v["use_when"]}
        for slug, v in sorted(jobs.items())
    ]
    return {
        **catalog,
        "skills": skills,
        "primary": PRIMARY,
        "mirror": MIRROR,
        "routing_sha256": hashlib.sha256(raw).hexdigest(),
    }


def render(root=ROOT):
    data = payload(root)
    embedded = (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
    )
    template = (root / "scripts/templates/intent-guide.html").read_text()
    if template.count("__ROUTING_DATA__") != 1:
        raise ValueError("Template must have one data placeholder")
    return template.replace("__ROUTING_DATA__", embedded)


def svg(root=ROOT):
    data = payload(root)
    ids = [
        "rough-problem",
        "competing-proposals",
        "shape-up",
        "small-change",
        "unexplained-failure",
        "unclear-feature",
    ]
    routes = {r["id"]: r for r in data["routes"]}
    rows = []
    for i, key in enumerate(ids):
        r = routes[key]
        y = 92 + i * 75
        label = html.escape(r["title"])
        owner = html.escape(r["entry_skill"])
        rows.append(
            f'<rect x="24" y="{y}" width="400" height="60" rx="10" fill="#25392b" stroke="#7aa981"/><text x="42" y="{y + 34}" fill="#f0f2ed" font-size="18">{label}</text><path d="M435 {y + 30}h38m-8-8 8 8-8 8" stroke="#b8efbd" fill="none"/><rect x="488" y="{y}" width="680" height="60" rx="10" fill="#202321" stroke="#49534c"/><text x="508" y="{y + 34}" fill="#f0f2ed" font-size="17">{owner}</text>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="590" viewBox="0 0 1200 590" role="img" aria-labelledby="title desc"><title id="title">Start with intent, then choose the next skill</title><desc id="desc">Six common user intents map to their existing Core-Prompts skill owners. Accepted artifacts, actual availability and permissions still govern the next action.</desc><rect width="1200" height="590" rx="14" fill="#171918"/><g font-family="system-ui,sans-serif"><text x="24" y="40" fill="#b8efbd" font-size="24">Describe the job. Your assistant recommends the first missing step.</text><text x="24" y="68" fill="#a7b1a9" font-size="16">Skip completed work. Full Shape Up keeps its conductor and human decisions.</text>'
        + "".join(rows)
        + "</g></svg>\n"
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    outputs = {
        ROOT / "docs/guide/index.html": render(),
        ROOT / "docs/guide/intent-flow.svg": svg(),
        ROOT / ".kiro/steering/intent-routing.json": (
            ROOT / ".meta/intent-routing.json"
        ).read_text(),
    }
    bad = []
    for path, text in outputs.items():
        if a.check:
            if not path.is_file() or path.read_text() != text:
                bad.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if bad:
        p.exit(1, "Stale intent guide: " + ", ".join(bad) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "mode": "check" if a.check else "build",
                "skills": len(payload()["skills"]),
                "outputs": [str(p.relative_to(ROOT)) for p in outputs],
            }
        )
    )


if __name__ == "__main__":
    main()
