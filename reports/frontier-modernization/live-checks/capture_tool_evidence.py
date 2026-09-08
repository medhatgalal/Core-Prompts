"""Capture observable local tool events and final reviewer messages; never reasoning."""
import datetime
import hashlib
import json
from pathlib import Path

PARENT = "01a08233-5e2d-7c20-b46b-68e3aee1c9fc"
OUT = Path(__file__).resolve().parent / "evidence"
SESSIONS = Path("/Users/medhat.galal/.codex/sessions/2026/09/08")
identities, summaries, finals, visible = [], [], [], []
for src in sorted(SESSIONS.glob("*.jsonl")):
    with src.open() as stream:
        try:
            meta = json.loads(stream.readline()).get("payload", {})
        except (ValueError, AttributeError):
            continue
    if meta.get("id") != PARENT and meta.get("parent_thread_id") != PARENT:
        continue
    records, allowed, call_ids, settings = [], set(), [], []
    final_count = 0
    for raw in src.read_text().splitlines():
        event = json.loads(raw)
        item = event.get("payload", {})
        if event.get("type") == "turn_context":
            settings.append({key: item[key] for key in ("model", "effort") if key in item})
        if event.get("type") != "response_item":
            continue
        kind = item.get("type")
        if kind in ("function_call", "custom_tool_call") and item.get("name") not in ("list_agents", "wait_agent"):
            allowed.add(item["call_id"])
            payload = {key: item[key] for key in ("type", "id", "call_id", "name", "namespace", "arguments", "input") if key in item}
            records.append({"timestamp": event.get("timestamp"), "payload": payload})
            call_ids.append({"call_id": item["call_id"], "name": item.get("name"), "namespace": item.get("namespace")})
        elif kind in ("function_call_output", "custom_tool_call_output") and item.get("call_id") in allowed:
            payload = {key: item[key] for key in ("type", "id", "call_id", "output") if key in item}
            if item["call_id"] == "call_Er7Gh4n086C8oPDgAG8CcdqW":
                payload.pop("output", None)
                payload["output_omitted_reason"] = "Irrelevant read-only memory lookup results; original native tool result remains in the host session. The source read in this combined result was incomplete and recovered separately."
                payload["original_output_sha256"] = hashlib.sha256(json.dumps(item.get("output"), ensure_ascii=False).encode()).hexdigest()
            records.append({"timestamp": event.get("timestamp"), "payload": payload})
        elif kind == "message" and item.get("role") == "assistant" and item.get("phase") == "commentary" and meta.get("id") == PARENT:
            visible.append({"thread_id": meta["id"], "timestamp": event.get("timestamp"), "message_id": item.get("id"), "content": item.get("content")})
        elif kind == "message" and item.get("role") == "assistant" and item.get("phase") == "final_answer" and meta.get("id") != PARENT:
            finals.append({"thread_id": meta["id"], "agent_path": meta.get("agent_path"), "timestamp": event.get("timestamp"), "message_id": item.get("id"), "content": item.get("content")})
            final_count += 1
            if meta["id"] == "01a0823c-a467-7173-938b-6c5cbead3781" and final_count == 2:
                break  # Cedar was released to unrelated parent work after its contract review.
    name = "controller" if meta["id"] == PARENT else meta.get("agent_path", meta["id"]).rsplit("/", 1)[-1]
    dest = OUT / f"{name}-tool-trace.jsonl"
    dest.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    (OUT / f"{name}-call-ids.json").write_text(json.dumps(call_ids, indent=2) + "\n")
    identities.append({"thread_id": meta.get("id"), "parent_thread_id": meta.get("parent_thread_id"), "agent_path": meta.get("agent_path"), "cli_version": meta.get("cli_version"), "model_provider": meta.get("model_provider"), "multi_agent_version": meta.get("multi_agent_version"), "turn_model_settings": settings, "source_file": str(src)})
    summaries.append({"thread_id": meta["id"], "agent_path": meta.get("agent_path"), "trace": str(dest.relative_to(OUT.parent)), "tool_record_count": len(records), "call_count": len(call_ids), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
(OUT / "host-session-identities.json").write_text(json.dumps(identities, indent=2) + "\n")
(OUT / "reviewer-final-results.json").write_text(json.dumps(finals, indent=2, ensure_ascii=False) + "\n")
(OUT / "controller-visible-messages.json").write_text(json.dumps(visible, indent=2, ensure_ascii=False) + "\n")
summary = {"capture_time": datetime.datetime.now(datetime.timezone.utc).isoformat(), "scope": "This demonstration controller and its direct independent reviewers only; cedar ends after its second final answer, before release to unrelated parent work", "filter": "Actual tool calls/results, visible controller progress and reviewer final answers; excludes reasoning, all other messages, world state, unrelated agent inventory and the initial irrelevant read-only memory result (identified omission; original remains in native history).", "cutoff": "Snapshot of completed records available at capture; excludes pending capture output and any later events.", "reasoning_records_exported": 0, "sessions": summaries}
(OUT / "trace-extraction.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
