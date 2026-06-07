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
    """Run a git command in repo, return stdout or empty string on error."""
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, check=check
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def author_flags(authors: list[str]) -> list[str]:
    """Convert list of author names to git --author flags."""
    flags = []
    for a in authors:
        flags += ["--author", a]
    return flags


# ── Metrics gathering ─────────────────────────────────────────────────────────


def _remote_web_url(repo: Path) -> str:
    """Convert git remote URL to HTTPS web base URL."""
    def _to_https(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("git@"):
            raw = raw[4:]
            host, path_part = raw.split(":", 1)
            return f"https://{host}/{path_part.rstrip('.git')}"
        if raw.startswith("https://"):
            return raw.rstrip(".git")
        return ""

    # Try all remotes, prefer prod/origin/appian, filter out forks
    all_remotes_raw = git(repo, "remote", "-v", check=False)
    best = ""
    for line in all_remotes_raw.splitlines():
        if "(fetch)" not in line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        remote_name, url = parts[0], parts[1]
        https = _to_https(url)
        if not https:
            continue
        # Prefer canonical remotes over forks
        # Prefer named canonical remotes
        if remote_name in ("origin", "prod", "appian"):
            best = https
            break  # Use first canonical remote found
        elif not best:
            best = https
    return best


def _default_branch(repo: Path) -> str:
    """Get the default branch name (bare, e.g. 'main')."""
    ref = _default_branch_ref(repo)
    return ref.split("/")[-1] if "/" in ref else ref


def _default_branch_ref(repo: Path) -> str:
    """Get the full remote-tracking ref for the default branch (e.g. 'origin/main')."""
    for remote in ("origin", "appian", "prod", "dev"):
        b = git(repo, "symbolic-ref", f"refs/remotes/{remote}/HEAD", check=False)
        if b:
            # b is like 'refs/remotes/origin/main' — return 'origin/main'
            parts = b.strip().split("refs/remotes/")
            return parts[-1] if len(parts) > 1 else b.strip()
    # Fallback: find which remote/branch actually exists
    for remote in ("origin", "appian", "prod", "dev"):
        for branch in ("main", "master", "develop"):
            if git(repo, "rev-parse", "--verify", f"{remote}/{branch}", check=False):
                return f"{remote}/{branch}"
    return "main"


def _parse_shortstat(raw: str) -> tuple[int, int]:
    """Parse git shortstat output into (added, deleted) totals."""
    added = deleted = 0
    for line in raw.splitlines():
        m = re.search(r"(\d+) insertion", line)
        if m:
            added += int(m.group(1))
        m = re.search(r"(\d+) deletion", line)
        if m:
            deleted += int(m.group(1))
    return added, deleted


def _parse_daily(raw: str) -> dict[str, int]:
    """Parse date-per-line output into daily commit counts."""
    daily: dict[str, int] = defaultdict(int)
    for d in raw.splitlines():
        if d:
            daily[d] += 1
    return dict(daily)


def gather_repo_metrics(repo: Path, since: str, authors: list[str], branch_scope: str = "all") -> dict[str, Any]:
    """Run all git commands for one repo with optional author filter.
    branch_scope: 'all' (shipped+inflight), 'shipped' (default branch only), 'in-flight' (branches only)"""
    af = author_flags(authors)
    since_flag = [f"--since={since}"]

    web_url = _remote_web_url(repo)
    default_branch = _default_branch(repo)

    # Use the full remote-tracking ref (e.g. 'origin/main', 'dev/main')
    _branch_ref = _default_branch_ref(repo)
    shipped_ref = [_branch_ref]  # commits on default branch
    inflight_ref = ["--remotes", "--not", _branch_ref]  # commits NOT on default

    # --- SHIPPED metrics (on default branch) ---
    # Use --first-parent without --no-merges to handle squash-merge repos
    shipped_commits_raw = git(repo, "log", *since_flag, "--first-parent", *shipped_ref, "--oneline", *af)
    shipped_commits = len(shipped_commits_raw.splitlines()) if shipped_commits_raw else 0
    shipped_shas_raw = git(repo, "log", *since_flag, "--first-parent", *shipped_ref, "--format=%H", *af)
    shipped_shas = set(shipped_shas_raw.splitlines()) if shipped_shas_raw else set()

    shipped_stat = git(repo, "log", *since_flag, "--first-parent", *shipped_ref, "--shortstat", "--format=", *af)
    shipped_added, shipped_deleted = _parse_shortstat(shipped_stat)

    shipped_dates = git(repo, "log", *since_flag, "--first-parent", *shipped_ref, "--format=%ad", "--date=short", *af)
    shipped_daily = _parse_daily(shipped_dates)

    # --- IN-FLIGHT metrics (on feature branches, not on default) ---
    inflight_commits_raw = git(repo, "log", *since_flag, "--no-merges", *inflight_ref, "--oneline", *af)
    inflight_commits = len(inflight_commits_raw.splitlines()) if inflight_commits_raw else 0

    inflight_stat = git(repo, "log", *since_flag, *inflight_ref, "--shortstat", "--format=", *af)
    inflight_added, inflight_deleted = _parse_shortstat(inflight_stat)

    inflight_dates = git(repo, "log", *since_flag, "--no-merges", *inflight_ref, "--format=%ad", "--date=short", *af)
    inflight_daily = _parse_daily(inflight_dates)

    # --- TOTALS (combine both) ---
    commits = shipped_commits + inflight_commits
    added = shipped_added + inflight_added
    deleted = shipped_deleted + inflight_deleted

    # Merge daily counts
    daily: dict[str, int] = defaultdict(int)
    for d, c in shipped_daily.items():
        daily[d] += c
    for d, c in inflight_daily.items():
        daily[d] += c

    # MRs (merges on default branch only — that's what "merged" means)
    merges_raw = git(repo, "log", *since_flag, "--merges", "--first-parent", *shipped_ref, "--oneline", *af)
    merges = len(merges_raw.splitlines()) if merges_raw else 0

    # Contributors (all branches combined)
    contrib_raw = git(repo, "log", *since_flag, "--no-merges", "--format=%aN", "--remotes", *af)
    contrib_counts: dict[str, int] = defaultdict(int)
    for name in contrib_raw.splitlines():
        if name and not BOT_PATTERNS.match(name):
            contrib_counts[name] += 1
    contributors: list[tuple[int, str]] = sorted(
        [(v, k) for k, v in contrib_counts.items()], reverse=True
    )

    # Top changed files (all branches)
    numstat = git(repo, "log", *since_flag, "--numstat", "--format=", "--remotes", *af)
    file_churn: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            f = parts[2]
            a, d = file_churn[f]
            file_churn[f] = (a + int(parts[0]), d + int(parts[1]))
    top_files = sorted(file_churn.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)[:10]

    # Category breakdown (all branches)
    subjects = git(repo, "log", *since_flag, "--no-merges", "--format=%s", "--remotes", *af).splitlines()
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
                categories[m.group(1).lower()] += 1

    # Releases: tags in window (branch-agnostic)
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
    releases = releases[:10]

    # Recent commits with SHAs (all branches - in-flight)
    commits_sha_raw = git(repo, "log", *since_flag, "--no-merges", "--format=%H %ad %s", "--date=short", "--remotes", *af)
    inflight_with_sha = [{"sha": l[:40], "date": l[41:51], "subject": l[52:]} for l in commits_sha_raw.splitlines() if len(l) > 52][:200]
    # Shipped commits with SHAs (first-parent on default branch)
    shipped_sha_log = git(repo, "log", *since_flag, "--first-parent", "--format=%H %ad %s", "--date=short", *shipped_ref, *af)
    shipped_with_sha = [{"sha": l[:40], "date": l[41:51], "subject": l[52:]} for l in shipped_sha_log.splitlines() if len(l) > 52][:200]
    commits_with_sha = shipped_with_sha + inflight_with_sha
    commits_in_window = [{"date": c["date"], "subject": c["subject"]} for c in commits_with_sha]

    # Recent context (last 10 commits regardless of window)
    recent_raw = git(repo, "log", "--no-merges", "--format=%ad %s", "--date=short", "-10", *af)
    recent = [{"date": l[:10], "subject": l[11:]} for l in recent_raw.splitlines() if len(l) > 11]

    return {
        "commits": commits,
        "shipped_commits": shipped_commits,
        "inflight_commits": inflight_commits,
        "merges": merges,
        "added": added,
        "deleted": deleted,
        "net": added - deleted,
        "shipped_added": shipped_added,
        "shipped_deleted": shipped_deleted,
        "shipped_net": shipped_added - shipped_deleted,
        "inflight_added": inflight_added,
        "inflight_deleted": inflight_deleted,
        "inflight_net": inflight_added - inflight_deleted,
        "daily": dict(daily),
        "shipped_daily": shipped_daily,
        "inflight_daily": inflight_daily,
        "contributors": contributors,
        "top_files": top_files,
        "categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
        "is_jira": is_jira,
        "releases": releases,
        "recent": recent,
        "low_activity": commits < 5,
        "commits_in_window": commits_in_window,
        "commit_subjects": subjects,
        "web_url": web_url,
        "default_branch": default_branch,
        "commits_with_sha": commits_with_sha,
        "shipped_shas": shipped_shas,
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
        "web_url": repo_metrics[0].get("web_url", "") if repo_metrics else "",
        "default_branch": repo_metrics[0].get("default_branch", "main") if repo_metrics else "main",
        "commits_with_sha": [],
        "shipped_shas": set(),
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
        agg["commits_with_sha"].extend(r.get("commits_with_sha", []))
        agg["shipped_shas"].update(r.get("shipped_shas", set()))
        if not agg["web_url"] and r.get("web_url"):
            agg["web_url"] = r["web_url"]
            agg["default_branch"] = r.get("default_branch", "main")

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
.bar-chart{display:flex;align-items:flex-end;gap:3px;height:140px}
.bar-day{display:flex;flex-direction:column;align-items:stretch;gap:3px;flex:1;min-width:12px}
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
.section ul li{color:#e6edf3;font-size:13px;padding:8px 0;border-bottom:1px solid rgba(48,54,61,0.4)}
.section ul li:last-child{border-bottom:none}
.staleness-warn{background:rgba(210,153,34,0.1);border:1px solid rgba(210,153,34,0.4);border-radius:8px;padding:10px 14px;margin-bottom:16px;color:#d29922;font-size:12px}
.arch-card{cursor:pointer;transition:transform 0.15s,box-shadow 0.15s}
.arch-card:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,0,0,0.4)}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:1000;align-items:center;justify-content:center;padding:24px}
.modal-overlay.open{display:flex}
.modal-box{background:#161b22;border:1px solid rgba(48,54,61,0.8);border-radius:16px;padding:32px;max-width:800px;width:100%;max-height:90vh;overflow-y:auto;position:relative}
.modal-close{position:absolute;top:16px;right:20px;background:none;border:none;color:#8b949e;font-size:20px;cursor:pointer}
.modal-close:hover{color:#e6edf3}
.modal-title{color:#58a6ff;font-size:18px;font-weight:600;margin-bottom:12px}
.modal-desc{color:#c9d1d9;font-size:14px;line-height:1.7;margin-bottom:16px}
.modal-files{color:#8b949e;font-size:12px;margin-bottom:20px;font-family:monospace}
.modal-commits table{width:100%;border-collapse:collapse;font-size:12px}
.modal-commits th{color:#8b949e;text-align:left;padding:6px 8px;border-bottom:1px solid rgba(48,54,61,0.6)}
.modal-commits td{padding:6px 8px;border-bottom:1px solid rgba(48,54,61,0.3);color:#e6edf3}
.mc-table{width:100%;border-collapse:collapse;font-size:12px}
.mc-date{color:#8b949e;white-space:nowrap;padding:5px 8px}
.mc-subj{padding:5px 8px;color:#e6edf3}
.mc-subj a{color:#58a6ff;text-decoration:none}
"""

CAT_COLORS = {
    "fix": "#58a6ff", "feat": "#3fb950", "refactor": "#a371f7",
    "test": "#d29922", "chore": "#8b949e", "docs": "#8b949e",
    "release": "#d29922", "ci": "#39d5ff", "perf": "#3fb950",
    "build": "#39d5ff", "style": "#8b949e", "revert": "#f85149",
}
CONTRIB_COLORS = ["#58a6ff", "#3fb950", "#a371f7", "#d29922", "#39d5ff",
                  "#f85149", "#8b949e", "#e6edf3"]


def _bar_chart(daily: dict[str, int], since: str, shipped_daily: dict[str, int] | None = None, inflight_daily: dict[str, int] | None = None) -> str:
    since_dt = _parse_since(since)
    days = [(since_dt + timedelta(days=i)).isoformat() for i in range(7)]
    max_c = max((daily.get(d, 0) for d in days), default=1) or 1
    has_split = shipped_daily is not None and inflight_daily is not None and any(inflight_daily.get(d, 0) > 0 for d in days)

    legend = ""
    if has_split:
        legend = '<div style="display:flex;gap:12px;margin-bottom:8px;font-size:10px;color:#8b949e"><span>■ <span style="color:#58a6ff">Shipped</span></span><span>■ <span style="color:#d29922">In Flight</span></span></div>'

    bars = []
    for d in days:
        c = daily.get(d, 0)
        shipped_c = shipped_daily.get(d, 0) if shipped_daily else c
        inflight_c = inflight_daily.get(d, 0) if inflight_daily else 0
        total_h = max(2, int(c / max_c * 120))
        label = d[8:]
        count_label = str(c) if c > 0 else ""

        if has_split and inflight_c > 0:
            shipped_h = max(1, int(shipped_c / max_c * 120)) if shipped_c > 0 else 0
            inflight_h = max(1, int(inflight_c / max_c * 120)) if inflight_c > 0 else 0
            bars.append(
                f'<div class="bar-day">'
                f'<div style="color:#8b949e;font-size:9px;text-align:center;height:12px;line-height:12px">{count_label}</div>'
                f'<div style="display:flex;flex-direction:column-reverse;height:{total_h}px;cursor:pointer" title="{shipped_c} shipped + {inflight_c} in flight on {d}" data-date="{d}" data-count="{c}" onclick="openDay(this)">'
                f'<div style="height:{shipped_h}px;background:#58a6ff;border-radius:3px 3px 0 0;width:100%"></div>'
                f'<div style="height:{inflight_h}px;background:#d29922;border-radius:3px 3px 0 0;width:100%"></div>'
                f'</div>'
                f'<span class="bar-label">{label}</span>'
                f'</div>'
            )
        else:
            is_peak = c == max_c and c > 0
            cls = "bar-fill peak" if is_peak else "bar-fill"
            bars.append(
                f'<div class="bar-day">'
                f'<div style="color:#8b949e;font-size:9px;text-align:center;height:12px;line-height:12px">{count_label}</div>'
                f'<div class="{cls}" style="height:{total_h}px;cursor:{"pointer" if c>0 else "default"}" title="{c} commits on {d}" data-date="{d}" data-count="{c}" {"onclick=openDay(this)" if c>0 else ""}></div>'
                f'<span class="bar-label">{label}</span>'
                f'</div>'
            )
    return f'{legend}<div class="bar-chart">{"".join(bars)}</div>'


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


def _churn_bars(top_files: list, web_url: str = "", branch: str = "main") -> str:
    if not top_files:
        return "<p style='color:#8b949e;font-size:12px'>No data</p>"
    max_total = max(a + d for _, (a, d) in top_files) or 1
    html = []
    for fname, (a, d) in top_files:
        short = fname.split("/")[-1]
        total = a + d
        add_pct = a / max_total * 100
        del_pct = d / max_total * 100
        file_url = (f"{web_url}/-/blob/{branch}/{fname}" if "gitlab" in web_url else (f"{web_url}/blob/{branch}/{fname}" if web_url else "")) if a > 0 else ""
        file_link = f'<a href="{file_url}" target="_blank" style="color:#c9d1d9;text-decoration:none;border-bottom:1px dotted rgba(139,148,158,0.4)">{short}</a>' if file_url else f'<span style="color:#8b949e">{short}</span>'
        html.append(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
            f'<span style="font-size:11px;word-break:break-all" title="{fname}">{file_link}</span>'
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
    max_c = contributors[0][0] if contributors else 1
    rows = []
    for i, (count, name) in enumerate(contributors):
        pct = count / max_c * 100
        color = CONTRIB_COLORS[i % len(CONTRIB_COLORS)]
        # Link to Home people search (avoids guessing usernames)
        first, last = (name.split()[0], name.split()[-1]) if len(name.split()) >= 2 else (name, "")
        home_url = f"https://home.appian.com/suite/sites/home/page/home/searchresults#q={first}+{last}" if last else ""
        name_html = f'<a href="{home_url}" target="_blank" style="color:#e6edf3;text-decoration:none;border-bottom:1px dotted rgba(139,148,158,0.3)">{name}</a>'
        rows.append(
            f'<div style="margin-bottom:7px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
            f'{name_html}'
            f'<span style="color:#8b949e;font-size:11px">{count} ({count/total*100:.0f}%)</span>'
            f'</div>'
            f'<div style="height:8px;width:{pct:.1f}%;background:{color};border-radius:3px;min-width:4px"></div>'
            f'</div>'
        )
    return "".join(rows)



def _generate_narrative(entry_name: str, metrics: dict) -> dict:
    """Generate AI narrative for one entry using a constrained prompt.
    Falls back to template narrative if AI is unavailable."""
    import subprocess as _sp, json as _json

    subjects = metrics.get("commit_subjects", [])[:20]
    top_files = metrics.get("top_files", [])[:8]
    contributors = metrics.get("contributors", [])[:5]
    categories = metrics.get("categories", {})
    is_jira = metrics.get("is_jira", False)
    commits = metrics.get("commits", 0)
    net = metrics.get("net", 0)
    releases = metrics.get("releases", 0)

    # Build structured file evidence string
    file_evidence = ", ".join(
        f"{f[0].split('/')[-1]} (+{f[1].get('added',0)}/-{f[1].get('deleted',0)})"
        for f in top_files[:6]
    ) if top_files else "no files"

    contrib_str = ", ".join(f"{c['name']} ({c['count']})" for c in contributors[:3])
    subj_sample = "\n".join(f"- {s[:80]}" for s in subjects[:12])
    cat_str = str(dict(list(categories.items())[:5]))

    prompt = f"""Generate a concise engineering report narrative for: {entry_name}

DATA (do not invent anything not listed here):
- Commits: {commits}, Net lines: {net:+,}, Releases: {releases}
- Contributors: {contrib_str}
- Top changed files: {file_evidence}
- Commit categories: {cat_str}
- Sample commit subjects:
{subj_sample}

OUTPUT exactly this JSON (no other text):
{{
  "summary": "3-4 sentences. Arc of the week based ONLY on the files and subjects above. Team framing only.",
  "themes": "<ul style='list-style:none;padding:0;margin:0'><li style='padding:8px 0;border-bottom:1px solid rgba(48,54,61,0.4)'><span style='color:#e6edf3;font-size:13px'>EMOJI <strong>SPECIFIC TITLE from files/subjects</strong> — 1 sentence citing a specific file or metric.</span></li>... (4 items total)</ul>",
  "architecture": "<div style='background:rgba(30,35,44,0.9);border:1px solid rgba(48,54,61,0.7);border-radius:10px;padding:16px'><div style='color:#58a6ff;font-size:13px;font-weight:600;margin-bottom:8px'>MODULE NAME from top files</div><div style='color:#c9d1d9;font-size:12px;line-height:1.6;margin-bottom:10px'>What changed in 1-2 sentences.</div><div style='color:#8b949e;font-size:11px'>filename +N -N</div></div>... (4 cards, each MUST reference actual filenames)"
}}"""

    # Try kiro CLI first, then claude, then fall back to template
    for cmd in [["kiro", "ask", "--no-context"], ["claude", "--print"]]:
        try:
            result = _sp.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=60, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                # Extract JSON from output
                text = result.stdout.strip()
                m = __import__('re').search(r'\{[\s\S]*\}', text)
                if m:
                    parsed = _json.loads(m.group(0))
                    if all(k in parsed for k in ("summary", "themes", "architecture")):
                        return parsed
        except (FileNotFoundError, _sp.TimeoutExpired, _json.JSONDecodeError):
            continue

    # Fallback: template-based narrative (always works, lower quality)
    return _template_narrative(entry_name, metrics)


def _template_narrative(entry_name: str, metrics: dict) -> dict:
    """Template-based narrative fallback — no AI required."""
    commits = metrics.get("commits", 0)
    net = metrics.get("net", 0)
    releases = metrics.get("releases", 0)
    top_files = metrics.get("top_files", [])[:4]
    contributors = metrics.get("contributors", [])[:3]
    categories = metrics.get("categories", {})
    subjects = metrics.get("commit_subjects", [])[:5]

    # Summary
    top_cat = list(categories.keys())[0] if categories else "various"
    top_contrib = contributors[0]["name"].split()[0] if contributors else "the team"
    summary = (
        f"{entry_name} delivered {commits} commits and {net:+,} net lines this week"
        + (f", shipping {releases} releases" if releases else "")
        + f". Work was led by {top_contrib} with focus on {top_cat} changes."
        + (" The codebase is growing with primarily additive changes." if net > 0 else " Refactoring reduced net line count while improving structure.")
    )

    # Themes from categories
    theme_items = []
    cat_emojis = {"fix": "🐛", "feat": "✨", "refactor": "♻️", "test": "🧪", "chore": "🔧", "docs": "📝", "ci": "⚙️"}
    for cat, count in list(categories.items())[:4]:
        emoji = cat_emojis.get(cat, "📦")
        pct = int(count / max(commits, 1) * 100)
        theme_items.append(f"<li style='padding:8px 0;border-bottom:1px solid rgba(48,54,61,0.4)'><span style='color:#e6edf3;font-size:13px'>{emoji} <strong>{cat.capitalize()} work</strong> — {count} commits ({pct}% of week's output).</span></li>")
    if releases:
        theme_items.append(f"<li style='padding:8px 0;border-bottom:1px solid rgba(48,54,61,0.4)'><span style='color:#e6edf3;font-size:13px'>🚀 <strong>{releases} releases</strong> shipped this week.</span></li>")
    themes = f"<ul style='list-style:none;padding:0;margin:0'>{''.join(theme_items[:4])}</ul>"

    # Architecture cards from top files
    def _card(title, desc, files_str):
        return (f'<div style="background:rgba(30,35,44,0.9);border:1px solid rgba(48,54,61,0.7);border-radius:10px;padding:16px">'
                f'<div style="color:#58a6ff;font-size:13px;font-weight:600;margin-bottom:8px">{title}</div>'
                f'<div style="color:#c9d1d9;font-size:12px;line-height:1.6;margin-bottom:10px">{desc}</div>'
                f'<div style="color:#8b949e;font-size:11px">{files_str}</div></div>')

    arch_cards = []
    for item in top_files[:4]:
        fname = item[0].split("/")[-1] if isinstance(item, list) else item.get("file","?").split("/")[-1]
        stats = item[1] if isinstance(item, list) else item
        added = stats.get("added", 0) if isinstance(stats, dict) else 0
        deleted = stats.get("deleted", 0) if isinstance(stats, dict) else 0
        arch_cards.append(_card(fname, f"File received {added+deleted} line changes this week.", f"+{added} -{deleted}"))
    while len(arch_cards) < 4:
        arch_cards.append(_card("Other Changes", "Additional work across the codebase.", "various files"))
    architecture = "".join(arch_cards)

    return {"summary": summary, "themes": themes, "architecture": architecture}



def _normalize_themes(themes_html: str) -> str:
    """Apply dark-theme styles to plain <ul><li> themes HTML."""
    if not themes_html or 'list-style:none' in themes_html:
        return themes_html
    result = themes_html.replace('<ul>', "<ul style='list-style:none;padding:0;margin:0'>")
    result = result.replace('<li>', "<li style='padding:8px 0;border-bottom:1px solid rgba(48,54,61,0.4)'>")
    return result

_HEAD_MODAL_SCRIPT = (
    "<script>"
    "function closeModal(){"
    "var m=document.getElementById('arch-modal');"
    "if(m){m.classList.remove('open');document.body.style.overflow='';}"
    "}"
    "function openCard(c){"
    "var ds=c.querySelectorAll('div');"
    "var t=document.getElementById('modal-title');"
    "var d=document.getElementById('modal-desc');"
    "var f=document.getElementById('modal-files');"
    "var mc=document.getElementById('modal-commits');"
    "if(t)t.textContent=ds[0]?ds[0].textContent:'';"
    "if(d)d.textContent=ds[1]?ds[1].textContent:'';"
    "if(f)f.textContent=ds[2]?ds[2].textContent:'';"
    "var commits=window._archCommits||[];"
    "if(mc)mc.innerHTML=commits.length"
    "?'<table class=\'mc-table\'><tr><th>Date</th><th>Commit</th></tr>'"
    "+commits.map(function(c){return '<tr><td class=\'mc-date\'>'+(c.date||'')+'</td>"
    "<td class=\'mc-subj\'>'+(c.url?'<a href=\''+c.url+'\' target=\'_blank\'>'+c.subject+'</a>':c.subject)+'</td></tr>';}).join('')+'</table>'"
    ":'No commit details.';"
    "var m=document.getElementById('arch-modal');"
    "if(m){m.classList.add('open');document.body.style.overflow='hidden';}"
    "}"
    "function openDay(bar){"
    "var date=bar.getAttribute('data-date'),count=bar.getAttribute('data-count');"
    "if(!count||count==='0')return;"
    "var commits=(window._dailyCommits||{})[date]||[];"
    "var t=document.getElementById('modal-title');"
    "if(t)t.textContent=date+' \u2014 '+count+' commit'+(count==='1'?'':'s');"
    "var d=document.getElementById('modal-desc'),f=document.getElementById('modal-files');"
    "if(d)d.textContent='';if(f)f.textContent='';"
    "var mc=document.getElementById('modal-commits');"
    "if(mc)mc.innerHTML=commits.length"
    "?'<table class=\'mc-table\'><tr><th>Commit</th></tr>'"
    "+commits.map(function(c){return '<tr><td class=\'mc-subj\'>'+(c.url?'<a href=\''+c.url+'\' target=\'_blank\'>'+c.subject+'</a>':c.subject)+'</td></tr>';}).join('')+'</table>'"
    ":'Commits from branch activity.';"
    "var m=document.getElementById('arch-modal');"
    "if(m){m.classList.add('open');document.body.style.overflow='hidden';}"
    "}"
    "</script>"
)


def _write_modal_js(output_dir: Path) -> None:
    """Write eng-report-modal.js — clean JS, no quoting issues."""
    js_path = output_dir / "eng-report-modal.js"
    if js_path.exists():
        return
    js_path.write_text('function closeModal(){\n  var m=document.getElementById("arch-modal");\n  if(m){m.classList.remove("open");document.body.style.overflow="";}\n}\nfunction openCard(c){\n  var ds=c.querySelectorAll("div");\n  var ids=["modal-title","modal-desc","modal-files"];\n  for(var i=0;i<3;i++){var el=document.getElementById(ids[i]);if(el)el.textContent=ds[i]?ds[i].textContent:"";}\n  var mc=document.getElementById("modal-commits"),commits=window._archCommits||[];\n  if(mc){\n    if(commits.length){\n      var rows=commits.map(function(r){\n        var link=r.url?"<a href="+r.url+" target=_blank>"+r.subject+"</a>":r.subject;\n        return "<tr><td class=mc-date>"+(r.date||"")+"</td><td class=mc-subj>"+link+"</td></tr>";\n      }).join("");\n      mc.innerHTML="<table class=mc-table><tr><th>Date</th><th>Commit</th></tr>"+rows+"</table>";\n    } else { mc.textContent="No commit details."; }\n  }\n  var m=document.getElementById("arch-modal");\n  if(m){m.classList.add("open");document.body.style.overflow="hidden";}\n}\nfunction openDay(bar){\n  var date=bar.getAttribute("data-date"),count=bar.getAttribute("data-count");\n  if(!count||count==="0")return;\n  var commits=(window._dailyCommits||{})[date]||[];\n  var t=document.getElementById("modal-title");\n  if(t)t.textContent=date+" \\u2014 "+count+" commit"+(count==="1"?"":"s");\n  var d=document.getElementById("modal-desc"),f=document.getElementById("modal-files");\n  if(d)d.textContent="";if(f)f.textContent="";\n  var mc=document.getElementById("modal-commits");\n  if(mc){\n    if(commits.length){\n      var rows=commits.map(function(r){\n        var badge=r.s?"<span style=\'color:#3fb950;font-size:10px;margin-right:6px\'>shipped</span>":"<span style=\'color:#d29922;font-size:10px;margin-right:6px\'>in\\u2011flight</span>";\n        var link=r.url?"<a href="+r.url+" target=_blank>"+r.subject+"</a>":r.subject;\n        return "<tr><td class=mc-subj>"+badge+link+"</td></tr>";\n      }).join("");\n      mc.innerHTML="<table class=mc-table><tr><th>Commit</th></tr>"+rows+"</table>";\n    } else { mc.textContent="Commits from branch activity."; }\n  }\n  var m=document.getElementById("arch-modal");\n  if(m){m.classList.add("open");document.body.style.overflow="hidden";}\n}\n', encoding="utf-8")



def _make_arch_modal() -> str:
    return (
        '<div class="modal-overlay" id="arch-modal" onclick="if(event.target===this)closeModal()">'
        '<div class="modal-box">'
        '<button class="modal-close" onclick="closeModal()">&#x2715;</button>'
        '<div class="modal-title" id="modal-title"></div>'
        '<div class="modal-desc" id="modal-desc"></div>'
        '<div class="modal-files" id="modal-files"></div>'
        '<div class="modal-commits" id="modal-commits"></div>'
        '</div></div>'
        '<script>'
        'function closeModal(){'
        'document.getElementById("arch-modal").classList.remove("open");'
        'document.body.style.overflow="";}'
        'function openDay(bar){'
        'var date=bar.getAttribute("data-date");'
        'var count=bar.getAttribute("data-count");'
        'if(!count||count==="0")return;'
        'var commits=(window._dailyCommits||{})[date]||[];'
        'document.getElementById("modal-title").textContent=date+" \u2014 "+count+" commit"+(count==="1"?"":"s");'
        'document.getElementById("modal-desc").textContent="";'
        'document.getElementById("modal-files").textContent="";'
        'var mc=document.getElementById("modal-commits");'
        'mc.innerHTML=commits.length'
        '?("<p style=\"color:#8b949e;font-size:10px;margin-bottom:6px\">"+(commits.length<parseInt(count)?"Showing "+commits.length+" of "+count+" commits":"All "+count+" commits")+"</p>")+"<table><tr><th>Commit</th></tr>"+commits.map(function(c){var badge=c.s?"<span style=\'color:#3fb950;font-size:10px;margin-right:6px\'>shipped</span>":"<span style=\'color:#d29922;font-size:10px;margin-right:6px\'>in\‑flight</span>";return "<tr><td style=\'padding:5px 8px\'>"+badge+(c.url?"<a href=\'"+c.url+"\' target=\'_blank\' style=\'color:#58a6ff;text-decoration:none\'>"+c.subject+"</a>":c.subject)+"</td></tr>";}).join("")+"</table>"'
        ':"<p style=\'color:#8b949e;font-size:12px\'>Commits from branch activity.</p>";'
        'document.getElementById("arch-modal").classList.add("open");'
        'document.body.style.overflow="hidden";}'
        'function openCard(card){'
        'var ds=card.querySelectorAll("div");'
        'document.getElementById("modal-title").textContent=ds[0]?ds[0].textContent:"";'
        'document.getElementById("modal-desc").textContent=ds[1]?ds[1].textContent:"";'
        'document.getElementById("modal-files").textContent=ds[2]?ds[2].textContent:"";'
        'var commits=window._archCommits||[];'
        'var mc=document.getElementById("modal-commits");'
        'mc.innerHTML=commits.length'
        '?"<p style=\'color:#8b949e;font-size:12px;margin-bottom:8px\'>Commits this period</p><table><tr><th>Date</th><th>Commit</th></tr>"+commits.map(function(c){return "<tr><td style=\'color:#8b949e;white-space:nowrap;padding:5px 8px\'>"+c.date+"</td><td style=\'padding:5px 8px\'>"+(c.url?"<a href=\'"+c.url+"\' target=\'_blank\' style=\'color:#58a6ff;text-decoration:none\'>"+c.subject+"</a>":c.subject)+"</td></tr>";}).join("")+"</table>"'
        ':"<p style=\'color:#8b949e;font-size:12px\'>No commit details available.</p>";'
        'document.getElementById("arch-modal").classList.add("open");'
        'document.body.style.overflow="hidden";}'
        '</script>'
    )


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
    top_pct = min(100, int(m["contributors"][0][0] / max(m["commits"], 1) * 100)) if m["contributors"] else 0

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
    shipped = m.get("shipped_commits", m["commits"])
    inflight = m.get("inflight_commits", 0)
    shipped_net = m.get("shipped_net", m["net"])
    inflight_net = m.get("inflight_net", 0)
    web_url = m.get("web_url", "")
    is_gl = "gitlab" in web_url
    tags_url = f"{web_url}/-/tags" if is_gl else (f"{web_url}/tags" if web_url else "")
    mrs_url = f"{web_url}/-/merge_requests?state=merged" if is_gl else (f"{web_url}/pulls?q=is:merged" if web_url else "")
    commits_url = f"{web_url}/-/commits/{m.get('default_branch','main')}" if is_gl else (f"{web_url}/commits/{m.get('default_branch','main')}" if web_url else "")

    def _linked_card(label, value, url, cls="", subtitle=""):
        val_html = f'<a href="{url}" target="_blank" style="color:inherit;text-decoration:none">{value}</a>' if url else str(value)
        sub_html = f'<div style="font-size:10px;color:#8b949e;margin-top:4px">{subtitle}</div>' if subtitle else ""
        return f'<div class="card"><div class="card-label">{label}</div><div class="card-value {cls}">{val_html}</div>{sub_html}</div>'

    # Build shipped/inflight subtitle for commits and net lines
    commits_sub = f'<span style="color:#3fb950">{shipped} shipped</span><br><span style="color:#d29922">{inflight} in flight</span>' if inflight > 0 else ""
    net_sub = ""
    if inflight_net != 0 or shipped_net != m["net"]:
        sn = f"+{shipped_net:,}" if shipped_net >= 0 else f"{shipped_net:,}"
        fn = f"+{inflight_net:,}" if inflight_net >= 0 else f"{inflight_net:,}"
        net_sub = f'<span style="color:#3fb950">{sn} shipped</span><br><span style="color:#d29922">{fn} in flight</span>'

    body_parts.append(f"""
<div class="cards">
  {_linked_card("Commits", m['commits'], commits_url, subtitle=commits_sub)}
  {_linked_card("MRs Merged", m['merges'], mrs_url)}
  {_linked_card("Net Lines", net_str, "", net_cls, subtitle=net_sub)}
  {_linked_card("Releases", len(m['releases']), tags_url, "blue")}
  <div class="card"><div class="card-label">Contributors</div><div class="card-value">{contrib_count}</div></div>
  <div class="card"><div class="card-label">Top Contributor</div><div class="card-value" style="font-size:13px">{top_contributor.split()[0]} ({top_pct}%)</div></div>
</div>""")

    if m["low_activity"]:
        # Activity Snapshot mode
        body_parts.append('<div class="section"><h3>📋 Activity Snapshot</h3>')
        web_url = m.get("web_url", "")
        if m["commits"] == 0:
            body_parts.append('<p style="color:#8b949e;font-size:13px">No commits in this period.</p>')
        else:
            recent_window = [r for r in m.get("commits_with_sha", []) if r["date"] >= _parse_since(since).isoformat()] or [r for r in m["recent"] if r["date"] >= _parse_since(since).isoformat()]
            def _commit_link(r):
                sha = r.get("sha","")
                subj = r.get("subject", r.get("subject",""))[:100]
                if sha and web_url:
                    url = f"{web_url}/-/commit/{sha}" if "gitlab" in web_url else f"{web_url}/commit/{sha}"
                    return f'<a href="{url}" target="_blank" style="color:#e6edf3;text-decoration:none;border-bottom:1px dotted rgba(139,148,158,0.4)">{subj}</a>'
                return f'<span class="subject">{subj}</span>'
            items = "\n".join(
                f'<div class="snapshot-item"><span style="color:#8b949e">{r["date"]}</span> {_commit_link(r)}</div>'
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
                f'{_normalize_themes(narrative["themes"])}'
                f'</div>'
            )

        # Architecture evolution — before charts
        if narrative and narrative.get("architecture"):
            web_url = m.get("web_url","")
            is_gl = "gitlab" in web_url
            # Build commits data for modal as JSON stored in a script tag
            related = []
            for c in m.get("commits_with_sha",[])[:20]:
                sha = c.get("sha","")
                url = (f"{web_url}/-/commit/{sha}" if is_gl else f"{web_url}/commit/{sha}") if sha and web_url else ""
                related.append({"sha":sha,"date":c.get("date",""),"subject":c.get("subject",""),"url":url})
            # Add arch-card class to each card by simple string replace
            arch_html = narrative["architecture"].replace(
                'style="background:rgba(30,35,44,0.9)',
                'class="arch-card" onclick="openCard(this)" style="background:rgba(30,35,44,0.9)'
            )
            # Store commits in page-level JS var, cards call openArch with their index
            commits_script = f'<script>window._archCommits={json.dumps(related)};</script>'
            # Also emit daily commits map for bar clicks
            daily_map = {}
            for c in m.get("commits_with_sha", []):
                d2 = c.get("date","")
                if d2:
                    if d2 not in daily_map: daily_map[d2] = []
                    sha = c.get("sha","")
                    url2 = (f"{web_url}/-/commit/{sha}" if is_gl else f"{web_url}/commit/{sha}") if sha and web_url else ""
                    daily_map[d2].append({"sha":sha,"subject":c.get("subject",""),"url":url2})
            commits_script += f'<script>window._archDailyCommits={json.dumps(daily_map)};</script>'
            body_parts.append(
                f'<div class="section" style="margin-bottom:16px">'
                f'<h3>🏛 Architecture Evolution</h3>'
                f'<p style="color:#8b949e;font-size:10px;margin-bottom:12px">Click any card for details</p>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px" id="arch-grid">'
                f'{arch_html}'
                f'</div></div>{commits_script}'
            )

        # Daily chart + categories
        # Emit daily commits map for bar chart click modal
        daily_commits_map = {}
        web_url = m.get("web_url", "")
        is_gl = "gitlab" in web_url
        shipped_shas = set()
        # Get shipped commit SHAs to tag them
        shipped_sha_raw = m.get("shipped_shas", set())
        for c in m.get("commits_with_sha", []):
            d2 = c.get("date", "")
            if d2:
                if d2 not in daily_commits_map: daily_commits_map[d2] = []
                sha = c.get("sha", "")
                url2 = (f"{web_url}/-/commit/{sha}" if is_gl else f"{web_url}/commit/{sha}") if sha and web_url else ""
                is_shipped = sha in shipped_sha_raw
                daily_commits_map[d2].append({"sha": sha, "subject": c.get("subject", ""), "url": url2, "s": is_shipped})
        body_parts.append(f'<script>window._dailyCommits={json.dumps(daily_commits_map)};</script>')

        body_parts.append('<div class="grid2">')
        body_parts.append(
            f'<div class="section"><h3>📈 Daily Velocity</h3>'
            f'{_bar_chart(m["daily"], since, m.get("shipped_daily"), m.get("inflight_daily"))}</div>'
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
            f'{_churn_bars(m["top_files"], m.get("web_url",""), m.get("default_branch","main"))}</div>'
        )
        body_parts.append(
            f'<div class="section"><h3>👥 Contributors</h3>'
            f'{_contrib_bar(m["contributors"])}</div>'
        )
        body_parts.append("</div>")

        # Releases
        if m["releases"]:
            web_url = m.get("web_url", "")
            def _tag_url(tag):
                if not web_url: return ""
                if "gitlab" in web_url: return f"{web_url}/-/tags/{tag}"
                return f"{web_url}/releases/tag/{tag}"
            items = "\n".join(
                f'<div class="release-item">'
                + (f'<a href="{_tag_url(r["tag"])}" target="_blank" class="release-tag" style="text-decoration:none">{r["tag"]}</a>' if _tag_url(r["tag"]) else f'<span class="release-tag">{r["tag"]}</span>')
                + f'<span class="release-date">{r["date"]}</span>'
                + f'</div>'
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



    # (placeholder replaced after f-string is evaluated)
    footer_parts = [f"{name}", f"Generated: {today}"]
    if scope_warning:
        footer_parts.append("⚠ Org data may be stale")

    _html_raw = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>{CSS}</style>
<script src="eng-report-modal.js"></script>
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
__ARCH_MODAL_PLACEHOLDER__
</body>
</html>"""
    _html = _html_raw.replace("__ARCH_MODAL_PLACEHOLDER__", _make_arch_modal())
    return _html


# ── Config loading ─────────────────────────────────────────────────────────────

def load_config(path: Path) -> dict:
    """Load config.yaml using PyYAML if available, else built-in parser."""
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

def run_entry(entry: dict, since: str, output_dir: Path, author_filter: str | None = None, narrative: dict | None = None, fetched_paths: set | None = None, use_ai: bool = False) -> dict[str, Any]:
    """Process one config entry and write its HTML file. Returns summary row."""
    name = entry.get("label", entry["name"])
    file_key = entry["name"]
    if fetched_paths is None:
        fetched_paths = set()
    branch_scope = entry.get("_branch_scope", "all")
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

    # Gather metrics per repo (fetch each unique path once)
    per_repo: list[dict] = []
    for rp in repo_paths:
        if not rp.exists():
            print(f"  ⚠ {rp} not found, skipping", file=sys.stderr)
            continue
        if str(rp) not in fetched_paths:
            git(rp, "fetch", "--all", "--quiet", check=False)
            fetched_paths.add(str(rp))
        m = gather_repo_metrics(rp, since, authors, branch_scope=branch_scope)
        m["_repo_name"] = rp.name
        per_repo.append(m)

    if not per_repo:
        print(f"  ✗ {name}: no valid repos", file=sys.stderr)
        return {"name": name, "commits": 0, "merges": 0, "added": 0, "deleted": 0,
                "net": 0, "releases": 0, "top_contributor": "—"}

    # Aggregate if multiple repos
    agg = aggregate_metrics(per_repo)

    # Generate narrative if requested and not provided
    if use_ai and not narrative and not agg.get("low_activity"):
        summary_for_ai = {
            "commits": agg["commits"], "net": agg["net"], "releases": len(agg.get("releases",[])),
            "commit_subjects": agg.get("commit_subjects",[])[:20],
            "top_files": [[f, {"added": a, "deleted": d}] for f,(a,d) in agg.get("top_files",[])[:8]],
            "contributors": [{"count": c, "name": n} for c,n in agg.get("contributors",[])[:5]],
            "categories": agg.get("categories",{}),
            "is_jira": agg.get("is_jira", False),
        }
        print(f"  → generating AI narrative for {name}...", file=sys.stderr)
        narrative = _generate_narrative(name, summary_for_ai)

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
    since_dt = _parse_since(since)
    today_dt = date.today()
    date_range = f"{since_dt.strftime('%b %d')} – {today_dt.strftime('%b %d, %Y')}"
    subtitle_parts.append(date_range)
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
    _write_modal_js(output_dir)

    top_contributor = agg["contributors"][0][1] if agg["contributors"] else "—"
    top_pct = int(agg["contributors"][0][0] / max(agg["commits"], 1) * 100) if agg["contributors"] else 0
    print(f"  ✓ {name}: {agg['commits']} commits, {agg['net']:+,} lines → {out_path.name}", file=sys.stderr)

    # Summary row (for index) — always returned
    summary = {
        "name": file_key,
        "label": name,
        "commits": agg["commits"],
        "shipped_commits": agg.get("shipped_commits", agg["commits"]),
        "inflight_commits": agg.get("inflight_commits", 0),
        "merges": agg["merges"],
        "added": agg["added"],
        "deleted": agg["deleted"],
        "net": agg["net"],
        "shipped_net": agg.get("shipped_net", agg["net"]),
        "inflight_net": agg.get("inflight_net", 0),
        "shipped_daily": agg.get("shipped_daily", {}),
        "inflight_daily": agg.get("inflight_daily", {}),
        "releases": len(agg["releases"]),
        "top_contributor": f"{top_contributor.split()[0]} ({top_pct}%)" if agg["contributors"] else "—",
        "group": scope.get("tribe", ""),
        # Rich data for narrative generation
        "commit_subjects": agg.get("commit_subjects", [])[:50],
        "top_files": [(f, {"added": a, "deleted": d}) for f, (a, d) in agg.get("top_files", [])],
        "contributors": [{"count": c, "name": n} for c, n in agg.get("contributors", [])],
        "categories": agg.get("categories", {}),
        "is_jira": agg.get("is_jira", False),
        "web_url": agg.get("web_url", ""),
        "daily": agg.get("daily", {}),
        "low_activity": agg.get("low_activity", False),
    }
    return summary


def build_index(rows: list[dict], output_dir: Path, config: dict, entries: list[dict]) -> None:
    """Build grouped _index.html — always generated, sections by category."""
    since = config.get("local", {}).get("window", "1 week ago")
    today = date.today().isoformat()
    since_dt = _parse_since(since)
    today_date = date.today()

    # Map name → label and category from entries
    # Map tribe name to friendly group label
    tribe_to_group = {
        "AGENTIC AI": "Agentic AI", "AI COPILOT": "AI Copilot",
        "ENTERPRISE AUTOMATION": "Enterprise Automation", "SMART SEARCH": "Smart Search",
        "AI PLATFORM": "AI Platform",
    }
    entry_meta = {
        e["name"]: {
            "label": e.get("label", e["name"]),
            "category": e.get("category", "Repos"),
            "group": tribe_to_group.get(e.get("scope", {}).get("tribe", ""), ""),
        }
        for e in entries
    }

    # Group rows by category
    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        cat = entry_meta.get(r["name"], {}).get("category", "Repos")
        label = entry_meta.get(r["name"], {}).get("label", r["name"])
        group = entry_meta.get(r["name"], {}).get("group", r.get("group", ""))
        groups[cat].append({**r, "_label": label, "_group": group})

    CATEGORY_ORDER = ["Repos", "SBU", "Groups", "Teams", "Individuals"]

    def table_section(cat: str, cat_rows: list) -> str:
        total_c = sum(r["commits"] for r in cat_rows)
        is_teams = cat == "Teams"
        if is_teams:
            cat_rows = sorted(cat_rows, key=lambda r: (r.get("_group",""), r["_label"]))
        rows_html = "\n".join(
            (f'<tr>'
            f'<td style="color:#8b949e;font-size:12px">{r.get("_group","")}</td>' if is_teams else "") +
            f'<td><a href="{r["name"]}.html" style="color:#58a6ff;font-weight:500">{r["_label"]}</a></td>'
            f'<td style="text-align:right">{r["commits"]}</td>'
            f'<td style="text-align:right;color:{"#3fb950" if r["net"]>=0 else "#f85149"}">{"+" if r["net"]>=0 else ""}{r["net"]:,}</td>'
            f'<td style="text-align:right">{r["releases"]}</td>'
            f'<td style="color:#8b949e;font-size:12px">{r["top_contributor"]}</td>'
            f'</tr>'
            for r in cat_rows
        )
        group_header = '<th>Group</th>' if is_teams else ""
        return (
            f'<div class="section" style="margin-bottom:20px">'
            f'<h3 style="color:#e6edf3;font-size:14px;margin-bottom:12px">{cat} <span style="color:#8b949e;font-size:11px;font-weight:normal">({len(cat_rows)} · {total_c} commits)</span></h3>'
            f'<table class="index-table">'
            f'<tr>{group_header}<th>Report</th><th style="text-align:right">Commits</th><th style="text-align:right">Net Lines</th><th style="text-align:right">Releases</th><th>Top Contributor</th></tr>'
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
<script src="eng-report-modal.js"></script>
</head>
<body>
<div class="container">
<div class="header">
  <h1>Engineering Reports — {today}</h1>
  <p style="color:#8b949e;font-size:13px">{len(rows)} reports · {since_dt.strftime('%b %d')} – {today_date.strftime('%b %d, %Y')} · {total_commits} commits · +{total_added:,} lines added</p>
</div>
{sections}
<div class="footer">Generated: {today}</div>
</div>
__ARCH_MODAL_PLACEHOLDER__
</body>
</html>"""

    html = html.replace("__ARCH_MODAL_PLACEHOLDER__", _make_arch_modal())
    _write_modal_js(output_dir)
    (output_dir / "_index.html").write_text(html, encoding="utf-8")
    print(f"  ✓ _index.html ({len(rows)} reports, {len(groups)} categories)")


def main() -> None:
    """CLI entry point."""
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
    p_run.add_argument("--json", action="store_true", dest="json_only", help="Output full metrics JSON to stdout (no HTML written — use with --narrative-file on next run)")
    p_run.add_argument("--no-index", action="store_true", help="Skip _index.html generation")
    p_run.add_argument("--author", default=None, help="Generate report for a single person across all configured repos")
    p_run.add_argument("--branch-scope", default=None, dest="branch_scope", choices=["all","shipped","in-flight"], help="Branch scope: all (default), shipped (main only), in-flight (branches only)")
    p_run.add_argument("--ai", action="store_true", help="Generate AI narrative inline (calls kiro/claude for each active entry)")
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
        # Merge all unique repo paths into one group entry
        all_paths = list(seen_paths)
        if all_paths:
            entries = [{"name": f"individual-{author.replace(' ','-')}", "label": author,
                        "repos": all_paths, "category": "Individuals"}]
        else:
            entries = []

    # Load optional AI narrative file
    narratives: dict[str, dict] = {}
    if getattr(args, "narrative_file", None) and args.narrative_file:
        try:
            with open(args.narrative_file) as f:
                narratives = json.load(f)
        except FileNotFoundError:
            print(f"error: narrative file not found: {args.narrative_file}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"error: narrative file is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    json_only = getattr(args, "json_only", False)
    def log(*a): print(*a, file=sys.stderr if json_only else sys.stdout)
    log(f"eng-report run — {len(entries)} entries, window: {since}")
    log(f"Output: {output_dir}\n")

    branch_scope = getattr(args, "branch_scope", None) or config.get("local", {}).get("branch_scope", "all")
    fetched_paths: set[str] = set()
    use_ai = getattr(args, "ai", False)

    rows = []
    for entry in entries:
        narrative = narratives.get(entry["name"])
        entry["_branch_scope"] = branch_scope
        row = run_entry(entry, since, output_dir, author_filter=author, narrative=narrative, fetched_paths=fetched_paths, use_ai=use_ai)
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
