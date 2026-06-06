#!/usr/bin/env python3
"""eng-report: deterministic engineering progress report generator.

Data layer: pure git → structured metrics → HTML.
AI narrative layer: optional, called via stdin/stdout protocol.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = Path.home() / ".kiro" / "skills" / "eng-report" / "config.yaml"
DEFAULT_OUTPUT_DIR = Path("/tmp") / date.today().isoformat()
BOT_PATTERNS = re.compile(
    r"^(appian\s+ci|.*-ops|.*-automation|root|hudson-.*|process\s+foundations)",
    re.IGNORECASE,
)
JIRA_PREFIX = re.compile(r"^[A-Z]{2,10}-\d+")
CONVENTIONAL_PREFIX = re.compile(r"^(\w+)[\s(:\!]")


# ── Git helpers ───────────────────────────────────────────────────────────────

def git(repo: Path, *args: str, check: bool = True) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=check
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def author_flags(authors: list[str]) -> list[str]:
    flags = []
    for a in authors:
        flags += ["--author", a]
    return flags


# ── Metrics gathering ─────────────────────────────────────────────────────────

def gather_repo_metrics(repo: Path, since: str, authors: list[str]) -> dict[str, Any]:
    """Run all git commands for one repo with optional author filter."""
    af = author_flags(authors)
    since_flag = [f"--since={since}"]

    commits_raw = git(repo, "log", *since_flag, "--no-merges", "--oneline", *af)
    commits = len(commits_raw.splitlines()) if commits_raw else 0

    merges_raw = git(repo, "log", *since_flag, "--merges", "--oneline", *af)
    merges = len(merges_raw.splitlines()) if merges_raw else 0

    # Lines added/deleted
    shortstat = git(repo, "log", *since_flag, "--shortstat", "--format=", *af)
    added = deleted = 0
    for line in shortstat.splitlines():
        m = re.search(r"(\d+) insertion", line)
        if m:
            added += int(m.group(1))
        m = re.search(r"(\d+) deletion", line)
        if m:
            deleted += int(m.group(1))

    # Commits per day
    dates_raw = git(repo, "log", *since_flag, "--no-merges", "--format=%ad", "--date=short", *af)
    daily: dict[str, int] = defaultdict(int)
    for d in dates_raw.splitlines():
        if d:
            daily[d] += 1

    # Contributors — use log --format to get consistent names matching author_flags
    contrib_raw = git(repo, "log", *since_flag, "--no-merges", "--format=%aN", *af)
    contrib_counts: dict[str, int] = defaultdict(int)
    for name in contrib_raw.splitlines():
        if name and not BOT_PATTERNS.match(name):
            contrib_counts[name] += 1
    contributors: list[tuple[int, str]] = sorted(
        [(v, k) for k, v in contrib_counts.items()], reverse=True
    )

    # Top changed files
    numstat = git(repo, "log", *since_flag, "--numstat", "--format=", *af)
    file_churn: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            f = parts[2]
            a, d = file_churn[f]
            file_churn[f] = (a + int(parts[0]), d + int(parts[1]))
    top_files = sorted(file_churn.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)[:10]

    # Category breakdown
    subjects = git(repo, "log", *since_flag, "--no-merges", "--format=%s", *af).splitlines()
    jira_count = sum(1 for s in subjects if re.match(r"^[A-Z][A-Z0-9]{1,9}-\d+[\s:]", s))
    is_jira = len(subjects) > 0 and jira_count / len(subjects) > 0.8

    categories: dict[str, int] = defaultdict(int)
    if is_jira:
        for s in subjects:
            m = re.match(r"^([A-Z][A-Z0-9]{1,9})-\d+", s)
            if m:
                categories[m.group(1)] += 1
    else:
        for s in subjects:
            m = CONVENTIONAL_PREFIX.match(s)
            if m and m.group(1).isalpha() and not m.group(1).isupper():
                categories[m.group(1)] += 1

    # Releases: tags in window
    since_dt = _parse_since(since)
    tags_raw = git(repo, "tag", "--sort=-creatordate",
                   "--format=%(creatordate:short) %(refname:short)")
    releases = []
    for line in tags_raw.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            try:
                tag_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
                if tag_date >= since_dt:
                    releases.append({"date": parts[0], "tag": parts[1]})
            except ValueError:
                pass
    releases = releases[:10]  # cap at 10

    # Recent commits in window (for commit listing section)
    commits_in_window_raw = git(repo, "log", *since_flag, "--no-merges", "--format=%ad %s", "--date=short", *af)
    commits_in_window = [{"date": l[:10], "subject": l[11:]} for l in commits_in_window_raw.splitlines() if len(l) > 11][:20]

    # Recent context (last 10 commits regardless of window — for low-activity reports)
    recent_raw = git(repo, "log", "--no-merges", "--format=%ad %s", "--date=short", "-10", *af)
    recent = [{"date": l[:10], "subject": l[11:]} for l in recent_raw.splitlines() if len(l) > 11]

    return {
        "commits": commits,
        "merges": merges,
        "added": added,
        "deleted": deleted,
        "net": added - deleted,
        "daily": dict(daily),
        "contributors": contributors,
        "top_files": top_files,
        "categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
        "is_jira": is_jira,
        "releases": releases,
        "recent": recent,
        "low_activity": commits < 5,
        "commits_in_window": commits_in_window,
        "commit_subjects": subjects,
    }


def _parse_since(since: str) -> date:
    """Convert since string to a date object."""
    since = since.strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", since):
        return datetime.strptime(since[:10], "%Y-%m-%d").date()
    m = re.match(r"(\d+)\s+(week|day|month)s?\s+ago", since)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"week": 7, "day": 1, "month": 30}[unit] * n
        return date.today() - timedelta(days=delta)
    return date.today() - timedelta(days=7)


def aggregate_metrics(repo_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge metrics from multiple repos into one aggregated result."""
    if len(repo_metrics) == 1:
        return repo_metrics[0]

    agg: dict[str, Any] = {
        "commits": sum(r["commits"] for r in repo_metrics),
        "merges": sum(r["merges"] for r in repo_metrics),
        "added": sum(r["added"] for r in repo_metrics),
        "deleted": sum(r["deleted"] for r in repo_metrics),
        "net": sum(r["net"] for r in repo_metrics),
        "daily": defaultdict(int),
        "contributors": defaultdict(int),
        "top_files": [],
        "categories": defaultdict(int),
        "is_jira": all(r["is_jira"] for r in repo_metrics),
        "releases": [],
        "recent": [],
        "low_activity": sum(r["commits"] for r in repo_metrics) < 5,
        "commits_in_window": [],
        "commit_subjects": [],
    }

    seen_tags: set[str] = set()
    all_files: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

    for r in repo_metrics:
        for d, c in r["daily"].items():
            agg["daily"][d] += c
        for count, name in r["contributors"]:
            agg["contributors"][name] += count
        for f, (a, d) in r["top_files"]:
            fa, fd = all_files[f]
            all_files[f] = (fa + a, fd + d)
        for cat, count in r["categories"].items():
            agg["categories"][cat] += count
        for rel in r["releases"]:
            if rel["tag"] not in seen_tags:
                seen_tags.add(rel["tag"])
                agg["releases"].append(rel)
        agg["commits_in_window"].extend(r.get("commits_in_window", []))
        agg["commit_subjects"].extend(r.get("commit_subjects", []))

    agg["daily"] = dict(agg["daily"])
    agg["contributors"] = sorted(
        [(v, k) for k, v in agg["contributors"].items()], reverse=True
    )
    agg["top_files"] = sorted(all_files.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)[:10]
    agg["categories"] = dict(sorted(agg["categories"].items(), key=lambda x: x[1], reverse=True))
    agg["releases"] = sorted(agg["releases"], key=lambda x: x["date"], reverse=True)
    agg["commits_in_window"] = sorted(agg["commits_in_window"], key=lambda x: x["date"], reverse=True)[:20]

    return agg


