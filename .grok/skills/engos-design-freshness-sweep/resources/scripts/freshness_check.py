#!/usr/bin/env python3
"""Check normalized freshness evidence and render a bounded analysis; no remote I/O."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

TITLE = "What changed since this was designed / simpler path that exists today"


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and all(nonempty(x) for x in value) and len(set(value)) == len(value)


def check(data):
    """Return asserted coverage checks, never a semantic or authenticated verdict."""
    errors, notes, refs, queries = [], {}, set(), []

    def require(condition, message):
        if not condition:
            errors.append(message)

    if not isinstance(data, dict) or data.get("schema_version") != "FreshnessEvidence.v1":
        raise ValueError("expected FreshnessEvidence.v1 object")
    anchor, designed = timestamp(data["collected_at"]), timestamp(data["design_at"])
    since = anchor - timedelta(days=14)
    require(designed <= anchor, "design_at is later than collection anchor")
    require(nonempty(data.get("design_ref")), "design revision missing")
    roots, owners, repos = data["roots"], data["owners"], data["repos"]
    require(strings(roots) and bool(roots), "root tickets missing or duplicated")
    require(isinstance(owners, dict) and bool(owners) and all(nonempty(k) and nonempty(v) for k, v in owners.items()), "owner identities/provenance missing")
    require(strings(repos) and bool(repos), "repository scope missing or duplicated")
    gaps = data["gaps"]
    require(isinstance(gaps, list) and not gaps, "source gaps remain")
    tickets, mrs, merges = data["tickets"], data["mrs"], data["merges"]
    if not all(isinstance(x, dict) for x in (tickets, mrs, merges, owners)) or not strings(roots) or not strings(repos):
        raise ValueError("invalid scope/collection containers")
    require(set(merges) == set(repos), "merge searches do not cover exactly every repository")

    def stream(value, label):
        if not isinstance(value, dict):
            raise ValueError(f"{label}: expected stream object")
        require(nonempty(value.get("query_ref")), f"{label}: query provenance missing")
        pages = value.get("pages")
        if not isinstance(pages, list) or not pages:
            errors.append(f"{label}: pages missing")
            return []
        items, seen_cursors, expected, totals = [], set(), None, []
        for index, page in enumerate(pages):
            if not isinstance(page, dict) or not isinstance(page.get("items"), list):
                raise ValueError(f"{label}: malformed page")
            cursor, following = page["cursor"], page["next"]
            require(cursor == expected and (cursor is None or nonempty(cursor)), f"{label}: broken cursor chain")
            require(cursor not in seen_cursors, f"{label}: repeated cursor")
            seen_cursors.add(cursor)
            require(following is None or nonempty(following), f"{label}: invalid next cursor")
            require(index == len(pages) - 1 or following is not None, f"{label}: pages after terminal cursor")
            expected = following
            total = page["total"]
            require(total is None or type(total) is int and total >= 0, f"{label}: invalid total")
            if total is not None:
                totals.append(total)
            items.extend(page["items"])
        require(expected is None, f"{label}: pagination not exhausted")
        ids = [item["ref"] for item in items]
        require(all(nonempty(x) for x in ids) and len(set(ids)) == len(ids), f"{label}: duplicate/missing items")
        require(all(total == len(items) for total in totals), f"{label}: reported total mismatch")
        refs.update(ids)
        queries.append({"source": label, "query_ref": value.get("query_ref"),
                        "pages": len(pages), "items": len(items), "reported_totals": totals})
        return items

    def read_note(note, label, allow_empty=False):
        require(isinstance(note["body"], str) and (allow_empty or nonempty(note["body"])) and nonempty(note["author"]), f"{label}: missing full body/author")
        require(timestamp(note["at"]) <= anchor, f"{label}: note later than anchor; recollect")
        require(note["ref"] not in notes or notes[note["ref"]] == note, f"{label}: conflicting duplicate discussion identity")
        notes[note["ref"]] = note
        require(strings(note["ticket_links"]) and strings(note["mr_links"]), f"{label}: invalid discussion links")
        ticket_queue.extend(note["ticket_links"])
        mr_queue.extend(note["mr_links"])

    def discussions(item, ref, is_ticket):
        platform = item["platform"]
        expected = ({"jira": {"comments"}, "github": {"issue_comments"},
                     "gitlab": {"notes", "discussions"}} if is_ticket else
                    {"github": {"issue_comments", "reviews", "review_comments", "review_threads"},
                     "gitlab": {"notes", "discussions"}}).get(platform)
        require(expected is not None, f"{ref}: unsupported source platform")
        endpoints = item["discussion"]
        if not isinstance(endpoints, dict):
            raise ValueError("discussion must map endpoints to streams")
        require(expected is not None and set(endpoints) == expected, f"{ref}: required discussion endpoints missing or unexpected")
        for endpoint, value in endpoints.items():
            for record in stream(value, f"{ref}/{endpoint}"):
                if endpoint in {"discussions", "review_threads"}:
                    # Each returned thread has its own exhausted notes/replies stream.
                    for note in stream(record["notes"], f"{ref}/{endpoint}/{record['ref']}/notes"):
                        read_note(note, ref)
                else:
                    read_note(record, ref, allow_empty=endpoint == "reviews")

    ticket_queue, mr_queue = list(roots), []
    visited_tickets, visited_mrs = set(), set()
    for repo in repos:
        if repo not in merges:
            continue
        search = merges[repo]
        require(timestamp(search["since"]) == since and timestamp(search["until"]) == anchor, f"{repo}: merge window must be exactly fourteen days")
        require(strings(search["owners"]) and set(search["owners"]) == set(owners), f"{repo}: owner search incomplete")
        for merge in stream(search, repo):
            merged = timestamp(merge["merged_at"])
            require(since <= merged <= anchor, f"{repo}: merge outside requested window")
            require(strings(merge["participants"]) and bool(merge["participants"]), f"{repo}: merge participants missing")
            if set(merge["participants"]) & set(owners):
                mr_queue.append(merge["ref"])
                require(mrs.get(merge["ref"], {}).get("repo") == repo, f"{repo}: owner merge missing or in wrong repository")
    while ticket_queue or mr_queue:
        is_ticket = bool(ticket_queue)
        queue = ticket_queue if is_ticket else mr_queue
        ref = queue.pop()
        visited = visited_tickets if is_ticket else visited_mrs
        if ref in visited:
            continue
        visited.add(ref)
        collection = tickets if is_ticket else mrs
        if ref not in collection:
            errors.append(f"unread {'ticket' if is_ticket else 'MR'}: {ref}")
            continue
        item = collection[ref]
        refs.add(ref)
        tlinks, mlinks = item["links" if is_ticket else "ticket_links"], item["mrs" if is_ticket else "mr_links"]
        require(strings(tlinks) and strings(mlinks), f"{ref}: invalid links")
        ticket_queue.extend(tlinks)
        mr_queue.extend(mlinks)
        require(nonempty(item["inspected_ref"]), f"{ref}: description/status/link or diff/API inspection missing")
        refs.add(item["inspected_ref"])
        if not is_ticket:
            require(item["repo"] in repos, f"{ref}: involved repository omitted from scope")
        discussions(item, ref, is_ticket)
    require(set(tickets) == visited_tickets, "ticket inventory differs from reachable scope")
    require(set(mrs) == visited_mrs, "MR inventory differs from linked/owner-merge scope")
    changes = data["changes"]
    require(isinstance(changes, list) and bool(changes), "assumption reconciliation missing")
    for change in changes:
        require(all(nonempty(change.get(k)) for k in ("assumption", "implication", "simpler_path")), "change analysis missing")
        require(change.get("disposition") in {"retain", "revise", "retire", "investigate"}, "invalid change disposition")
        evidence = change["evidence_refs"]
        require(strings(evidence) and bool(evidence) and set(evidence) <= refs, "change cites uncollected evidence")
    verdict, blockers = data["verdict"], data["blockers"]
    require(verdict in {"ready", "incomplete", "blocked"}, "invalid verdict")
    require(isinstance(blockers, list), "invalid blockers")
    require(verdict == "blocked" or not blockers, "blockers require blocked verdict")
    accepted_blockers = []
    if verdict == "blocked":
        require(bool(blockers), "blocked verdict lacks owner confirmation")
        for blocker in blockers:
            before = len(errors)
            note = notes.get(blocker["note_ref"])
            require(nonempty(blocker.get("scope")), "blocker scope missing")
            require(blocker["owner"] in owners and note is not None and note["author"] == blocker["owner"], "blocker lacks responsible owner's source quote")
            require(note is not None and nonempty(blocker["quote"]) and blocker["quote"] in note["body"], "blocker quote is not exact source text")
            currency = blocker["current_evidence_refs"]
            require(strings(currency) and bool(currency) and set(currency) <= refs,
                    "blocker current-evidence binding missing")
            require(nonempty(blocker.get("currency_assessment")), "blocker currency assessment missing")
            if len(errors) == before:
                accepted_blockers.append(dict(blocker, at=note["at"]))
    status = "incomplete" if errors or verdict == "incomplete" else verdict
    return {"schema_version": "FreshnessCheck.v1", "section": TITLE, "status": status,
            "design_ref": data["design_ref"], "design_at": data["design_at"],
            "since": since.isoformat(), "until": anchor.isoformat(),
            "coverage": {"tickets": len(visited_tickets), "mrs": len(visited_mrs), "notes": len(notes), "repos": len(repos)},
            "scope": {"roots": roots, "owners": owners, "repos": repos}, "queries": queries,
            "errors": errors, "gaps": gaps, "changes": changes,
            "blockers": accepted_blockers if status == "blocked" else [],
            "limits": "Normalized assertions checked; remote completeness, reading, owner authenticity, semantic feasibility and authority not assessed."}


def markdown(result):
    lines = [f"## {TITLE}", "", f"Status: {result['status']}",
             f"Design: {result['design_ref']} ({result['design_at']})",
             f"Merge window: {result['since']} through {result['until']}",
             f"Coverage: {json.dumps(result['coverage'], sort_keys=True)}",
             f"Scope and ownership provenance: {json.dumps(result['scope'], sort_keys=True)}", ""]
    for query in result["queries"]:
        lines.append(f"- Source coverage: {query['source']}; {query['query_ref']}; pages={query['pages']}; items={query['items']}; reported totals={query['reported_totals']}")
    lines.append("")
    for change in result["changes"]:
        lines.extend([f"- Previous assumption: {change['assumption']}",
                      f"  Current evidence: {', '.join(change['evidence_refs'])}",
                      f"  Implication: {change['implication']}",
                      f"  Simpler path: {change['simpler_path']} ({change['disposition']})"])
    for blocker in result["blockers"]:
        lines.append(f"- Owner confirmation for {blocker['scope']}: {blocker['owner']} at {blocker['note_ref']} ({blocker['at']}): {blocker['quote']}")
        lines.append(f"  Currency evidence: {', '.join(blocker['current_evidence_refs'])}; {blocker['currency_assessment']}")
    lines.extend(["", "Gaps/check failures: " + json.dumps(result["gaps"] + result["errors"]), "", result["limits"]])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        def pairs(values):
            out = {}
            for key, value in values:
                if key in out:
                    raise ValueError("duplicate JSON key")
                out[key] = value
            return out
        data = json.loads(args.evidence.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError("non-JSON constant")))
        result = check(data)
        print(markdown(result) if args.format == "markdown" else json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 1 if result["status"] == "incomplete" else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        print(json.dumps({"schema_version": "FreshnessCheck.v1", "status": "incomplete", "errors": [f"Invalid input or unable to assess: {type(error).__name__}"]}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
