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
    errors, notes, events, queries, currency_limits = [], {}, {}, [], []

    def require(condition, message):
        if not condition:
            errors.append(message)

    if not isinstance(data, dict) or data.get("schema_version") != "FreshnessEvidence.v2":
        raise ValueError("expected FreshnessEvidence.v2; older evidence requires recollection")
    anchor = timestamp(data["collected_at"])
    since = anchor - timedelta(days=14)
    mode = data["baseline_mode"]
    require(mode in {"first_design", "revision_comparison"}, "invalid baseline mode")
    require(nonempty(data.get("source_ref")), "actual baseline/requirement source_ref missing")
    if mode == "first_design":
        require(data.get("design_ref") is None and data.get("design_at") is None, "first_design conflicts with prior design coordinates")
    if mode == "revision_comparison":
        require(nonempty(data.get("design_ref")), "design revision missing")
        require(data.get("design_at") is not None, "design_at unknown; comparison incomplete")
    if data.get("design_at") is not None:
        require(timestamp(data["design_at"]) <= anchor, "design_at later than anchor")
    roots, owners, repos = data["roots"], data["owners"], data["repos"]
    require(strings(roots) and bool(roots), "root tickets missing or duplicated")
    require(isinstance(owners, dict) and bool(owners) and all(nonempty(k) and nonempty(v) for k, v in owners.items()), "owner identities/provenance missing")
    require(strings(repos) and bool(repos), "repository scope missing or duplicated")
    gaps = data["gaps"]
    require(isinstance(gaps, list) and not gaps, "source gaps remain")
    tickets, mrs = data["tickets"], data["mrs"]
    if not all(isinstance(x, dict) for x in (tickets, mrs, owners)) or not strings(roots) or not strings(repos):
        raise ValueError("invalid scope/collection containers")
    read_refs, interface_refs, inventory_refs = set(), set(), set()

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
        inventory_refs.update(ids)
        queries.append({"source": label, "query_ref": value.get("query_ref"),
                        "pages": len(pages), "items": len(items), "reported_totals": totals,
                        "cursors": [{"cursor": p["cursor"], "next": p["next"]} for p in pages],
                        "item_refs": ids,
                        "item_provenance": [{k: item[k] for k in
                            ("ref", "source_ref", "observed_at", "revision", "item_kind", "kind_source_ref")
                            if k in item} for item in items],
                        "scope": {k: value[k] for k in
                        ("repo_ref", "mode", "owner", "role", "scope_ref", "since", "until") if k in value}})
        return items

    ticket_queue, mr_queue = list(roots), []

    def links(item, label):
        require(strings(item["ticket_links"]) and strings(item["mr_links"]), f"{label}: invalid links")
        ticket_queue.extend(item["ticket_links"])
        mr_queue.extend(item["mr_links"])

    def canonical_note(note):
        # Acquisition locators/clocks and stream projection metadata are receipts,
        # not the source record's identity or content/version.
        content = {key: note.get(key) for key in
                   ("ref", "revision", "author", "at", "updated_at", "body", "content", "full_body")}
        content["ticket_links"] = sorted(note["ticket_links"])
        content["mr_links"] = sorted(note["mr_links"])
        return content

    def read_note(note, label, allow_empty=False, event=False):
        before = len(errors)
        require(nonempty(note["ref"]) and nonempty(note.get("source_ref")) and nonempty(note.get("revision")), f"{label}: source/revision missing")
        legitimate_empty = (allow_empty and (event or note.get("record_kind") == "review_submission")
                            and nonempty(note.get("kind_source_ref")))
        text_body = isinstance(note.get("body"), str) and (legitimate_empty or nonempty(note.get("body")))
        structured_event = event and isinstance(note.get("content"), dict) and bool(note["content"])
        require((text_body or structured_event) and nonempty(note.get("author")) and note.get("full_body") is True, f"{label}: missing full body/content/author")
        require(timestamp(note["at"]) <= anchor, f"{label}: occurrence later than anchor; recollect")
        review_currency_limited = False
        if note.get("updated_at") is not None:
            require(timestamp(note["updated_at"]) <= anchor, f"{label}: edit later than anchor; recollect")
        else:
            metadata = note.get("edit_metadata", {})
            sourced = nonempty(metadata.get("source_ref"))
            native_event = event and metadata.get("semantics") in {"immutable", "not_exposed"} and sourced
            observed_review = (not event and note.get("record_kind") == "review_submission"
                               and metadata.get("semantics") == "not_exposed" and sourced
                               and note.get("observed_at") is not None)
            require(native_event or observed_review, f"{label}: edit metadata missing; source currency unknown")
            if observed_review:
                require(timestamp(note["observed_at"]) >= timestamp(note["at"]), f"{label}: review observation precedes submission")
                review_currency_limited = True
        previous = notes.get(note["ref"], events.get(note["ref"]))
        require(previous is None or canonical_note(previous) == canonical_note(note), f"{label}: conflicting duplicate discussion identity")
        require(not (event and note["ref"] in notes or not event and note["ref"] in events), f"{label}: conflicting note/event classification")
        if len(errors) == before:
            (events if event else notes)[note["ref"]] = note
            read_refs.add(note["ref"])
            if review_currency_limited:
                limitation = {"ref": note["ref"], "observed_at": note["observed_at"],
                              "source_ref": metadata["source_ref"],
                              "limitation": "Full review body read; edit history unavailable. Historical currency unverified; agent must assess materiality and revalidate actual source before handoff."}
                if limitation not in currency_limits:
                    currency_limits.append(limitation)
        links(note, label)

    def discussions(item, ref):
        discussion = item["discussion"]
        require(nonempty(discussion.get("inventory_ref")), f"{ref}: stream inventory basis missing")
        required, streams = discussion["required_streams"], discussion["streams"]
        require(strings(required) and bool(required), f"{ref}: required stream inventory missing")
        if not isinstance(streams, dict):
            raise ValueError("streams must be a map")
        require(set(required) <= set(streams), f"{ref}: required stream missing")
        for name, value in streams.items():
            role = value["role"]
            require(role in {"notes", "threads", "events", "mixed"}, f"{ref}/{name}: invalid stream role")
            for record in stream(value, f"{ref}/{name}"):
                if role == "threads":
                    links(record, ref)
                    for note in stream(record["notes"], f"{ref}/{name}/{record['ref']}/notes"):
                        read_note(note, ref)
                else:
                    if role == "mixed":
                        require(record.get("item_kind") in {"note", "event"}
                                and nonempty(record.get("kind_source_ref")), f"{ref}/{name}: item kind/source projection missing")
                    read_note(record, ref, allow_empty=value.get("allow_empty_body") is True,
                              event=role == "events" or role == "mixed" and record.get("item_kind") == "event")

    # Preserve each real query, including independently exhausted zero-result roles.
    coverage, query_ids = set(), set()
    merge_queries = data["merge_queries"]
    if not isinstance(merge_queries, list):
        raise ValueError("merge_queries must be a list")
    roles = {"author", "coauthor", "merger"}
    for search in merge_queries:
        repo, query_mode = search["repo_ref"], search["mode"]
        require(repo in repos, f"{repo}: query repository outside scope")
        require(nonempty(search.get("scope_ref")), f"{repo}: query filter scope evidence missing")
        require(timestamp(search["since"]) == since and timestamp(search["until"]) == anchor, f"{repo}: merge window must be exactly fourteen days")
        require(search["query_ref"] not in query_ids, "merge query identity duplicated")
        query_ids.add(search["query_ref"])
        if query_mode == "repo_wide":
            require(search["owner"] is None and search["role"] is None, f"{repo}: repo-wide query has owner filter")
            coverage.update((repo, owner, role) for owner in owners for role in roles)
        elif query_mode == "per_owner":
            owner, role = search["owner"], search["role"]
            require(owner in owners and role in roles, f"{repo}: invalid owner/role filter")
            coverage.add((repo, owner, role))
        else:
            require(False, f"{repo}: invalid merge query mode")
        for merge in stream(search, f"{repo}/{search['query_ref']}"):
            require(since <= timestamp(merge["merged_at"]) <= anchor, f"{repo}: merge outside requested window")
            participation = merge["participation"]
            require(isinstance(participation, dict) and set(participation) == roles and all(strings(v) for v in participation.values()), f"{repo}: participation roles missing")
            require(any(participation.values()), f"{repo}: participation unresolved; attribution gap")
            if query_mode == "per_owner":
                require(search["owner"] in participation.get(search["role"], []), f"{repo}: result does not match query owner/role")
            if any(set(v) & set(owners) for v in participation.values()):
                mr_queue.append(merge["ref"])
                require(repo in mrs.get(merge["ref"], {}).get("repo_refs", []), f"{repo}: owner merge unread or wrong repository")
    for note in data["confirmation_records"]:
        read_note(note, "confirmation")
    attempted_tickets, attempted_mrs, read_tickets, read_mrs = set(), set(), set(), set()
    involved = set(repos)
    while ticket_queue or mr_queue:
        is_ticket = bool(ticket_queue)
        queue = ticket_queue if is_ticket else mr_queue
        ref = queue.pop()
        attempted = attempted_tickets if is_ticket else attempted_mrs
        if ref in attempted:
            continue
        attempted.add(ref)
        collection = tickets if is_ticket else mrs
        if ref not in collection:
            errors.append(f"unread {'ticket' if is_ticket else 'MR'}: {ref}")
            continue
        item = collection[ref]
        require(nonempty(item["system"]) and nonempty(item["source_kind"]), f"{ref}: source identity missing")
        mapping = item.get("repo_mapping", {})
        mapping_kind = mapping.get("kind")
        require(mapping_kind in {"native_repository", "mapped_repositories", "no_repository"}
                and nonempty(mapping.get("source_ref")), f"{ref}: repository mapping unresolved or provenance missing")
        require(strings(item["repo_refs"]), f"{ref}: invalid repository binding")
        if mapping_kind == "no_repository":
            require(is_ticket and item["source_kind"] == "external_ticket" and not item["repo_refs"], f"{ref}: no-repository mapping only applies to external tickets")
        else:
            require(bool(item["repo_refs"]), f"{ref}: repository binding missing")
        if not is_ticket or item["source_kind"] == "codehost_issue":
            require(mapping_kind == "native_repository" and bool(item["repo_refs"]), f"{ref}: native codehost repository required")
        involved.update(item["repo_refs"])
        require(set(item["repo_refs"]) <= set(repos), f"{ref}: involved repository omitted from scope")
        links(item, ref)
        require(nonempty(item.get("inspected_ref")) and nonempty(item.get("revision")) and item.get("full_body") is True and isinstance(item.get("body"), str), f"{ref}: full description/status/link revision missing")
        if (nonempty(item.get("inspected_ref")) and nonempty(item.get("revision"))
                and item.get("full_body") is True and isinstance(item.get("body"), str)):
            (read_tickets if is_ticket else read_mrs).add(ref)
            read_refs.update((ref, item.get("inspected_ref")))
        discussions(item, ref)
    for repo in involved:
        require(all((repo, owner, role) in coverage for owner in owners for role in roles), f"{repo}: owner/author-coauthor-merger query coverage incomplete")
    require(set(tickets) == read_tickets, "ticket inventory differs from read reachable scope")
    require(set(mrs) == read_mrs, "MR inventory differs from read linked/owner-merge scope")
    inspected_subjects, content_refs = set(), set()
    for inspected in data["interface_inspections"]:
        before = len(errors)
        require(nonempty(inspected["ref"]) and inspected["subject_ref"] in read_refs and nonempty(inspected["revision"]) and nonempty(inspected["source_ref"]) and inspected["full_body"] is True and isinstance(inspected["body"], str), "inspection lacks read subject/revision/source/full body")
        require(inspected["kind"] in {"code", "interface", "contract", "diff", "content"}, "invalid inspection kind")
        require(inspected["ref"] not in read_refs and inspected["ref"] not in inventory_refs and inspected["ref"] not in content_refs, "inspection evidence identity must be distinct")
        if not nonempty(inspected["body"]):
            require(inspected["kind"] == "diff" and nonempty(inspected.get("empty_diff_ref")), "empty content needs verified empty diff evidence")
        if len(errors) == before:
            content_refs.add(inspected["ref"])
            inspected_subjects.add(inspected["subject_ref"])
            if inspected["kind"] in {"code", "interface", "contract"} and nonempty(inspected["body"]):
                interface_refs.add(inspected["ref"])
    require(read_mrs <= inspected_subjects, "linked/selected MR diff/content inspection missing")
    refs = read_refs | content_refs
    changes = data["changes"]
    require(isinstance(changes, list) and bool(changes), "assumption reconciliation missing")
    for change in changes:
        require(all(nonempty(change.get(k)) for k in ("assumption", "implication", "simpler_path")), "change analysis missing")
        require(change.get("disposition") in {"retain", "revise", "retire", "investigate"}, "invalid change disposition")
        require(change.get("kind") in {"status", "interface"}, "change kind missing")
        evidence = change["evidence_refs"]
        require(strings(evidence) and bool(evidence) and set(evidence) <= refs, "change cites unread evidence")
        if change.get("kind") == "interface":
            require(bool(set(evidence) & interface_refs), "interface change lacks inspected interface/code/contract evidence")
    responsibilities = data["responsibilities"]
    if not isinstance(responsibilities, dict):
        raise ValueError("responsibilities must map scope IDs")
    for scope, responsibility in responsibilities.items():
        require(nonempty(scope) and strings(responsibility["owners"]) and bool(responsibility["owners"]) and set(responsibility["owners"]) <= set(owners) and nonempty(responsibility["source_ref"]), "responsibility provenance/owners missing")
    proposal, blockers = data["proposed_assessment"], data["blockers"]
    require(nonempty(proposal), "proposed assessment missing")
    require(isinstance(blockers, list), "invalid blockers")
    excerpts = []
    for blocker in blockers:
        before = len(errors)
        note = notes.get(blocker["note_ref"])
        responsibility = responsibilities.get(blocker["scope_id"], {})
        require(blocker["owner"] in responsibility.get("owners", []) and note is not None and note.get("author") == blocker["owner"], "blocker lacks scoped responsible owner's source quote")
        require(note is not None and isinstance(note.get("body"), str) and nonempty(blocker["quote"]) and blocker["quote"] in note["body"], "blocker quote is not exact source text")
        currency = blocker["current_evidence_refs"]
        require(strings(currency) and bool(currency) and set(currency) <= refs, "blocker current-evidence binding missing")
        require(nonempty(blocker.get("currency_assessment")), "blocker currency assessment missing")
        if len(errors) == before:
            excerpts.append(dict(blocker, at=note["at"], source_ref=note.get("source_ref"), revision=note.get("revision")))
    return {"schema_version": "FreshnessCheck.v2", "section": TITLE,
            "validation_status": "incomplete" if errors else "complete",
            "semantic_review_pending": True, "proposed_assessment": proposal,
            "baseline_mode": mode, "source_ref": data.get("source_ref"),
            "design_ref": data.get("design_ref"), "design_at": data.get("design_at"),
            "since": since.isoformat(), "until": anchor.isoformat(),
            "coverage": {"tickets": len(read_tickets), "mrs": len(read_mrs), "notes": len(notes), "events": len(events), "repos": len(involved)},
            "frontier": {"tickets": sorted(attempted_tickets - read_tickets), "mrs": sorted(attempted_mrs - read_mrs)},
            "attempted": {"tickets": len(attempted_tickets), "mrs": len(attempted_mrs)},
            "scope": {"roots": roots, "owners": owners, "repos": sorted(involved), "responsibilities": responsibilities},
            "queries": queries, "errors": errors, "gaps": gaps, "currency_limits": currency_limits, "changes": changes,
            "matched_source_excerpts": excerpts,
            "limits": "Mechanical normalized assertions only. Agent semantic review of full context, supersession, current interfaces and availability is mandatory in this same run before the final technical assessment."}


