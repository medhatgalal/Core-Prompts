"""Policy-aware failure-history recovery. Receipts are mechanical FAKE fixtures."""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import re
import subprocess
import sys

import pytest

from test_shaping_loop import failed_g3_review, loop_policy
from test_shaping_runtime import accept_fixture, advance, prepare, runtime, version, workshop, write_json


def recorded_failure(rt, *, old_policy):
    if not old_policy:
        loop_policy(rt)
    advance(rt, 2)
    order, candidate = prepare(rt, "G3", "historical-failure")
    failed_g3_review(rt, order, candidate)
    failure_order_id = order["work_order_id"]
    if old_policy:
        loop_policy(rt)
        for number in range(3):
            order, candidate = prepare(rt, f"G{number}", "after-rebind")
            accept_fixture(rt, order, candidate)
    return failure_order_id


def corrupt_event(rt, work_order, mutation):
    state = rt._load()
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    order = state["orders"][work_order]
    if mutation == "malformed_hash":
        order["policy_hash"] = "not-a-sha256"
    elif mutation == "missing_hash":
        del order["policy_hash"]
    elif mutation == "wrong_binding_digest":
        order["policy_hash"] = "f" * 64
        encoded = (json.dumps(order["policy_bindings"], sort_keys=True,
                              separators=(",", ":"), allow_nan=False) + "\n").encode()
        if order["policy_hash"] == hashlib.sha256(encoded).hexdigest():
            order["policy_hash"] = "e" * 64
    elif mutation == "event_gate":
        event["gate"] = "G2"
    elif mutation == "unknown_order":
        event["record"]["work_order_id"] = "missing-work-order"
    elif mutation == "event_seal":
        event["return_hash"] = "f" * 64
    elif mutation == "seal_hash":
        order["seal"]["return_hash"] = "f" * 64
    elif mutation == "missing_seal":
        order["seal"] = None
    elif mutation == "receipt_provenance":
        event["provenance"]["sha256"] = "not-a-sha256"
    elif mutation == "receipt_binding":
        event["review"]["policy_hash"] = "f" * 64
    else:
        raise AssertionError(mutation)
    rt._commit(state, version(rt))


@pytest.mark.parametrize("mutation", [
    "malformed_hash", "missing_hash", "wrong_binding_digest", "unknown_order",
    "event_gate", "event_seal", "seal_hash", "missing_seal",
    "receipt_provenance", "receipt_binding",
])
@pytest.mark.parametrize("old_policy", [True, False], ids=["previous-policy", "current-policy"])
def test_unverifiable_review_history_enters_recovery_without_pointer_change(
        workshop, runtime, mutation, old_policy):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=old_policy)
    corrupt_event(rt, work_order, mutation)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Recovery):
        prepare(rt, "G3", f"recovery-{mutation}")
    assert (rt.root / "state/run.json").read_bytes() == before


def test_previous_policy_floor_failure_is_retained_but_not_reclassified(workshop, runtime):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=True)
    state = rt._load()
    historical = state["orders"][work_order]
    assert re.fullmatch(r"[0-9a-f]{64}", historical["policy_hash"])
    assert historical["policy_hash"] != runtime.digest(runtime.encoded(state["policy_bindings"]))
    predecessor = rt.snapshot(historical["predecessor"])
    assert "research-coverage.json" not in predecessor["files"]
    before_events = len(rt._load()["observations"])
    order, candidate = prepare(rt, "G3", "after-policy-rebind")
    assert order["work_order_id"] == "G3-after-policy-rebind"
    assert candidate.is_dir()
    events = rt._load()["observations"]
    assert any(item["record"]["work_order_id"] == work_order for item in events)
    assert len(events) == before_events  # prepare adds an order, not an observation


def test_current_policy_same_facts_still_hold_without_pointer_change(workshop, runtime):
    rt = workshop
    recorded_failure(rt, old_policy=False)
    rt.reopen("G3", "FAKE fixture preserves current-policy floor history", version(rt))
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Hold, match="floor-only G3 retry blocked") as caught:
        prepare(rt, "G3", "same-current-facts")
    assert not str(caught.value).startswith("recovery_pending:")
    assert (rt.root / "state/run.json").read_bytes() == before


def test_live_snapshot_storage_corruption_is_recovery(workshop, runtime):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=False)
    state = rt._load()
    predecessor = state["orders"][work_order]["predecessor"]
    snapshot_path = rt.root / "accepted" / f"{predecessor}.json"
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["files"]["research-coverage.json"]["base64"] = "e30="
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Recovery):
        prepare(rt, "G3", "corrupt-current-coverage")
    assert (rt.root / "state/run.json").read_bytes() == before


