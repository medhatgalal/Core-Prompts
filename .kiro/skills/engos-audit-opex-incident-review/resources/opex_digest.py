"""Validate OpEx snapshots and render a deterministic daily digest.

The script performs no network access. The skill gathers evidence and writes
normalized snapshots; this renderer owns calculations and presentation.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "OpExDigestSnapshot.v1"
TERMINAL_DPA_STATES = {"cancelled", "closed", "done", "resolved", "shipped"}
KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]*-\d+$")
STATUS_CLASSES = {
    "closed": "good",
    "done": "good",
    "resolved": "good",
    "shipped": "good",
    "remediated": "warn",
    "postmortem": "due",
    "code review": "info",
    "in progress": "info",
    "verification & validation": "info",
    "backlog": "muted",
    "not needed": "muted",
    "not set": "muted",
    "no sla": "muted",
}


class SnapshotError(ValueError):
    """Raised when a snapshot cannot support an honest report."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SnapshotError(f"{path} must contain a JSON object")
    return value


def _date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"{field} must begin with YYYY-MM-DD") from exc


def _timestamp(value: str, field: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except (TypeError, ValueError) as exc:
        raise SnapshotError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SnapshotError(f"{field} must include a timezone offset")
    return parsed


def _days(start: str, end: date, field: str) -> int:
    return max(0, (end - _date(start, field)).days)


def _require_string(mapping: dict[str, Any], field: str, where: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{where}.{field} must be a non-empty string")
    return value.strip()


def _unique_keys(items: list[dict[str, Any]], kind: str) -> None:
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SnapshotError(f"{kind}[{index}] must be an object")
        key = _require_string(item, "key", f"{kind}[{index}]")
        if not KEY_PATTERN.fullmatch(key):
            raise SnapshotError(f"{kind}[{index}].key has an invalid ticket key: {key}")
        if key in seen:
            raise SnapshotError(f"duplicate {kind} key: {key}")
        seen.add(key)


def validate_snapshot(snapshot: dict[str, Any], *, previous: bool = False) -> None:
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotError(f"schema_version must be {SCHEMA_VERSION}")
    as_of = _timestamp(
        _require_string(snapshot, "as_of", "snapshot"), "snapshot.as_of"
    ).date()
    scope = snapshot.get("scope")
    if not isinstance(scope, dict):
        raise SnapshotError("snapshot.scope must be an object")
    _require_string(scope, "label", "snapshot.scope")
    priorities = scope.get("priorities")
    if not isinstance(priorities, list) or not all(
        isinstance(item, str) and item for item in priorities
    ):
        raise SnapshotError(
            "snapshot.scope.priorities must be a non-empty string array"
        )
    base_url = scope.get("jira_base_url")
    if base_url is not None and not re.fullmatch(
        r"https?://[^\s<>\"']+", str(base_url)
    ):
        raise SnapshotError("snapshot.scope.jira_base_url must be an HTTP(S) URL")
    incidents = snapshot.get("incidents")
    dpas = snapshot.get("dpas")
    if not isinstance(incidents, list) or not isinstance(dpas, list):
        raise SnapshotError("snapshot.incidents and snapshot.dpas must be arrays")
    _unique_keys(incidents, "incidents")
    _unique_keys(dpas, "dpas")
    incident_keys = {item["key"] for item in incidents}
    dpa_keys = {item["key"] for item in dpas}
    dpa_by_key = {item["key"]: item for item in dpas}
    for index, incident in enumerate(incidents):
        where = f"incidents[{index}]"
        for field in (
            "summary",
            "group",
            "priority",
            "status",
            "owner",
            "created",
            "last_meaningful_progress",
        ):
            _require_string(incident, field, where)
        created = _date(incident["created"], f"{where}.created")
        last_progress = _date(
            incident["last_meaningful_progress"],
            f"{where}.last_meaningful_progress",
        )
        if created > as_of or last_progress > as_of or last_progress < created:
            raise SnapshotError(
                f"{where} requires created <= last_meaningful_progress <= snapshot.as_of"
            )
        for field in ("dpa_keys", "unlinked_dpa_keys"):
            values = incident.get(field, [])
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise SnapshotError(f"{where}.{field} must be a string array")
        affected = incident.get("affected_entities", [])
        if not isinstance(affected, list) or not all(
            isinstance(value, str) and value for value in affected
        ):
            raise SnapshotError(f"{where}.affected_entities must be a string array")
        missing = sorted(set(incident.get("dpa_keys", [])) - dpa_keys)
        if missing:
            raise SnapshotError(
                f"{where}.dpa_keys references missing DPAs: {', '.join(missing)}"
            )
        overlap = sorted(
            set(incident.get("dpa_keys", []))
            & set(incident.get("unlinked_dpa_keys", []))
        )
        if overlap:
            raise SnapshotError(
                f"{where} lists DPAs as both linked and unlinked: {', '.join(overlap)}"
            )
        wrong_parent = sorted(
            key
            for key in incident.get("dpa_keys", [])
            if dpa_by_key[key]["parent"] != incident["key"]
        )
        if wrong_parent:
            raise SnapshotError(
                f"{where}.dpa_keys have a different parent: {', '.join(wrong_parent)}"
            )
    for index, dpa in enumerate(dpas):
        where = f"dpas[{index}]"
        for field in ("summary", "parent", "priority", "status", "created"):
            _require_string(dpa, field, where)
        if _date(dpa["created"], f"{where}.created") > as_of:
            raise SnapshotError(f"{where}.created must not be after snapshot.as_of")
        if dpa["parent"] not in incident_keys and not dpa.get("historical_parent"):
            raise SnapshotError(
                f"{where}.parent is absent from incidents and historical_parent is not true"
            )
    coverage = snapshot.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("status") not in {
        "complete",
        "partial",
        "blocked",
    }:
        raise SnapshotError(
            "snapshot.coverage.status must be complete, partial, or blocked"
        )
    if not isinstance(coverage.get("sources"), list) or not coverage["sources"]:
        raise SnapshotError("snapshot.coverage.sources must name at least one source")
    if previous:
        return
    thresholds = snapshot.get("thresholds", {})
    stuck = thresholds.get("stuck_days", 7)
    chronic = thresholds.get("chronic_days", 14)
    if (
        not isinstance(stuck, int)
        or not isinstance(chronic, int)
        or stuck < 1
        or chronic <= stuck
    ):
        raise SnapshotError("thresholds require 1 <= stuck_days < chronic_days")
    changes = snapshot.get("changes", [])
    if not isinstance(changes, list):
        raise SnapshotError("snapshot.changes must be an array")
    for index, change in enumerate(changes):
        if not isinstance(change, dict):
            raise SnapshotError(f"changes[{index}] must be an object")
        for field in ("subject", "kind", "description", "current_status"):
            _require_string(change, field, f"changes[{index}]")
        if not isinstance(change.get("counts_as_progress"), bool):
            raise SnapshotError(f"changes[{index}].counts_as_progress must be boolean")
        if (
            not change["counts_as_progress"]
            and not str(change.get("exclusion_reason") or "").strip()
        ):
            raise SnapshotError(
                f"changes[{index}] needs exclusion_reason when it is not progress"
            )
    resolved = snapshot.get("resolved", [])
    if not isinstance(resolved, list):
        raise SnapshotError("snapshot.resolved must be an array")
    for index, item in enumerate(resolved):
        if not isinstance(item, dict):
            raise SnapshotError(f"resolved[{index}] must be an object")
        key = _require_string(item, "key", f"resolved[{index}]")
        if not KEY_PATTERN.fullmatch(key):
            raise SnapshotError(
                f"resolved[{index}].key has an invalid ticket key: {key}"
            )
        _require_string(item, "evidence", f"resolved[{index}]")
    additional_decisions = snapshot.get("additional_decisions", [])
    if not isinstance(additional_decisions, list):
        raise SnapshotError("snapshot.additional_decisions must be an array")
    for index, item in enumerate(additional_decisions):
        if not isinstance(item, dict):
            raise SnapshotError(f"additional_decisions[{index}] must be an object")
        key = _require_string(item, "key", f"additional_decisions[{index}]")
        if not KEY_PATTERN.fullmatch(key):
            raise SnapshotError(
                f"additional_decisions[{index}].key has an invalid ticket key: {key}"
            )
        _require_string(item, "text", f"additional_decisions[{index}]")
    for field in ("additional_patterns", "caveats"):
        values = snapshot.get(field, [])
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise SnapshotError(f"snapshot.{field} must be a string array")
    history = snapshot.get("history", [])
    if not isinstance(history, list) or not all(
        isinstance(item, dict) for item in history
    ):
        raise SnapshotError("snapshot.history must be an object array")
    for index, item in enumerate(history):
        for field in ("open", "dpas_overdue", "postmortems_overdue", "chronic"):
            if field in item and (
                not isinstance(item[field], int)
                or isinstance(item[field], bool)
                or item[field] < 0
            ):
                raise SnapshotError(
                    f"history[{index}].{field} must be a non-negative integer"
                )


def _open_dpa(dpa: dict[str, Any]) -> bool:
    return str(dpa["status"]).strip().casefold() not in TERMINAL_DPA_STATES


def _dpa_due(dpa: dict[str, Any], snapshot: dict[str, Any]) -> date | None:
    explicit = dpa.get("due")
    if explicit:
        return _date(str(explicit), f"DPA {dpa['key']} due")
    days = snapshot.get("dpa_sla_days", {}).get(dpa["priority"])
    if not isinstance(days, int) or days < 1:
        return None
    return _date(dpa["created"], f"DPA {dpa['key']} created") + timedelta(days=days)


def _postmortem_label(incident: dict[str, Any], as_of: date) -> tuple[str, str]:
    postmortem = incident.get("postmortem", {})
    if (
        not postmortem
        or not postmortem.get("required", True)
        or str(postmortem.get("state") or "").casefold() == "not_needed"
    ):
        return "not needed", "muted"
    if postmortem.get("complete") or postmortem.get("signoff_complete"):
        return "complete", "good"
    due_value = postmortem.get("due")
    if not due_value:
        return "due unknown", "muted"
    due = _date(str(due_value), f"incident {incident['key']} postmortem due")
    delta = (due - as_of).days
    if delta < 0:
        return f"{-delta}d overdue", "bad"
    return f"due {due.strftime('%m-%d')} ({delta}d)", "good" if delta >= 5 else "warn"


def _badge(text: str, css_class: str | None = None) -> str:
    selected = css_class or STATUS_CLASSES.get(text.casefold(), "muted")
    return f'<span class="badge {selected}">{html.escape(text)}</span>'


def _ticket(key: str, base_url: str) -> str:
    if not KEY_PATTERN.fullmatch(key):
        return html.escape(key)
    url = base_url.rstrip("/") + "/" + key
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(key)}</a>'


def build_model(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(current)
    validate_snapshot(previous, previous=True)
    as_of_timestamp = _timestamp(current["as_of"], "snapshot.as_of")
    prior_timestamp = _timestamp(previous["as_of"], "previous.as_of")
    as_of = as_of_timestamp.date()
    prior_date = prior_timestamp.date()
    if prior_timestamp >= as_of_timestamp:
        raise SnapshotError("previous.as_of must be earlier than snapshot.as_of")
    if prior_timestamp.utcoffset() != as_of_timestamp.utcoffset():
        raise SnapshotError(
            "current and previous snapshots must use the same timezone offset"
        )
    if (
        current["scope"]["label"] != previous["scope"]["label"]
        or current["scope"]["priorities"] != previous["scope"]["priorities"]
    ):
        raise SnapshotError(
            "current and previous snapshots must use the same scope and priorities"
        )
    incidents = [
        dict(item) for item in current["incidents"] if item.get("on_board", True)
    ]
    incident_by_key = {item["key"]: item for item in incidents}
    prior_keys = {
        item["key"] for item in previous["incidents"] if item.get("on_board", True)
    }
    current_keys = set(incident_by_key)
    for incident in incidents:
        incident["age_days"] = _days(
            incident["created"], as_of, f"incident {incident['key']} created"
        )
        incident["stalled_days"] = _days(
            incident["last_meaningful_progress"],
            as_of,
            f"incident {incident['key']} last_meaningful_progress",
        )
        incident["postmortem_label"], incident["postmortem_class"] = _postmortem_label(
            incident, as_of
        )
    newly_seen = sorted(current_keys - prior_keys)
    new_keys: list[str] = []
    discovered_corrections: list[dict[str, Any]] = []
    for key in newly_seen:
        classification = str(incident_by_key[key].get("new_classification") or "")
        if classification == "new":
            new_keys.append(key)
        elif classification == "correction":
            discovered_corrections.append(
                {
                    "subject": key,
                    "kind": "incident_discovered",
                    "description": f"{key} appeared because the prior snapshot under-captured the population",
                    "current_status": incident_by_key[key]["status"],
                    "counts_as_progress": False,
                    "exclusion_reason": "R2 correction",
                }
            )
        else:
            raise SnapshotError(
                f"newly seen incident {key} requires new_classification=new or correction"
            )
    changes = list(current.get("changes", []))
    progressed = [item for item in changes if item["counts_as_progress"]]
    corrections = [
        item for item in changes if not item["counts_as_progress"]
    ] + discovered_corrections
    missing_today = sorted(prior_keys - current_keys)
    resolved_evidence = {item["key"]: item for item in current.get("resolved", [])}
    unresolved_missing = sorted(set(missing_today) - set(resolved_evidence))
    unexpected_resolved = sorted(set(resolved_evidence) - set(missing_today))
    if unresolved_missing:
        raise SnapshotError(
            f"prior incidents missing today require resolved evidence: {', '.join(unresolved_missing)}"
        )
    if unexpected_resolved:
        raise SnapshotError(
            f"resolved evidence names incidents not removed from the board: {', '.join(unexpected_resolved)}"
        )
    if missing_today and current["coverage"]["status"] != "complete":
        raise SnapshotError(
            "partial or blocked coverage cannot prove incident drop-off"
        )
    resolved = []
    for item in previous["incidents"]:
        if item["key"] in resolved_evidence:
            resolved.append(
                {
                    **item,
                    "resolution_evidence": resolved_evidence[item["key"]]["evidence"],
                }
            )
    stuck_days = current.get("thresholds", {}).get("stuck_days", 7)
    chronic_days = current.get("thresholds", {}).get("chronic_days", 14)
    stalled = [item for item in incidents if item["stalled_days"] >= stuck_days]
    chronic = sorted(
        (item for item in stalled if item["stalled_days"] >= chronic_days),
        key=lambda x: (-x["stalled_days"], x["key"]),
    )
    stuck = sorted(
        (item for item in stalled if item["stalled_days"] < chronic_days),
        key=lambda x: (-x["stalled_days"], x["key"]),
    )
    dpas = [dict(item) for item in current["dpas"] if _open_dpa(item)]
    open_dpa_keys = {item["key"] for item in dpas}
    for incident in incidents:
        incident["open_dpa_keys"] = [
            key for key in incident.get("dpa_keys", []) if key in open_dpa_keys
        ]
    overdue_dpas: list[dict[str, Any]] = []
    no_sla_dpas: list[dict[str, Any]] = []
    for dpa in dpas:
        due = _dpa_due(dpa, current)
        dpa["due_date"] = due
        if due is None:
            dpa["sla_label"] = "no SLA"
            dpa["sla_class"] = "muted"
            no_sla_dpas.append(dpa)
        else:
            remaining = (due - as_of).days
            if remaining < 0:
                dpa["sla_label"] = f"OVERDUE {-remaining}d"
                dpa["sla_class"] = "bad"
                overdue_dpas.append(dpa)
            else:
                dpa["sla_label"] = f"on track {remaining}d"
                dpa["sla_class"] = "good"

    decisions: list[dict[str, str]] = []
    for incident in incidents:
        postmortem = incident.get("postmortem", {})
        if incident["postmortem_class"] == "bad":
            state = str(postmortem.get("state") or "").casefold()
            obligation = (
                "Postmortem sign-off"
                if state in {"filled", "written"}
                else "Postmortem"
            )
            decisions.append(
                {
                    "key": incident["key"],
                    "rank": 10,
                    "text": f"{obligation} {incident['postmortem_label']}. Owner: {incident['owner']}.",
                }
            )
        if incident.get("unlinked_dpa_keys"):
            keys = ", ".join(incident["unlinked_dpa_keys"])
            decisions.append(
                {
                    "key": incident["key"],
                    "rank": 40,
                    "text": f"Link, do not re-file: {keys} are named in evidence but not linked in Jira. Owner: {incident['owner']}.",
                }
            )
        if (
            incident["priority"].casefold() == "blocker"
            and incident["stalled_days"] >= chronic_days
        ):
            decisions.append(
                {
                    "key": incident["key"],
                    "rank": 50,
                    "text": f"Chronic Blocker: {incident['stalled_days']} days stalled. Owner: {incident['owner']}.",
                }
            )
    oldest_overdue = (
        min(overdue_dpas, key=lambda item: item["due_date"] or date.max)
        if overdue_dpas
        else None
    )
    for dpa in overdue_dpas:
        suffix = (
            "; it is the oldest SLA breach on this board"
            if dpa is oldest_overdue
            else ""
        )
        decisions.append(
            {
                "key": dpa["key"],
                "rank": 20,
                "text": f"{dpa['key']} ({dpa['parent']}) is {dpa['sla_label']}{suffix}.",
            }
        )
    for dpa in no_sla_dpas:
        decisions.append(
            {
                "key": dpa["key"],
                "rank": 30,
                "text": f"{dpa['key']} ({dpa['parent']}) has no priority and therefore no SLA clock. Set one or park it.",
            }
        )
    decisions.extend(current.get("additional_decisions", []))

    obligations: dict[str, list[tuple[int, str, str, str]]] = defaultdict(list)
    priority_rank = {"blocker": 4, "critical": 3, "major": 2, "minor": 1}
    for incident in incidents:
        owes: list[str] = []
        if not incident.get("open_dpa_keys"):
            owes.append("DPAs")
        if incident.get("unlinked_dpa_keys"):
            owes = ["DPA links"]
        if incident["postmortem_class"] == "bad":
            owes.append(
                "postmortem sign-off"
                if str(incident.get("postmortem", {}).get("state", "")).casefold()
                in {"filled", "written"}
                else "postmortem"
            )
        elif (
            incident["postmortem_label"].startswith("due ")
            and not incident.get("open_dpa_keys")
            and str(incident.get("postmortem", {}).get("state") or "").casefold()
            in {"blank", "missing"}
        ):
            owes.append("postmortem")
        if owes:
            severity = priority_rank.get(incident["priority"].casefold(), 0)
            overdue_weight = 1000 if incident["postmortem_class"] == "bad" else 0
            worst = (
                f"{incident['key']} {incident['postmortem_label']}"
                if "postmortem" in " ".join(owes).casefold()
                else f"{incident['key']} no DPAs filed"
            )
            if "DPA links" in owes:
                worst = f"{incident['key']} - {len(incident['unlinked_dpa_keys'])} DPA(s) identified but not linked"
            obligations[incident["owner"]].append(
                (
                    overdue_weight + incident["stalled_days"] * 10 + severity,
                    " + ".join(dict.fromkeys(owes)),
                    worst,
                    incident["key"],
                )
            )
    for dpa in overdue_dpas:
        parent = incident_by_key.get(dpa["parent"])
        owner = str(dpa.get("owner") or (parent or {}).get("owner") or "Unknown")
        if parent:
            obligations[owner].append(
                (1400, "overdue DPA", f"{dpa['key']} {dpa['sla_label']}", parent["key"])
            )
    owner_rows = []
    for owner, items in obligations.items():
        worst = max(items, key=lambda item: item[0])
        owes = " + ".join(
            dict.fromkeys(part for item in items for part in item[1].split(" + "))
        )
        incident_count = len({item[3] for item in items})
        owner_rows.append(
            {
                "owner": owner,
                "incidents": incident_count,
                "owes": owes,
                "worst": worst[2],
                "weight": worst[0] + incident_count * 100,
            }
        )
    owner_rows.sort(key=lambda item: (-item["weight"], item["owner"]))

    zero_dpa = [item for item in incidents if not item.get("open_dpa_keys")]
    zero_dpa_blockers = [
        item for item in zero_dpa if item["priority"].casefold() == "blocker"
    ]
    unlinked = [item for item in incidents if item.get("unlinked_dpa_keys")]
    cannot_drop = [item for item in incidents if item.get("why_open")]
    one_artifact = [
        item
        for item in cannot_drop
        if not item.get("open_dpa_keys")
        and item.get("postmortem", {}).get("state") in {"filled", "not_needed"}
    ]
    patterns = [
        f"{len(zero_dpa)} of {len(incidents)} active incidents have zero linked DPAs, {len(zero_dpa_blockers)} of them Blockers ({', '.join(item['key'] for item in zero_dpa)}).",
    ]
    if no_sla_dpas:
        patterns.append(
            f"{len(no_sla_dpas)} open DPA(s) carry no priority, so no SLA clock ({', '.join(item['key'] for item in no_sla_dpas)})."
        )
    if unlinked:
        count = sum(len(item["unlinked_dpa_keys"]) for item in unlinked)
        patterns.append(
            f"{count} DPA ticket(s) are named in evidence but not linked to their incident ({'; '.join(item['key'] + ': ' + ', '.join(item['unlinked_dpa_keys']) for item in unlinked)}). Link them rather than re-filing them."
        )
    if cannot_drop:
        patterns.append(
            f"{len(cannot_drop)} active incident(s) cannot satisfy the drop-off rule ({', '.join(item['key'] for item in cannot_drop)}). {len(one_artifact)} are one artifact away: the postmortem obligation is satisfied and a linked DPA is missing."
        )
    patterns.extend(current.get("additional_patterns", []))
    for correction in corrections:
        patterns.append(
            f"Data quality: {correction['description']} Not counted as progress: {correction['exclusion_reason']}."
        )

    metrics = {
        "new": len(new_keys),
        "open": len(incidents),
        "chronic": len(chronic),
        "postmortems_overdue": sum(
            item["postmortem_class"] == "bad" for item in incidents
        ),
        "dpas_overdue": len(overdue_dpas),
        "open_dpas": len(dpas),
        "progressed": len({item["subject"] for item in progressed}),
        "stalled": len(stalled),
        "resolved": len(resolved),
        "affected_entities": len(
            {value for item in incidents for value in item.get("affected_entities", [])}
        ),
    }
    return {
        "as_of": as_of,
        "previous_as_of": prior_date,
        "scope": current["scope"],
        "coverage": current["coverage"],
        "metrics": metrics,
        "incidents": incidents,
        "new": [incident_by_key[key] for key in new_keys],
        "progressed": progressed,
        "corrections": corrections,
        "chronic": chronic,
        "stuck": stuck,
        "resolved": resolved,
        "dpas": dpas,
        "decisions": sorted(
            decisions,
            key=lambda item: (int(item.get("rank", 60)), item["key"], item["text"]),
        ),
        "owners": owner_rows,
        "patterns": patterns,
        "history": current.get("history", []),
        "caveats": current.get("caveats", []),
    }


def _rows(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def _incident_table_rows(
    items: list[dict[str, Any]], base_url: str, *, stalled: bool = False
) -> str:
    rows = []
    for item in items:
        pm = _badge(item["postmortem_label"], item["postmortem_class"])
        if stalled:
            rows.append(
                "<tr>"
                f"<td>{_ticket(item['key'], base_url)}</td><td>{html.escape(item['group'])}</td>"
                f"<td>{_badge(item['status'])}</td><td>{item['stalled_days']}</td>"
                f"<td>{html.escape(item['owner'])}</td><td>{pm}</td><td>{html.escape(str(item.get('why_open') or '—'))}</td>"
                "</tr>"
            )
        else:
            rows.append(
                "<tr>"
                f"<td>{_ticket(item['key'], base_url)}</td><td>{html.escape(item['group'])}</td>"
                f"<td>{html.escape(item['priority'])}</td><td>{_badge(item['status'])}</td>"
                f"<td>{item['age_days']}</td><td>{item['stalled_days']}</td><td>{pm}</td>"
                f"<td>{len(item.get('open_dpa_keys', []))}</td><td>{html.escape(item['owner'])}</td>"
                "</tr>"
            )
    return "".join(rows)


def _trend(history: list[dict[str, Any]], metrics: dict[str, int]) -> str:
    series = [*history, metrics][-3:]
    if len(series) < 2:
        return "Trend begins with this run."
    labels = (
        ("open", "open"),
        ("dpas_overdue", "overdue DPAs"),
        ("postmortems_overdue", "overdue postmortems"),
        ("chronic", "chronic"),
    )
    parts = []
    for key, label in labels:
        values = [int(row.get(key, 0)) for row in series]
        arrow = (
            "↘" if values[-1] < values[0] else ("↗" if values[-1] > values[0] else "=")
        )
        parts.append(f"{label} {' → '.join(map(str, values))} {arrow}")
    return f"Trend over {len(series)} runs: " + " · ".join(parts)


def render_html(model: dict[str, Any]) -> str:
    metrics = model["metrics"]
    base_url = str(
        model["scope"].get("jira_base_url") or "https://example.invalid/browse"
    )
    coverage = model["coverage"]
    nav_items = [
        ("decisions", "⚡ Needs a Decision"),
        ("owners", "👤 Who Owes What"),
        ("metrics", "📊 Metrics"),
        ("new", "🆕 New Today"),
        ("progressed", "📈 Progressed"),
        ("stalled", "⚠️ Stalled"),
        ("patterns", "🔁 Estate Patterns"),
        ("resolved", "✅ Resolved"),
        ("dpas", "🛡️ DPA Tracker"),
        ("all-open", "📋 All Open"),
    ]
    if any(item.get("deep_dive") for item in model["incidents"]):
        nav_items.append(("drill-downs", "🔎 Drill-downs"))
    nav = " · ".join(f'<a href="#{anchor}">{label}</a>' for anchor, label in nav_items)
    metric_cards = "".join(
        f'<div class="metric"><strong>{metrics[key]}</strong><span>{label}</span></div>'
        for key, label in (
            ("new", "New"),
            ("open", "Open total"),
            ("chronic", "Chronic"),
            ("postmortems_overdue", "Postmortems overdue"),
            ("dpas_overdue", "DPAs overdue"),
            ("open_dpas", "Open DPAs"),
        )
    )
    if metrics["affected_entities"]:
        metric_cards += f'<div class="metric"><strong>{metrics["affected_entities"]}</strong><span>Affected entities</span></div>'
    decision_items = (
        "".join(
            f"<li>{_ticket(item['key'], base_url)} — {html.escape(item['text'])}</li>"
            for item in model["decisions"]
        )
        or "<li>None.</li>"
    )
    owner_rows = (
        "".join(
            f"<tr><td>{html.escape(item['owner'])}</td><td>{item['incidents']}</td><td>{html.escape(item['owes'])}</td><td>{html.escape(item['worst'])}</td></tr>"
            for item in model["owners"]
        )
        or '<tr><td colspan="4">None.</td></tr>'
    )
    new_rows = (
        "".join(
            f"<tr><td>{_ticket(item['key'], base_url)}</td><td>{html.escape(item['group'])}</td><td>{html.escape(item['summary'])}</td><td>{_badge(item['status'])}</td></tr>"
            for item in model["new"]
        )
        or '<tr><td colspan="4">None.</td></tr>'
    )
    progressed_rows = (
        "".join(
            f"<tr><td>{_ticket(item['subject'], base_url)}</td><td>{html.escape(str(item.get('group') or '—'))}</td><td>{html.escape(item['description'])}</td><td>{_badge(item['current_status'])}</td></tr>"
            for item in model["progressed"]
        )
        or '<tr><td colspan="4">None.</td></tr>'
    )
    resolved_rows = (
        "".join(
            f"<tr><td>{_ticket(item['key'], base_url)}</td><td>{html.escape(item['group'])}</td><td>{html.escape(item['status'])}</td></tr>"
            for item in model["resolved"]
        )
        or '<tr><td colspan="3">None.</td></tr>'
    )
    dpa_rows = (
        "".join(
            "<tr>"
            f"<td>{_ticket(item['key'], base_url)}<small>{html.escape(item['summary'])}</small></td>"
            f"<td>{_ticket(item['parent'], base_url)}</td><td>{html.escape(item['priority'])}</td>"
            f"<td>{_badge(item['status'])}</td><td>{html.escape(item['created'])}</td>"
            f"<td>{item['due_date'].isoformat() if item['due_date'] else '—'}</td><td>{_badge(item['sla_label'], item['sla_class'])}</td>"
            "</tr>"
            for item in model["dpas"]
        )
        or '<tr><td colspan="7">None.</td></tr>'
    )
    drilldowns = []
    for incident in model["incidents"]:
        details = incident.get("deep_dive")
        if not isinstance(details, dict):
            continue
        whys = (
            "".join(
                f"<li>{html.escape(str(item))}</li>"
                for item in details.get("five_whys", [])
            )
            or "<li>Root cause: Not yet determined.</li>"
        )
        talking = (
            _rows([str(item) for item in details.get("talking_points", [])])
            or "<li>No sourced talking point.</li>"
        )
        questions = "".join(
            f"<dt>{html.escape(str(item.get('question', '')))}</dt><dd>{html.escape(str(item.get('answer', '')))}</dd>"
            for item in details.get("questions", [])
        )
        drilldowns.append(
            f'<details id="incident-{html.escape(incident["key"])}"><summary>{_ticket(incident["key"], base_url)} — {html.escape(incident["summary"])}</summary>'
            f"<h3>Facts and customer risk</h3><p>{html.escape(str(details.get('facts') or 'Not available from current evidence.'))}</p>"
            f"<p><strong>Customer risk:</strong> {html.escape(str(details.get('customer_risk') or 'Not assessed.'))}</p>"
            f"<h3>Five Whys</h3><ol>{whys}</ol><p><strong>Preventive action:</strong> {html.escape(str(details.get('preventive_action') or 'Not yet defined.'))}</p>"
            f"<h3>What to say</h3><ul>{talking}</ul><h3>If they ask</h3><dl>{questions or '<dt>No sourced questions.</dt><dd>—</dd>'}</dl></details>"
        )
    coverage_gaps = coverage.get("gaps", [])
    coverage_html = (
        ""
        if coverage["status"] == "complete"
        else f'<div class="coverage {coverage["status"]}"><strong>Coverage: {html.escape(coverage["status"])}</strong><ul>{_rows([str(item) for item in coverage_gaps])}</ul></div>'
    )
    caveats = (
        " ".join(html.escape(str(item)) for item in model["caveats"])
        or "None recorded."
    )
    summary = (
        f"{metrics['new']} new · {metrics['progressed']} progressed · {metrics['stalled']} stalled "
        f"({metrics['chronic']} chronic) · {metrics['resolved']} resolved · {metrics['open']} open total · "
        f"{metrics['open_dpas']} open DPAs ({metrics['dpas_overdue']} overdue, "
        f"{sum(item['due_date'] is None for item in model['dpas'])} no SLA)"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Daily OpEx Digest — {model["as_of"].isoformat()}</title>
<style>
:root{{--ink:#293d52;--red:#aa3028;--orange:#ef7f1a;--blue:#1264d7;--line:#d9dde2;--soft:#f6f7f8;--green:#20a64a}}
*{{box-sizing:border-box}} body{{margin:0;color:var(--ink);font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#fff}}
main{{max-width:1500px;margin:0 auto;padding:28px 30px 60px}} nav{{position:sticky;top:0;z-index:2;padding:10px 0;background:rgba(255,255,255,.96);font-weight:650}} nav a{{color:#1769aa;text-decoration:none}}
h1{{font-size:30px;margin:8px 0}} h2{{margin-top:32px;border-left:5px solid var(--red);padding-left:12px;color:var(--red)}} h3{{color:var(--red);border-left:4px solid var(--orange);padding-left:10px}}
.subtitle{{color:#65727c;font-weight:600}} .summary{{font-size:18px;font-weight:700;margin:24px 0}} .decision-box{{border:4px solid var(--orange);background:#fff8f0;padding:20px 46px}} .decision-box li{{margin:5px 0}}
.metric-grid{{display:flex;flex-wrap:wrap}} .metric{{min-width:120px;border:1px solid var(--line);padding:12px;text-align:center}} .metric strong{{display:block;font-size:27px}} .metric span{{color:#78858c}}
.table-wrap{{overflow-x:auto}} table{{width:100%;border-collapse:collapse}} th{{background:var(--ink);color:white;text-align:left;padding:10px 12px}} td{{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}} td small{{display:block;color:#65727c;margin-top:3px}}
a{{color:var(--blue)}} .badge{{display:inline-block;border-radius:999px;padding:3px 12px;font-weight:700;white-space:nowrap}} .good{{background:#e7f6e8;color:var(--green)}} .bad{{background:#fde9e7;color:#c33a31}} .warn{{background:#fff2e5;color:#e77712}} .due{{background:#fff3ca;color:#9b7900}} .info{{background:#e6f0fa;color:#1672a5}} .muted{{background:#eff1f2;color:#78858c}}
.trend{{border-left:4px solid var(--ink);background:var(--soft);padding:10px 14px;margin-top:14px;color:#62717c}} .coverage{{padding:12px;margin:14px 0;background:#fff3ca}} .coverage.blocked{{background:#fde9e7}} details{{border:1px solid var(--line);padding:12px;margin:10px 0}} summary{{font-weight:700;cursor:pointer}}
footer{{border-top:2px solid #999;margin-top:28px;padding-top:12px}} footer p{{margin:5px 0}} dl{{display:grid;grid-template-columns:minmax(160px,1fr) 3fr;gap:6px 18px}} dt{{font-weight:700}}
@media(max-width:760px){{main{{padding:16px}}nav{{position:static}}.decision-box{{padding:15px 24px}}th,td{{padding:8px;font-size:14px}}}}
@media print{{nav{{display:none}}main{{max-width:none;padding:0}}.decision-box,.badge{{print-color-adjust:exact;-webkit-print-color-adjust:exact}}section,details,tr{{break-inside:avoid}}}}
</style>
</head>
<body><main>
<nav aria-label="Digest sections">{nav}</nav>
<header><h1>Daily OpEx Digest — {model["as_of"].isoformat()}</h1><p class="subtitle">{html.escape(model["scope"]["label"])} · {" + ".join(html.escape(item) for item in model["scope"]["priorities"])} · vs prior snapshot {model["previous_as_of"].isoformat()}</p><p class="summary">{summary}</p>{coverage_html}</header>
<section id="decisions"><h2>⚡ Needs a Decision</h2><div class="decision-box"><ol>{decision_items}</ol></div></section>
<section id="owners"><h2>👤 Who Owes What</h2><p>Grouped by owner, worst first. This is the only part of the board that is a to-do list.</p><div class="table-wrap"><table><thead><tr><th>Owner</th><th>Incidents</th><th>Owes</th><th>Worst item</th></tr></thead><tbody>{owner_rows}</tbody></table></div><p class="trend">{html.escape(_trend(model["history"], metrics))}</p></section>
<section id="metrics"><h2>📊 Metrics</h2><div class="metric-grid">{metric_cards}</div></section>
<section id="new"><h2>🆕 New Today</h2><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>Summary</th><th>Status</th></tr></thead><tbody>{new_rows}</tbody></table></div></section>
<section id="progressed"><h2>📈 Progressed</h2><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>What changed since {model["previous_as_of"].isoformat()}</th><th>Current status</th></tr></thead><tbody>{progressed_rows}</tbody></table></div></section>
<section id="stalled"><h2>⚠️ Stalled</h2><h3>Chronic ({current_threshold(model, "chronic")}d+) — {len(model["chronic"])}</h3><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>Status</th><th>Days stalled</th><th>Owner</th><th>Postmortem</th><th>Why it can't close</th></tr></thead><tbody>{_incident_table_rows(model["chronic"], base_url, stalled=True) or '<tr><td colspan="7">None.</td></tr>'}</tbody></table></div><h3>Stuck ({current_threshold(model, "stuck")}-{current_threshold(model, "chronic") - 1}d) — {len(model["stuck"])}</h3><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>Status</th><th>Days stalled</th><th>Owner</th><th>Postmortem</th><th>Why it can't close</th></tr></thead><tbody>{_incident_table_rows(model["stuck"], base_url, stalled=True) or '<tr><td colspan="7">None.</td></tr>'}</tbody></table></div></section>
<section id="patterns"><h2>🔁 Estate Patterns</h2><ul>{_rows(model["patterns"])}</ul></section>
<section id="resolved"><h2>✅ Resolved / Dropped-off</h2><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>Last status</th></tr></thead><tbody>{resolved_rows}</tbody></table></div></section>
<section id="dpas"><h2>🛡️ DPA Tracker</h2><div class="table-wrap"><table><thead><tr><th>DPA</th><th>Parent</th><th>Priority</th><th>Status</th><th>Created</th><th>SLA due</th><th>Flag</th></tr></thead><tbody>{dpa_rows}</tbody></table></div></section>
<section id="all-open"><h2>📋 All Open Incidents</h2><div class="table-wrap"><table><thead><tr><th>Ticket</th><th>Group</th><th>Priority</th><th>Status</th><th>Age (d)</th><th>Stalled (d)</th><th>Postmortem</th><th>Open DPAs</th><th>Owner</th></tr></thead><tbody>{_incident_table_rows(model["incidents"], base_url)}</tbody></table></div></section>
{('<section id="drill-downs"><h2>🔎 Incident Drill-downs</h2>' + "".join(drilldowns) + "</section>") if drilldowns else ""}
<footer><p>Generated {html.escape(str(model["coverage"].get("generated_at") or model["as_of"].isoformat()))} · prior snapshot {model["previous_as_of"].isoformat()} · sources: {", ".join(html.escape(str(item)) for item in coverage["sources"])}.</p><p><strong>Caveats:</strong> {caveats}</p></footer>
</main></body></html>"""


def current_threshold(model: dict[str, Any], name: str) -> int:
    # Thresholds are attached by main after model construction to keep the model compact.
    return int(
        model.get("thresholds", {}).get(f"{name}_days", 14 if name == "chronic" else 7)
    )


def render_markdown(model: dict[str, Any]) -> str:
    metrics = model["metrics"]
    lines = [
        f"# Daily OpEx Digest — {model['as_of'].isoformat()}",
        "",
        f"{model['scope']['label']} · {' + '.join(model['scope']['priorities'])} · vs prior snapshot {model['previous_as_of'].isoformat()}",
        "",
        f"{metrics['new']} new · {metrics['progressed']} progressed · {metrics['stalled']} stalled ({metrics['chronic']} chronic) · {metrics['resolved']} resolved · {metrics['open']} open total · {metrics['open_dpas']} open DPAs ({metrics['dpas_overdue']} overdue)",
        "",
        "## ⚡ Needs a Decision",
        "",
    ]
    lines.extend(
        f"{index}. {item['key']} — {item['text']}"
        for index, item in enumerate(model["decisions"], 1)
    )
    if not model["decisions"]:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## 👤 Who Owes What",
            "",
            "| Owner | Incidents | Owes | Worst item |",
            "| --- | ---: | --- | --- |",
        ]
    )
    lines.extend(
        f"| {item['owner']} | {item['incidents']} | {item['owes']} | {item['worst']} |"
        for item in model["owners"]
    )
    lines.extend(
        [
            "",
            _trend(model["history"], metrics),
            "",
            "## 📊 Metrics",
            "",
            json.dumps(metrics, sort_keys=True),
            "",
            "## 🆕 New Today",
            "",
        ]
    )
    lines.extend(f"- {item['key']}: {item['summary']}" for item in model["new"])
    if not model["new"]:
        lines.append("None.")
    lines.extend(["", "## 📈 Progressed", ""])
    lines.extend(
        f"- {item['subject']}: {item['description']} ({item['current_status']})"
        for item in model["progressed"]
    )
    if not model["progressed"]:
        lines.append("None.")
    lines.extend(["", "## ⚠️ Stalled", "", f"### Chronic — {len(model['chronic'])}"])
    lines.extend(
        f"- {item['key']}: {item['stalled_days']}d, {item.get('why_open') or 'reason unknown'}"
        for item in model["chronic"]
    )
    lines.extend(["", f"### Stuck — {len(model['stuck'])}"])
    lines.extend(
        f"- {item['key']}: {item['stalled_days']}d, {item.get('why_open') or 'reason unknown'}"
        for item in model["stuck"]
    )
    lines.extend(["", "## 🔁 Estate Patterns", ""])
    lines.extend(f"- {item}" for item in model["patterns"])
    lines.extend(["", "## ✅ Resolved / Dropped-off", ""])
    lines.extend(f"- {item['key']}" for item in model["resolved"])
    if not model["resolved"]:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## 🛡️ DPA Tracker",
            "",
            "| DPA | Parent | Priority | Status | Created | SLA |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(
        f"| {item['key']} | {item['parent']} | {item['priority']} | {item['status']} | {item['created']} | {item['sla_label']} |"
        for item in model["dpas"]
    )
    lines.extend(
        [
            "",
            "## 📋 All Open Incidents",
            "",
            "| Ticket | Group | Priority | Status | Age | Stalled | Postmortem | DPAs | Owner |",
            "| --- | --- | --- | --- | ---: | ---: | --- | ---: | --- |",
        ]
    )
    lines.extend(
        f"| {item['key']} | {item['group']} | {item['priority']} | {item['status']} | {item['age_days']} | {item['stalled_days']} | {item['postmortem_label']} | {len(item.get('open_dpa_keys', []))} | {item['owner']} |"
        for item in model["incidents"]
    )
    lines.extend(
        [
            "",
            f"Generated {model['coverage'].get('generated_at') or model['as_of'].isoformat()} · sources: {', '.join(map(str, model['coverage']['sources']))}.",
            "",
            "Caveats: " + (" ".join(map(str, model["caveats"])) or "None recorded."),
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and render a Daily OpEx Digest from normalized snapshots"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser(
        "validate", help="validate current and prior snapshot JSON"
    )
    render = sub.add_parser("render", help="render deterministic HTML and/or Markdown")
    for command in (validate, render):
        command.add_argument("--current", required=True, type=Path)
        command.add_argument("--previous", required=True, type=Path)
    render.add_argument("--output-dir", required=True, type=Path)
    render.add_argument("--format", choices=("html", "md", "both"), default="html")
    render.add_argument("--basename", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = _load(args.current)
    previous = _load(args.previous)
    model = build_model(current, previous)
    model["thresholds"] = current.get("thresholds", {})
    if args.command == "validate":
        print(json.dumps({"status": "valid", "metrics": model["metrics"]}, indent=2))
        return 0
    basename = args.basename or f"opex-digest-{model['as_of'].isoformat()}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", basename):
        raise SnapshotError(
            "basename must contain only letters, digits, dots, underscores, and hyphens"
        )
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SnapshotError(f"cannot create output directory: {exc}") from exc
    requested: list[tuple[Path, str]] = []
    if args.format in {"html", "both"}:
        path = args.output_dir / f"{basename}.html"
        requested.append((path, render_html(model)))
    if args.format in {"md", "both"}:
        path = args.output_dir / f"{basename}.md"
        requested.append((path, render_markdown(model)))
    for path, _ in requested:
        if path.exists():
            raise SnapshotError(f"refusing to overwrite existing report: {path}")
    written = []
    for path, content in requested:
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(content)
        except FileExistsError as exc:
            raise SnapshotError(
                f"refusing to overwrite existing report: {path}"
            ) from exc
        written.append(str(path))
    print(
        json.dumps(
            {"status": "rendered", "metrics": model["metrics"], "written": written},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SnapshotError as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