def markdown(result):
    lines = [f"## {TITLE}", "", f"Validation status: {result['validation_status']} (semantic_review_pending)",
             f"Baseline: {result['baseline_mode']}; {result['source_ref']}; design {result['design_ref']} ({result['design_at']})",
             ("No prior design exists." if result["design_ref"] is None and result["design_at"] is None
              else "First-design mode conflicts with supplied prior design coordinates; see errors.")
             if result["baseline_mode"] == "first_design" else "Revision comparison.",
             f"Proposed assessment (semantic_review_pending): {result['proposed_assessment']}",
             f"Merge window: {result['since']} through {result['until']}",
             f"Coverage: {json.dumps(result['coverage'], sort_keys=True)}",
             f"Scope and ownership provenance: {json.dumps(result['scope'], sort_keys=True)}", ""]
    for query in result["queries"]:
        lines.append(f"- Source coverage: {query['source']}; {query['query_ref']}; pages={query['pages']}; items={query['items']}; reported totals={query['reported_totals']}")
        if query["scope"]:
            lines.append("  Query scope and terminal receipts: " + json.dumps({"scope": query["scope"], "cursors": query["cursors"], "item_refs": query["item_refs"], "item_provenance": query["item_provenance"]}, sort_keys=True))
        elif query["item_provenance"]:
            lines.append("  Item source receipts: " + json.dumps(query["item_provenance"], sort_keys=True))
    lines.extend(["", "Attempted: " + json.dumps(result["attempted"], sort_keys=True), "Frontier: " + json.dumps(result["frontier"], sort_keys=True)])
    lines.append("Currency limitations: " + json.dumps(result["currency_limits"], sort_keys=True))
    for change in result["changes"]:
        lines.extend([f"- Previous assumption: {change['assumption']}",
                      f"  Current evidence: {', '.join(change['evidence_refs'])}",
                      f"  Implication: {change['implication']}",
                      f"  Simpler path: {change['simpler_path']} ({change['disposition']})"])
    for blocker in result["matched_source_excerpts"]:
        lines.append(f"- Matched source excerpt for {blocker['scope_id']}: {blocker['owner']} at {blocker['note_ref']} ({blocker['at']}): {blocker['quote']}")
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
        if isinstance(data, dict) and data.get("schema_version") == "FreshnessEvidence.v1":
            print(json.dumps({"schema_version": "FreshnessCheck.v2", "validation_status": "incomplete",
                              "semantic_review_pending": True, "errors": ["FreshnessEvidence.v1 requires recollection for v2 coverage; no automatic upgrade."]}))
            return 2
        result = check(data)
        print(markdown(result) if args.format == "markdown" else json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 1 if result["validation_status"] == "incomplete" else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        print(json.dumps({"schema_version": "FreshnessCheck.v2", "validation_status": "incomplete", "semantic_review_pending": True, "errors": [f"Invalid input or unable to assess: {type(error).__name__}"]}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