def cli_prepare(rt, runtime, tmp_path):
    spec = {
        "schema_version": 1, "work_order_id": "G3-cli-recovery", "gate": "G3",
        "author": "fixture-author", "reviewer": {
            "identity": "fixture-reviewer", "independent": True,
            "assignment_evidence": "sources/assignment.txt",
            "context_evidence": "sources/context.txt"},
        "inputs": ["sources/original.txt", "sources/assignment.txt",
                   "sources/context.txt", "sources/rubric.txt"],
        "source_revision": "fixture-source-1", "resource_revision": "fixture-resource-1",
        "skill_allowlist": ["fixture-only"], "original_constraints": ["FAKE fixture"],
        "assigned_questions": [], "source_access_scope": "fixture only",
        "effort_bound": "one fixture", "stop_conditions": ["recovery"],
        "shape_basis": [],
    }
    spec_path = write_json(tmp_path / "cli-spec.json", spec)
    return subprocess.run(
        [sys.executable, runtime.__file__, "prepare", "--run", str(rt.root),
         "--expected-version", str(version(rt)), "--spec", str(spec_path)],
        text=True, capture_output=True, check=False, cwd=rt.root,
    )


def assert_cli(result, exit_code, status):
    assert result.returncode == exit_code, (result.returncode, result.stdout, result.stderr)
    assert json.loads(result.stdout)["status"] == status, (result.stdout, result.stderr)


def test_cli_reports_recovery_exit_and_preserves_pointer(workshop, runtime, tmp_path):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=True)
    corrupt_event(rt, work_order, "wrong_binding_digest")
    before = (rt.root / "state/run.json").read_bytes()
    result = cli_prepare(rt, runtime, tmp_path)
    assert_cli(result, 3, "recovery_pending")
    assert json.loads(result.stdout)["status"] == "recovery_pending"
    assert (rt.root / "state/run.json").read_bytes() == before


@pytest.mark.parametrize("old_policy", [True, False], ids=["previous-policy", "current-policy"])
def test_json_list_order_id_is_cli_recovery(workshop, runtime, tmp_path, old_policy):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=old_policy)
    state = rt._load()
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    event["record"]["work_order_id"] = ["malformed-json-list"]
    rt._commit(state, version(rt))
    before = (rt.root / "state/run.json").read_bytes()
    result = cli_prepare(rt, runtime, tmp_path)
    assert_cli(result, 3, "recovery_pending")
    with pytest.raises(runtime.Recovery):
        prepare(rt, "G3", "list-order-id")
    assert (rt.root / "state/run.json").read_bytes() == before


def replace_seal_hash(runtime, seal):
    seal["return_hash"] = runtime.digest(runtime.encoded(
        {key: value for key, value in seal.items() if key != "return_hash"}))


def bad_historical_coverage(rt, runtime, work_order, damage):
    """Inject a hash-valid historical snapshot and matching common bindings.

    Latest accepted G2 remains valid. This is deliberate mechanical corruption,
    not an accepted semantic Research result.
    """
    state = rt._load()
    order = state["orders"][work_order]
    prior = deepcopy(rt.snapshot(order["predecessor"]))
    historical_order_id = prior["work_order"]["work_order_id"]
    if damage == "missing":
        del prior["files"]["research-coverage.json"]
    else:
        raw = b'{"schema_version":1,"opened":"invalid-array"}\n'
        prior["files"]["research-coverage.json"] = {
            "sha256": runtime.digest(raw), "base64": base64.b64encode(raw).decode("ascii")}
    prior_subject = {name: file["sha256"] for name, file in prior["files"].items()}
    prior["work_order"]["seal"]["subject"] = prior_subject
    replace_seal_hash(runtime, prior["work_order"]["seal"])
    prior["receipt"].update(subject=prior_subject,
                            return_hash=prior["work_order"]["seal"]["return_hash"])
    raw_receipt = runtime.encoded(prior["receipt"])
    prior["receipt_bytes"] = base64.b64encode(raw_receipt).decode("ascii")
    bad_key = rt._immutable("accepted", prior)
    state["accepted_orders"][historical_order_id].update(
        snapshot=bad_key, receipt_hash=runtime.digest(raw_receipt))
    state["orders"][historical_order_id] = deepcopy(prior["work_order"])
    order["predecessor"] = bad_key
    order["seal"]["predecessor"] = bad_key
    if damage == "missing":
        del order["seal"]["subject"]["research-coverage.json"]
    else:
        order["seal"]["subject"]["research-coverage.json"] = prior_subject["research-coverage.json"]
    replace_seal_hash(runtime, order["seal"])
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    event["return_hash"] = order["seal"]["return_hash"]
    event["review"].update(predecessor=bad_key, subject=deepcopy(order["seal"]["subject"]),
                           return_hash=order["seal"]["return_hash"])
    # Align even the mutable receipt for the RED run: failure must reach coverage,
    # rather than the initial fix's raw-file equality check.
    raw_receipt = runtime.encoded(event["review"])
    (rt.root / event["provenance"]["path"]).write_bytes(raw_receipt)
    event["provenance"]["sha256"] = runtime.digest(raw_receipt)
    rt._commit(state, version(rt))
    return historical_order_id, bad_key


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_hash_valid_historical_current_coverage_reaches_classifier(
        workshop, runtime, tmp_path, monkeypatch, damage):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=False)
    rt.reopen("G2", "FAKE fixture creates a fresh valid latest G2", version(rt))
    fresh_order, candidate = prepare(rt, "G2", "latest-valid")
    accept_fixture(rt, fresh_order, candidate)
    historical_order_id, bad_key = bad_historical_coverage(rt, runtime, work_order, damage)
    state = rt._load()  # Must succeed: this is not an immutable-object hash failure.
    assert state["accepted"]["G2"] != bad_key
    latest = rt.snapshot(state["accepted"]["G2"])
    assert rt._opened_facts(latest, state)
    reached = []
    opened_facts = rt._opened_facts

    def trace(snapshot, state=None):
        reached.append(snapshot["work_order"]["work_order_id"])
        return opened_facts(snapshot, state)

    monkeypatch.setattr(rt, "_opened_facts", trace)
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Recovery, match="accepted G2 research-coverage"):
        prepare(rt, "G3", f"historical-coverage-{damage}")
    assert historical_order_id in reached
    result = cli_prepare(rt, runtime, tmp_path)
    assert_cli(result, 3, "recovery_pending")
    assert "accepted G2 research-coverage" in json.loads(result.stdout)["reason"]
    assert (rt.root / "state/run.json").read_bytes() == before