# ── HTML rendering ─────────────────────────────────────────────────────────────

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#e6edf3;font-family:system-ui,-apple-system,sans-serif;padding:24px;min-height:100vh}
.container{max-width:1200px;margin:0 auto}
.header{margin-bottom:28px;padding-bottom:16px;border-bottom:1px solid rgba(48,54,61,0.6)}
.header h1{color:#e6edf3;font-size:26px;margin-bottom:4px}
.header p{color:#8b949e;font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:24px}
.card{background:rgba(22,27,34,0.8);border:1px solid rgba(48,54,61,0.6);border-radius:12px;padding:16px;text-align:center}
.card-label{color:#8b949e;font-size:11px;text-transform:uppercase;margin-bottom:6px}
.card-value{color:#e6edf3;font-size:26px;font-weight:700}
.card-value.green{color:#3fb950}
.card-value.red{color:#f85149}
.card-value.blue{color:#58a6ff}
.section{background:rgba(22,27,34,0.8);border:1px solid rgba(48,54,61,0.6);border-radius:12px;padding:20px;margin-bottom:16px}
.section h3{color:#e6edf3;font-size:14px;margin-bottom:16px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.bar-chart{display:flex;align-items:flex-end;gap:3px;height:100px}
.bar-day{display:flex;flex-direction:column;align-items:center;gap:3px;flex:1}
.bar-fill{width:100%;border-radius:3px 3px 0 0;min-height:2px;background:#58a6ff}
.bar-fill.peak{background:linear-gradient(to top,#d29922,#f85149)}
.bar-label{font-size:10px;color:#8b949e}
.cat-row{margin-bottom:8px}
.cat-header{display:flex;justify-content:space-between;margin-bottom:3px;font-size:12px}
.cat-bar{height:16px;border-radius:3px;min-width:4px}
.churn-row{margin-bottom:10px}
.churn-name{color:#e6edf3;font-size:11px;margin-bottom:3px;word-break:break-all;opacity:0.85}
.churn-bars{display:flex;gap:4px;align-items:center;font-size:11px}
.churn-add{background:#3fb950;height:12px;border-radius:2px;min-width:2px}
.churn-del{background:#f85149;height:12px;border-radius:2px;min-width:2px}
.contrib-bar{display:flex;border-radius:4px;overflow:hidden;height:20px;margin-bottom:8px}
.contrib-seg{height:100%}
.commit-list{list-style:none}
.commit-list li{padding:6px 0;border-bottom:1px solid rgba(48,54,61,0.4);font-size:12px;color:#8b949e}
.commit-list li:last-child{border-bottom:none}
.commit-list .subject{color:#e6edf3}
.release-item{padding:6px 0;border-bottom:1px solid rgba(48,54,61,0.4);font-size:12px}
.release-item:last-child{border-bottom:none}
.release-tag{color:#a371f7;font-weight:600}
.release-date{color:#8b949e;margin-left:8px}
.per-repo-table{width:100%;border-collapse:collapse;font-size:12px}
.per-repo-table th{color:#8b949e;text-align:left;padding:6px 8px;border-bottom:1px solid rgba(48,54,61,0.6)}
.per-repo-table td{padding:6px 8px;border-bottom:1px solid rgba(48,54,61,0.3)}
.per-repo-table tr:last-child td{border-bottom:none}
.jira-note{color:#d29922;font-size:11px;margin-top:8px}
.no-activity{text-align:center;padding:40px 20px}
.no-activity .icon{font-size:40px;margin-bottom:12px}
.snapshot-item{padding:5px 0;border-bottom:1px solid rgba(48,54,61,0.3);font-size:12px}
.snapshot-item:last-child{border-bottom:none}
.footer{border-top:1px solid rgba(48,54,61,0.6);padding-top:12px;margin-top:24px;color:#8b949e;font-size:11px;text-align:center}
.staleness-warn{background:rgba(210,153,34,0.1);border:1px solid rgba(210,153,34,0.4);border-radius:8px;padding:10px 14px;margin-bottom:16px;color:#d29922;font-size:12px}
"""

CAT_COLORS = {
    "fix": "#58a6ff", "feat": "#3fb950", "refactor": "#a371f7",
    "test": "#d29922", "chore": "#8b949e", "docs": "#8b949e",
    "release": "#d29922", "ci": "#39d5ff", "perf": "#3fb950",
    "build": "#39d5ff", "style": "#8b949e", "revert": "#f85149",
}
CONTRIB_COLORS = ["#58a6ff", "#3fb950", "#a371f7", "#d29922", "#39d5ff",
                  "#f85149", "#8b949e", "#e6edf3"]


def _bar_chart(daily: dict[str, int], since: str) -> str:
    since_dt = _parse_since(since)
    days = [(since_dt + timedelta(days=i)).isoformat() for i in range(7)]
    max_c = max((daily.get(d, 0) for d in days), default=1) or 1
    bars = []
    for d in days:
        c = daily.get(d, 0)
        h = max(2, int(c / max_c * 90))
        is_peak = c == max_c and c > 0
        cls = "bar-fill peak" if is_peak else "bar-fill"
        label = d[8:]  # day number
        bars.append(
            f'<div class="bar-day">'
            f'<div class="{cls}" style="height:{h}px" title="{c} commits"></div>'
            f'<span class="bar-label">{label}</span>'
            f'</div>'
        )
    return f'<div class="bar-chart">{"".join(bars)}</div>'


def _cat_bars(categories: dict[str, int], is_jira: bool, limit: int = 10) -> str:
    if not categories:
        return "<p style='color:#8b949e;font-size:12px'>No data</p>"
    total = sum(categories.values())
    items = list(categories.items())[:limit]
    # If Jira and top key dominates (>90%), collapse to a note
    if is_jira and items and items[0][1] / total > 0.90:
        top_key = items[0][0]
        return (
            f'<p style="color:#8b949e;font-size:12px;line-height:1.6">'
            f'All commits tracked under <span style="color:#a371f7;font-weight:600">{top_key}</span> '
            f'({items[0][1]} of {total} commits)</p>'
            + (f'<p style="color:#8b949e;font-size:11px;margin-top:6px">Other keys: {", ".join(k for k,_ in items[1:4])}</p>' if len(items) > 1 else "")
        )
    max_v = items[0][1] if items else 1
    html = []
    for cat, count in items:
        pct = count / total * 100
        width = count / max_v * 100
        color = CAT_COLORS.get(cat.lower(), "#39d5ff")
        html.append(
            f'<div class="cat-row">'
            f'<div class="cat-header"><span style="color:#e6edf3">{cat}</span>'
            f'<span style="color:#8b949e">{count} ({pct:.0f}%)</span></div>'
            f'<div class="cat-bar" style="width:{width:.0f}%;background:{color}"></div>'
            f'</div>'
        )
    note = ""
    if is_jira:
        note = '<p class="jira-note">⚠ Jira-prefixed repo — top issue key prefixes</p>'
    return "".join(html) + note


def _churn_bars(top_files: list) -> str:
    if not top_files:
        return "<p style='color:#8b949e;font-size:12px'>No data</p>"
    max_total = max(a + d for _, (a, d) in top_files) or 1
    html = []
    for fname, (a, d) in top_files:
        short = fname.split("/")[-1]
        total = a + d
        add_pct = a / max_total * 100
        del_pct = d / max_total * 100
        html.append(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
            f'<span style="color:#c9d1d9;font-size:11px;word-break:break-all" title="{fname}">{short}</span>'
            f'<span style="color:#8b949e;font-size:10px"><span style="color:#3fb950">+{a}</span> <span style="color:#f85149">-{d}</span></span>'
            f'</div>'
            f'<div style="display:flex;gap:2px;height:6px;border-radius:3px;overflow:hidden;width:100%">'
            f'<div style="width:{add_pct:.1f}%;background:#3fb950;min-width:{"2px" if a>0 else "0"}"></div>'
            f'<div style="width:{del_pct:.1f}%;background:#f85149;min-width:{"2px" if d>0 else "0"}"></div>'
            f'</div>'
            f'</div>'
        )
    return "".join(html)


def _contrib_bar(contributors: list[tuple[int, str]]) -> str:
    if not contributors:
        return "<p style='color:#8b949e;font-size:12px'>No data</p>"
    total = sum(c for c, _ in contributors) or 1
    rows = []
    for i, (count, name) in enumerate(contributors[:8]):
        pct = count / total * 100
        color = CONTRIB_COLORS[i % len(CONTRIB_COLORS)]
        first = name.split()[0]
        rows.append(
            f'<div style="margin-bottom:7px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
            f'<span style="color:#e6edf3;font-size:12px">{name}</span>'
            f'<span style="color:#8b949e;font-size:11px">{count} ({pct:.0f}%)</span>'
            f'</div>'
            f'<div style="height:8px;width:{pct:.1f}%;background:{color};border-radius:3px;min-width:4px"></div>'
            f'</div>'
        )
    return "".join(rows)


def render_report(
    name: str,
    subtitle: str,
    metrics: dict[str, Any],
    since: str,
    repo_breakdown: list[dict] | None = None,
    scope_warning: str | None = None,
    narrative: dict[str, str] | None = None,
) -> str:
    # narrative may include: summary, themes, architecture, work_areas
    """Render a standalone HTML report from structured metrics."""
    m = metrics
    today = date.today().isoformat()
    avg_day = f"{m['commits'] / 7:.1f}" if m["commits"] else "0"
    commits_per_mr = f"{m['commits'] / m['merges']:.1f}" if m["merges"] else "—"
    top_contributor = m["contributors"][0][1] if m["contributors"] else "—"
    top_pct = int(m["contributors"][0][0] / max(m["commits"], 1) * 100) if m["contributors"] else 0

    body_parts: list[str] = []

    if scope_warning:
        body_parts.append(f'<div class="staleness-warn">⚠ {scope_warning}</div>')

    # Executive summary FIRST (leaders read top-down)
    if not m["low_activity"] and narrative and narrative.get("summary"):
        body_parts.append(
            f'<div class="section" style="border-left:3px solid #3fb950;margin-bottom:20px">'
            f'<h3>📊 Executive Summary</h3>'
            f'<p style="color:#e6edf3;line-height:1.7;font-size:13px">{narrative["summary"]}</p>'
            f'</div>'
        )

    # Metric cards
    net_cls = "green" if m["net"] >= 0 else "red"
    net_str = f"+{m['net']:,}" if m["net"] >= 0 else f"{m['net']:,}"
    contrib_count = len(m["contributors"])
    body_parts.append(f"""
<div class="cards">
  <div class="card"><div class="card-label">Commits</div><div class="card-value">{m['commits']}</div></div>
  <div class="card"><div class="card-label">MRs Merged</div><div class="card-value">{m['merges']}</div></div>
  <div class="card"><div class="card-label">Net Lines</div><div class="card-value {net_cls}">{net_str}</div></div>
  <div class="card"><div class="card-label">Releases</div><div class="card-value blue">{len(m['releases'])}</div></div>
  <div class="card"><div class="card-label">Contributors</div><div class="card-value">{contrib_count}</div></div>
  <div class="card"><div class="card-label">Top Contributor</div><div class="card-value" style="font-size:13px">{top_contributor.split()[0]} ({top_pct}%)</div></div>
</div>""")

    if m["low_activity"]:
        # Activity Snapshot mode
        body_parts.append('<div class="section"><h3>📋 Activity Snapshot</h3>')
        if m["commits"] == 0:
            body_parts.append('<p style="color:#8b949e;font-size:13px">No commits in this period.</p>')
        else:
            recent_window = [r for r in m["recent"] if r["date"] >= _parse_since(since).isoformat()]
            items = "\n".join(
                f'<div class="snapshot-item"><span style="color:#8b949e">{r["date"]}</span> '
                f'<span class="subject">{r["subject"][:100]}</span></div>'
                for r in recent_window
            )
            body_parts.append(items)
        body_parts.append("</div>")

        body_parts.append('<div class="section"><h3>🕐 Recent Context (last 10 commits)</h3>')
        items = "\n".join(
            f'<div class="snapshot-item"><span style="color:#8b949e">{r["date"]}</span> '
            f'<span class="subject">{r["subject"][:100]}</span></div>'
            for r in m["recent"]
        )
        body_parts.append(items + "</div>")
    else:
        # Full report
        # Key themes immediately after summary metrics
        if narrative and narrative.get("themes"):
            body_parts.append(
                f'<div class="section" style="margin-bottom:16px"><h3>💡 Key Themes</h3>'
                f'{narrative["themes"]}'
                f'</div>'
            )

        # Architecture evolution — before charts
        if narrative and narrative.get("architecture"):
            body_parts.append(
                f'<div class="section" style="margin-bottom:16px">'
                f'<h3>🏛 Architecture Evolution</h3>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px">'
                f'{narrative["architecture"]}'
                f'</div></div>'
            )

        # Daily chart + categories
        body_parts.append('<div class="grid2">')
        body_parts.append(
            f'<div class="section"><h3>📈 Daily Velocity</h3>'
            f'{_bar_chart(m["daily"], since)}</div>'
        )
        # Category / work areas section
        if m["is_jira"] and narrative and narrative.get("work_areas"):
            body_parts.append(
                f'<div class="section"><h3>🗂 Work Areas</h3>'
                f'<p style="color:#8b949e;font-size:10px;margin-bottom:12px">AI-summarized from commit messages</p>'
                f'{narrative["work_areas"]}'
                f'</div>'
            )
        elif m["is_jira"] and not (narrative and narrative.get("work_areas")):
            # Fallback: compact note
            cats = m["categories"]
            top = list(cats.items())[:1]
            total = sum(cats.values())
            note = f'All commits tracked under <span style="color:#a371f7;font-weight:600">{top[0][0]}</span> ({total} commits)' if top else "Jira-prefixed repo"
            body_parts.append(f'<div class="section"><h3>🏷 Commit Tracking</h3><p style="color:#8b949e;font-size:12px">{note}</p></div>')
        else:
            body_parts.append(
                f'<div class="section"><h3>🏷 Commit Categories</h3>'
                f'{_cat_bars(m["categories"], m["is_jira"])}</div>'
            )
        body_parts.append("</div>")

        # Churn + contributors
        body_parts.append('<div class="grid2">')
        body_parts.append(
            f'<div class="section"><h3>🔥 Code Churn</h3>'
            f'{_churn_bars(m["top_files"])}</div>'
        )
        body_parts.append(
            f'<div class="section"><h3>👥 Contributors</h3>'
            f'{_contrib_bar(m["contributors"])}</div>'
        )
        body_parts.append("</div>")

        # Releases
        if m["releases"]:
            items = "\n".join(
                f'<div class="release-item">'
                f'<span class="release-tag">{r["tag"]}</span>'
                f'<span class="release-date">{r["date"]}</span>'
                f'</div>'
                for r in m["releases"]
            )
            body_parts.append(f'<div class="section"><h3>🚀 Releases</h3>{items}</div>')

        # Per-repo breakdown (group entries only)
        if repo_breakdown:
            rows = "\n".join(
                f'<tr><td>{r["name"]}</td>'
                f'<td style="text-align:right">{r["commits"]}</td>'
                f'<td style="text-align:right">{r["merges"]}</td>'
                f'<td style="text-align:right;color:#3fb950">+{r["added"]}</td>'
                f'<td style="text-align:right;color:#f85149">-{r["deleted"]}</td>'
                f'<td style="text-align:right">{len(r["releases"])}</td></tr>'
                for r in repo_breakdown
            )
            total_commits = sum(r["commits"] for r in repo_breakdown)
            total_added = sum(r["added"] for r in repo_breakdown)
            total_deleted = sum(r["deleted"] for r in repo_breakdown)
            body_parts.append(
                f'<div class="section"><h3>📦 Per-Repo Breakdown</h3>'
                f'<table class="per-repo-table">'
                f'<tr><th>Repo</th><th>Commits</th><th>MRs</th>'
                f'<th>Added</th><th>Deleted</th><th>Releases</th></tr>'
                f'{rows}'
                f'<tr style="font-weight:600;border-top:1px solid rgba(48,54,61,0.8)">'
                f'<td>Total</td><td style="text-align:right">{total_commits}</td><td></td>'
                f'<td style="text-align:right;color:#3fb950">+{total_added}</td>'
                f'<td style="text-align:right;color:#f85149">-{total_deleted}</td><td></td></tr>'
                f'</table></div>'
            )



    footer_parts = [f"{name}", f"Generated: {today}"]
    if scope_warning:
        footer_parts.append("⚠ Org data may be stale")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>{name}</h1>
  <p style="color:#8b949e;font-size:13px">{subtitle}</p>
</div>
{"".join(body_parts)}
<div class="footer">{"  ·  ".join(footer_parts)}</div>
</div>
</body>
</html>"""


# ── Config loading ─────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    try:
        import yaml  # type: ignore
        with open(path) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Minimal YAML-subset parser for simple flat structures
        return _parse_simple_yaml(path)


def _parse_simple_yaml(path: Path) -> dict:
    """Parse the eng-report config.yaml without requiring PyYAML."""
    import re as _re
    config: dict = {"repos": [], "drive": {}, "local": {}}
    current_repo: dict | None = None
    current_scope: dict | None = None
    in_repos = False
    in_authors = False
    in_repo_list = False  # for group entries with `repos:` list

    with open(path) as f:
        for raw_line in f:
            line = raw_line.rstrip()
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # Skip comments and blanks
            if not stripped or stripped.startswith("#"):
                continue

            # Top-level keys
            if indent == 0:
                in_repos = stripped.startswith("repos:")
                in_authors = False
                in_repo_list = False
                if stripped.startswith("local:"):
                    current_repo = None
                elif stripped.startswith("drive:"):
                    current_repo = None
                continue

            if not in_repos:
                # Parse drive/local scalar values
                m = _re.match(r"(\w+):\s+(.+)", stripped)
                if m:
                    key, val = m.group(1), m.group(2).strip('"')
                    if line.startswith("  "):
                        section = "drive" if "folder" in key or "notify" in key or "chat" in key or "email" in key else "local"
                        config.setdefault(section, {})[key] = val
                continue

            # Repo entries (indent 2)
            if indent == 2 and stripped.startswith("- name:"):
                name = stripped.split(":", 1)[1].strip()
                current_repo = {"name": name}
                config["repos"].append(current_repo)
                current_scope = None
                in_authors = False
                in_repo_list = False
                continue

            if current_repo is None:
                continue

            # Repo-level keys (indent 4)
            if indent == 4:
                in_authors = False
                in_repo_list = False
                if stripped.startswith("path:"):
                    current_repo["path"] = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("remote:"):
                    current_repo["remote"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("label:"):
                    current_repo["label"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("category:"):
                    current_repo["category"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("repos:"):
                    current_repo.setdefault("repos", [])
                    in_repo_list = True
                elif stripped.startswith("scope:"):
                    current_scope = {}
                    current_repo["scope"] = current_scope
                continue

            # repo list items (indent 6, under `repos:`)
            if indent == 6 and in_repo_list and stripped.startswith("- "):
                current_repo.setdefault("repos", []).append(stripped[2:].strip())
                continue

            # Scope keys (indent 6)
            if indent == 6 and current_scope is not None:
                in_authors = False
                if stripped.startswith("tribe:"):
                    current_scope["tribe"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("team:"):
                    current_scope["team"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("business_unit:"):
                    current_scope["business_unit"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("resolved_at:"):
                    current_scope["resolved_at"] = stripped.split(":", 1)[1].strip().strip('"')
                elif stripped.startswith("authors:"):
                    current_scope["authors"] = []
                    in_authors = True
                continue

            # Author list items (indent 8)
            if indent == 8 and in_authors and current_scope is not None and stripped.startswith("- "):
                current_scope.setdefault("authors", []).append(stripped[2:].strip())
                continue

    return config


def _stale_warning(scope: dict, since: str) -> str | None:
    resolved_at = scope.get("resolved_at")
    if not resolved_at:
        return "Author list has no resolved_at date — may not reflect current org membership"
    since_dt = _parse_since(since)
    try:
        resolved_dt = datetime.strptime(resolved_at, "%Y-%m-%d").date()
        if since_dt < resolved_dt - timedelta(days=30):
            return f"Author list resolved {resolved_at} — may not reflect membership during this window"
    except ValueError:
        pass
    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def run_entry(entry: dict, since: str, output_dir: Path, author_filter: str | None = None, narrative: dict | None = None) -> dict[str, Any]:
    """Process one config entry and write its HTML file. Returns summary row."""
    name = entry.get("label", entry["name"])
    file_key = entry["name"]
    scope = entry.get("scope", {})
    authors: list[str] = scope.get("authors", [])
    # Individual author filter overrides scope authors
    if author_filter:
        authors = [author_filter]
        entry = {**entry, "label": author_filter, "name": entry["name"] + f"-{author_filter.replace(' ','-')}"}

    # Resolve repo paths (with remote bare-clone fallback)
    def resolve_repo_path(p: str, remote: str | None = None) -> Path:
        local = Path(p).expanduser()
        if local.exists():
            return local
        if not remote:
            return local  # will trigger "not found" warning below
        cache_dir = Path.home() / ".eng-report-cache"
        cache_dir.mkdir(exist_ok=True)
        bare = cache_dir / (local.name + ".git")
        if not bare.exists():
            print(f"  → cloning bare repo to {bare}", file=sys.stderr)
            subprocess.run(["git", "clone", "--bare", "--depth=90", remote, str(bare)],
                           check=True, capture_output=True)
        else:
            print(f"  → fetching {bare}", file=sys.stderr)
            subprocess.run(["git", "-C", str(bare), "fetch", "--depth=90"],
                           check=False, capture_output=True)
        return bare

    remote = entry.get("remote")
    if "path" in entry:
        repo_paths = [resolve_repo_path(entry["path"], remote)]
        is_group = False
    else:
        remotes = entry.get("remotes", [])
        repo_paths = [resolve_repo_path(p, remotes[i] if i < len(remotes) else None)
                      for i, p in enumerate(entry.get("repos", []))]
        is_group = len(repo_paths) > 1

    # Gather metrics per repo
    per_repo: list[dict] = []
    for rp in repo_paths:
        if not rp.exists():
            print(f"  ⚠ {rp} not found, skipping", file=sys.stderr)
            continue
        m = gather_repo_metrics(rp, since, authors)
        m["_repo_name"] = rp.name
        per_repo.append(m)

    if not per_repo:
        print(f"  ✗ {name}: no valid repos", file=sys.stderr)
        return {"name": name, "commits": 0, "merges": 0, "added": 0, "deleted": 0,
                "net": 0, "releases": 0, "top_contributor": "—"}

    # Aggregate if multiple repos
    agg = aggregate_metrics(per_repo)

    # Build subtitle
    scope_label = scope.get("team") or scope.get("tribe") or scope.get("business_unit") or ""
    repo_label = " + ".join(rp.name for rp in repo_paths)
    author_count = len(authors)
    subtitle_parts = [name]
    if scope_label:
        subtitle_parts.append(scope_label)
    subtitle_parts.append(repo_label)
    if author_count:
        subtitle_parts.append(f"{author_count} members")
    subtitle_parts.append(f"Since {since}")
    subtitle = " · ".join(subtitle_parts)

    # Staleness warning
    scope_warning = _stale_warning(scope, since) if scope else None

    # Per-repo breakdown for group entries
    breakdown = None
    if is_group:
        breakdown = [
            {
                "name": m["_repo_name"],
                "commits": m["commits"],
                "merges": m["merges"],
                "added": m["added"],
                "deleted": m["deleted"],
                "releases": m["releases"],
            }
            for m in per_repo
        ]

    html = render_report(
        name=name,
        subtitle=subtitle,
        metrics=agg,
        since=since,
        repo_breakdown=breakdown,
        scope_warning=scope_warning,
        narrative=narrative,
    )

    out_path = output_dir / f"{file_key}.html"
    out_path.write_text(html, encoding="utf-8")

    top_contributor = agg["contributors"][0][1] if agg["contributors"] else "—"
    top_pct = int(agg["contributors"][0][0] / max(agg["commits"], 1) * 100) if agg["contributors"] else 0
    print(f"  ✓ {name}: {agg['commits']} commits, {agg['net']:+,} lines → {out_path.name}", file=sys.stderr)

    return {
        "name": file_key,
        "commits": agg["commits"],
        "merges": agg["merges"],
        "added": agg["added"],
        "deleted": agg["deleted"],
        "net": agg["net"],
        "releases": len(agg["releases"]),
        "top_contributor": f"{top_contributor.split()[0]} ({top_pct}%)" if agg["contributors"] else "—",
    }


def build_index(rows: list[dict], output_dir: Path, config: dict, entries: list[dict]) -> None:
    """Build grouped _index.html — always generated, sections by category."""
    since = config.get("local", {}).get("window", "1 week ago")
    today = date.today().isoformat()

    # Map name → label and category from entries
    entry_meta = {e["name"]: {"label": e.get("label", e["name"]), "category": e.get("category", "Repos")} for e in entries}

    # Group rows by category
    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        cat = entry_meta.get(r["name"], {}).get("category", "Repos")
        label = entry_meta.get(r["name"], {}).get("label", r["name"])
        groups[cat].append({**r, "_label": label})

    CATEGORY_ORDER = ["Repos", "SBU", "Groups", "Teams", "Individuals"]

    def table_section(cat: str, cat_rows: list) -> str:
        total_c = sum(r["commits"] for r in cat_rows)
        rows_html = "\n".join(
            f'<tr>'
            f'<td><a href="{r["name"]}.html" style="color:#58a6ff;font-weight:500">{r["_label"]}</a></td>'
            f'<td style="text-align:right">{r["commits"]}</td>'
            f'<td style="text-align:right;color:{"#3fb950" if r["net"]>=0 else "#f85149"}">{"+" if r["net"]>=0 else ""}{r["net"]:,}</td>'
            f'<td style="text-align:right">{r["releases"]}</td>'
            f'<td style="color:#8b949e;font-size:12px">{r["top_contributor"]}</td>'
            f'</tr>'
            for r in cat_rows
        )
        return (
            f'<div class="section" style="margin-bottom:20px">'
            f'<h3 style="color:#e6edf3;font-size:14px;margin-bottom:12px">{cat} <span style="color:#8b949e;font-size:11px;font-weight:normal">({len(cat_rows)} · {total_c} commits)</span></h3>'
            f'<table class="index-table">'
            f'<tr><th>Report</th><th style="text-align:right">Commits</th><th style="text-align:right">Net Lines</th><th style="text-align:right">Releases</th><th>Top Contributor</th></tr>'
            f'{rows_html}'
            f'</table></div>'
        )

    sections = "".join(
        table_section(cat, groups[cat])
        for cat in CATEGORY_ORDER if cat in groups
    ) + "".join(
        table_section(cat, groups[cat])
        for cat in groups if cat not in CATEGORY_ORDER
    )

    total_commits = sum(r["commits"] for r in rows)
    total_added = sum(r["added"] for r in rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Engineering Reports — {today}</title>
<style>{CSS}
body{{padding:24px}}
.index-table{{width:100%;border-collapse:collapse;font-size:13px}}
.index-table th{{color:#8b949e;text-align:left;padding:8px 10px;border-bottom:1px solid rgba(48,54,61,0.6);font-weight:500}}
.index-table td{{padding:8px 10px;border-bottom:1px solid rgba(48,54,61,0.3)}}
.index-table tr:last-child td{{border-bottom:none}}
.index-table tr:hover td{{background:rgba(48,54,61,0.2)}}
a{{text-decoration:none}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>Engineering Reports — {today}</h1>
  <p style="color:#8b949e;font-size:13px">{len(rows)} reports · window: {since} · {total_commits} commits · +{total_added:,} lines added</p>
</div>
{sections}
<div class="footer">Generated: {today}</div>
</div>
</body>
</html>"""

    (output_dir / "_index.html").write_text(html, encoding="utf-8")
    print(f"  ✓ _index.html ({len(rows)} reports, {len(groups)} categories)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="eng-report: deterministic engineering progress report generator"
    )
    sub = parser.add_subparsers(dest="command")

    # run command
    p_run = sub.add_parser("run", help="Generate reports")
    p_run.add_argument("--config", default=str(DEFAULT_CONFIG))
    p_run.add_argument("--since", default=None, help="Override window (e.g. '2 weeks ago')")
    p_run.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    p_run.add_argument("--name", help="Generate only this entry by name")
    p_run.add_argument("--json-only", action="store_true", dest="json_only", help="Output metrics JSON to stdout only (no HTML written)")
    p_run.add_argument("--no-index", action="store_true", help="Skip _index.html generation")
    p_run.add_argument("--author", default=None, help="Generate report for a single person across all configured repos")
    p_run.add_argument("--narrative-file", default=None, dest="narrative_file",
                       help="JSON file mapping entry names to AI narrative {summary, themes, architecture, work_areas}")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    config = load_config(Path(args.config).expanduser())
    since = args.since or config.get("local", {}).get("window", "1 week ago")
    output_dir = Path(args.output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = config.get("repos", [])
    if args.name:
        entries = [e for e in entries if e["name"] == args.name]
        if not entries:
            print(f"error: no entry named '{args.name}'", file=sys.stderr)
            sys.exit(1)

    author = getattr(args, "author", None)
    if author:
        # Individual report: run against all unique repo paths with author filter
        seen_paths: set[str] = set()
        author_entries = []
        for e in entries:
            paths = [e.get("path")] if "path" in e else e.get("repos", [])
            for p in paths:
                if p and p not in seen_paths:
                    seen_paths.add(p)
                    author_entries.append({"name": f"individual-{author.replace(' ','-')}", "label": author, "path": p, "category": "Individuals"})
        entries = author_entries[:1]  # one combined entry using first repo; TODO: multi-repo merge

    # Load optional AI narrative file
    narratives: dict[str, dict] = {}
    if getattr(args, "narrative_file", None) and args.narrative_file:
        with open(args.narrative_file) as f:
            narratives = json.load(f)

    json_only = getattr(args, "json_only", False)
    def log(*a): print(*a, file=sys.stderr if json_only else sys.stdout)
    log(f"eng-report run — {len(entries)} entries, window: {since}")
    log(f"Output: {output_dir}\n")

    rows = []
    for entry in entries:
        narrative = narratives.get(entry["name"])
        row = run_entry(entry, since, output_dir, author_filter=author, narrative=narrative)
        rows.append(row)

    if getattr(args, "json_only", False):
        # Print only JSON to stdout; progress went to stderr
        print(json.dumps(rows, indent=2))
        return

    if not args.no_index and not args.name and not getattr(args, "author", None):
        print()
        build_index(rows, output_dir, config, entries)

    if not getattr(args, "json_only", False):
        print(f"\nDone. Open: {output_dir}/_index.html")


if __name__ == "__main__":
    main()