@pytest.mark.parametrize("old_policy", [True, False], ids=["previous-policy", "current-policy"])
@pytest.mark.parametrize("raw_receipt", ["deleted", "overwritten"])
def test_captured_history_survives_original_receipt_availability(
        workshop, runtime, tmp_path, old_policy, raw_receipt):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=old_policy)
    state = rt._load()
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    receipt_path = rt.root / event["provenance"]["path"]
    if raw_receipt == "deleted":
        receipt_path.unlink()
    else:
        receipt_path.write_text('{"unrelated":"FAKE overwritten receipt"}\n', encoding="utf-8")
    before = (rt.root / "state/run.json").read_bytes()
    facts = rt._floor_only_failure_facts(rt._load())
    assert (facts is None) == old_policy
    result = cli_prepare(rt, runtime, tmp_path)
    if old_policy:
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert rt._load()["observations"] == state["observations"]
    else:
        assert_cli(result, 2, "hold")
        assert "floor-only G3 retry blocked" in json.loads(result.stdout)["reason"]
        assert (rt.root / "state/run.json").read_bytes() == before


@pytest.mark.parametrize("old_policy", [True, False], ids=["previous-policy", "current-policy"])
@pytest.mark.parametrize("damage", ["path-binding", "unsafe-path"])
def test_captured_history_provenance_path_fail_closed(workshop, runtime, old_policy, damage):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=old_policy)
    state = rt._load()
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    path = "../outside.json" if damage == "unsafe-path" else "reviews/other.json"
    event["provenance"]["path"] = path
    if damage == "unsafe-path":
        event["record"]["evidence"] = path
    rt._commit(state, version(rt))
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Recovery):
        prepare(rt, "G3", "bad-provenance-path")
    assert (rt.root / "state/run.json").read_bytes() == before


@pytest.mark.parametrize("old_policy", [True, False], ids=["previous-policy", "current-policy"])
def test_legacy_provenance_digest_is_structural_not_raw_byte_authentication(
        workshop, runtime, old_policy):
    rt = workshop
    work_order = recorded_failure(rt, old_policy=old_policy)
    state = rt._load()
    event = next(item for item in state["observations"]
                 if item["record"]["work_order_id"] == work_order)
    event["provenance"]["sha256"] = "f" * 64
    rt._commit(state, version(rt))
    facts = rt._floor_only_failure_facts(rt._load())
    assert (facts is None) == old_policy


def test_mixed_policy_history_keeps_current_mean_only_stop(workshop, runtime, tmp_path):
    rt = workshop
    old_order_id = recorded_failure(rt, old_policy=True)
    order, candidate = prepare(rt, "G3", "current-failure")
    failed_g3_review(rt, order, candidate)
    state = rt._load()
    assert len(state["observations"]) == 2
    assert state["orders"][old_order_id]["policy_hash"] != order["policy_hash"]
    current_review = state["observations"][-1]["review"]
    assert min(item["score"] for item in current_review["scores"]["dimensions"].values()) >= 3
    assert current_review["scores"]["overall"] < 4
    before = (rt.root / "state/run.json").read_bytes()
    with pytest.raises(runtime.Hold, match="floor-only G3 retry blocked"):
        prepare(rt, "G3", "mixed-history-repeat")
    result = cli_prepare(rt, runtime, tmp_path)
    assert_cli(result, 2, "hold")
    assert "floor-only G3 retry blocked" in json.loads(result.stdout)["reason"]
    assert (rt.root / "state/run.json").read_bytes() == before
