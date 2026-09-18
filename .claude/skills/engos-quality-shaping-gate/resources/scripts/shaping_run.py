#!/usr/bin/env python3
"""Controller-operated shaping journal. Python 3.11+, standard library only.

Identity, independent context, evidence meaning and pixel quality are host/reviewer
trust boundaries, not properties authenticated by this local consistency checker.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile


GATES = [f"G{i}" for i in range(5)]
MIN_OUTPUTS = [
    ["brief.md", "intake.md"], ["framed.md"], ["research-notes.md"],
    ["pitch.md", "pitch-summary.md", "workstreams.md", "traceability.md", "contracts.md",
     "security-owners.md", "component.mmd", "sequence.mmd", "data-flow.mmd"],
    ["betting-table-prep.md"],
]
PREDICATES = {
    "G0": ["original_preserved", "source_coverage", "fact_classification", "no_selected_solution"],
    "G1": ["problem_frame", "confirmed_appetite_walkaway", "boundaries_uncertainties", "no_selected_solution"],
    "G2": ["uncertainties_resolved", "evidence_sufficiency", "grounded_risks"],
    "G3": ["coherent_bounded_solution", "exemplar_coverage", "diagrams_visual",
           "contracts_security", "workstreams_proof", "constraints_traceability",
           "author_audit", "independent_review", "rubric_assessment"],
    "G4": ["saved_target_parity", "target_revision_pixels", "faithful_betting_prep", "no_delivery_discrepancy"],
}
TEAM = ["simplicity", "testability", "security", "architecture", "cost", "feasibility", "confidence"]
PITCH = ["problem_clarity", "appetite_fit", "solution_sharpness", "contract_quality", "boundary_discipline"]
ROLES = ["readback", "pixels", "inventory"]
DIAGRAMS = ["component.mmd", "sequence.mmd", "data-flow.mmd"]


def delivery_roles(surface):
    return ["readback", "structured", "inventory"] if surface == "json" else ROLES


class Hold(ValueError):
    """Invalid, conflicting or stale input; nothing was accepted."""


class Recovery(RuntimeError):
    """Persistent state cannot be verified; do not guess success."""


def require(condition, message):
    if not condition:
        raise Hold(message)


def shape(value, required, optional=()):
    require(isinstance(value, dict), "expected an object")
    require(set(required) <= value.keys(), f"missing fields: {sorted(set(required) - value.keys())}")
    require(value.keys() <= set(required) | set(optional), "unknown fields")
    return value


def string(value):
    require(isinstance(value, str) and bool(value.strip()), "expected a nonempty string")
    return value


def strings(value, nonempty=True):
    require(isinstance(value, list) and (bool(value) or not nonempty), "expected a string array")
    for item in value:
        string(item)
    require(len(set(value)) == len(value), "duplicate array entries")
    return value


def integer(value, minimum=0):
    require(type(value) is int and value >= minimum, "expected a nonnegative integer")
    return value


def boolean(value):
    require(type(value) is bool, "expected a boolean")


def number(value, low=1, high=5):
    require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
            "invalid finite score")
    return value


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", value),
            "invalid identifier")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Hold("nonfinite JSON number")))
    except (ValueError, UnicodeError) as exc:
        raise Hold(f"malformed JSON: {exc}") from exc


def safe_relative(value):
    string(value)
    path = PurePosixPath(value)
    require(not path.is_absolute() and "\\" not in value and ":" not in value
            and all(p not in ("", ".", "..") for p in value.split("/")), "unsafe relative path")
    return value


def guarded(path):
    """Reject symlinks in every existing component, including the supplied root."""
    path = Path(os.path.abspath(path))
    for component in [*reversed(path.parents), path]:
        require(not component.is_symlink(), f"symlink refused: {component}")
    return path


def read_bytes(path):
    path = guarded(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        require(stat.S_ISREG(info.st_mode), f"not a regular file: {path}")
        value = handle.read()
    require(bool(value.strip()), f"empty evidence/artifact: {path}")
    return value


def sync_directory(path):
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic_write(path, data):
    path = guarded(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def validate_policy(policy):
    shape(policy, ["schema_version", "policy_id", "gates", "scoring", "delivery_targets", "references"])
    require(type(policy["schema_version"]) is int and policy["schema_version"] == 1, "unsupported policy schema")
    string(policy["policy_id"])
    shape(policy["gates"], GATES)
    for i, gate in enumerate(GATES):
        entry = shape(policy["gates"][gate], ["predicates", "required_outputs"])
        strings(entry["predicates"])
        strings(entry["required_outputs"])
        require(set(PREDICATES[gate]) <= set(entry["predicates"]), f"missing mandatory {gate} predicates")
        require(set(MIN_OUTPUTS[i]) <= set(entry["required_outputs"]), f"missing mandatory {gate} outputs")
        for name in entry["required_outputs"]:
            safe_relative(name)
    score = shape(policy["scoring"], ["dimensions", "minimum_dimension", "minimum_overall"])
    require(strings(score["dimensions"]) == TEAM + PITCH, "rubric requires the ordered twelve dimensions")
    number(score["minimum_dimension"], 3, 5)
    number(score["minimum_overall"], 4, 5)
    shape(policy["references"], ["gates", "rubric"])
    for path in policy["references"].values():
        safe_relative(path)
    require(isinstance(policy["delivery_targets"], list), "targets must be an array")
    targets = []
    for target in policy["delivery_targets"]:
        shape(target, ["surface", "destination"])
        targets.append((string(target["surface"]), string(target["destination"])))
    require(len(set(targets)) == len(targets), "duplicate targets")


class Runtime:
    Hold, Recovery = Hold, Recovery
    MIN_OUTPUTS = MIN_OUTPUTS
    safe_relative = staticmethod(safe_relative)

    def __init__(self, root):
        self.root = guarded(root)

    def path(self, relative):
        return guarded(self.root / safe_relative(relative))

    @contextmanager
    def lock(self):
        require(self.root.is_dir(), "run root does not exist")
        path = self.path("state/controller.lock")
        path.parent.mkdir(exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "r+b") as handle:
            if os.name == "nt":
                import msvcrt
                if os.fstat(handle.fileno()).st_size == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise Hold("controller lock busy; retry after current operation") from exc
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _immutable(self, directory, value):
        data = encoded(value)
        key = digest(data)
        path = self.path(f"{directory}/{key}.json")
        if path.exists():
            require(read_bytes(path) == data, "immutable object conflict")
        else:
            atomic_write(path, data)
        return key

    def _object(self, directory, key):
        require(isinstance(key, str) and re.fullmatch(r"[0-9a-f]{64}", key), "invalid object hash")
        data = read_bytes(self.path(f"{directory}/{key}.json"))
        require(digest(data) == key, "immutable object hash mismatch")
        return decode(data)

    def snapshot(self, key):
        snapshot = self._object("accepted", key)
        for name, item in snapshot["files"].items():
            safe_relative(name)
            require(digest(base64.b64decode(item["base64"], validate=True)) == item["sha256"], "snapshot file corruption")
        return snapshot

    def _load(self):
        try:
            pointer = decode(read_bytes(self.path("state/run.json")))
            shape(pointer, ["version", "revision"])
            integer(pointer["version"])
            state = self._object("state/revisions", pointer["revision"])
            require(state["version"] == pointer["version"], "pointer version mismatch")
            require(state["schema_version"] == 1, "unsupported state schema")
            validate_policy(state["policy"])
            snapshots = {}
            for order_id, record in state["accepted_orders"].items():
                snap = self.snapshot(record["snapshot"])
                require(snap["run_id"] == state["run_id"] and snap["receipt"]["work_order_id"] == order_id,
                        "acceptance run/order mismatch")
                require(digest(base64.b64decode(snap["receipt_bytes"], validate=True)) == record["receipt_hash"],
                        "acceptance receipt mismatch")
                snapshots[record["snapshot"]] = snap
            predecessor = None
            for gate in GATES:
                if gate not in state["accepted"]:
                    require(not any(g in state["accepted"] for g in GATES[GATES.index(gate) + 1:]), "noncontiguous acceptance")
                    break
                snap = snapshots[state["accepted"][gate]]
                require(snap["gate"] == gate and snap["predecessor"] == predecessor, "broken predecessor chain")
                predecessor = state["accepted"][gate]
            return state
        except (Hold, OSError, KeyError, TypeError, AttributeError, IndexError, binascii.Error) as exc:
            raise Recovery(f"recovery_pending: {exc}") from exc

    def _replace_pointer(self, pointer):
        atomic_write(self.path("state/run.json"), encoded(pointer))

    def _commit(self, state, expected):
        if expected >= 0:
            require(self._load()["version"] == expected, "stale expected-version")
        state["version"] = expected + 1
        key = self._immutable("state/revisions", state)
        self._replace_pointer({"version": state["version"], "revision": key})

    def _expected(self, state, expected):
        integer(expected)
        require(state["version"] == expected, "stale expected-version")

    def _policy_binding(self, path):
        path = guarded(path)
        require(path.is_relative_to(self.root), "policy must be under run root")
        relative = path.relative_to(self.root).as_posix()
        self._input_name(relative)
        data = read_bytes(path)
        policy = decode(data)
        validate_policy(policy)
        paths = [relative, *policy["references"].values()]
        for name in paths:
            self._input_name(name)
        return policy, {name: digest(read_bytes(self.path(name))) for name in paths}, relative

    def init(self, run_id, controller, policy_path):
        identifier(run_id)
        string(controller)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.lock():
            require(not self.path("state/run.json").exists(), "run already initialized")
            require(not any(self.path(p).exists() for p in ("accepted", "state/revisions", "candidates")),
                    "recovery_pending: existing state without pointer; inspect before init")
            policy, hashes, path = self._policy_binding(policy_path)
            state = {"schema_version": 1, "version": 0, "run_id": run_id, "controller": controller,
                     "generation": 0, "policy": policy, "policy_bindings": hashes, "policy_path": path,
                     "accepted": {}, "accepted_orders": {}, "orders": {}, "deliveries": {}, "reopens": []}
            self._commit(state, -1)
            return {"run_id": run_id, "version": 0, "status": "initialized"}

    def policy(self):
        return self._load()["policy"]

    def status(self):
        # A read sees one old or new complete revision; no writer lock needed.
        state = self._load()
        bindings = [state["policy_bindings"]]
        if state["accepted"]:
            latest = state["accepted"][next(reversed(state["accepted"]))]
            bindings.append(self.snapshot(latest)["input_hashes"])
        drift = self._binding_drift(bindings)
        content_bindings = [state['policy_bindings']]
        if 'G3' in state['accepted']:
            content_bindings.append(self.snapshot(state['accepted']['G3'])['input_hashes'])
        content_drift = self._binding_drift(content_bindings)
        delivery_drift = []
        if "G4" in state["accepted"]:
            for operation in self.snapshot(state["accepted"]["G4"])["deliveries"].values():
                if operation["bundle"] != state["accepted"].get("G3") or operation["status"] != "verified":
                    continue
                for item in operation["record"]["evidence"].values():
                    try:
                        if digest(read_bytes(self.path(item["path"]))) != item["sha256"]:
                            delivery_drift.append(item["path"])
                    except (Hold, OSError):
                        delivery_drift.append(item["path"])
        return {"run_id": state["run_id"], "version": state["version"], "generation": state["generation"],
                "stage": next(reversed(state["accepted"]), None), "accepted": state["accepted"],
                "dependency_drift": sorted(drift),
                "delivery_drift": sorted(set(delivery_drift)),
                "content_ready": "G3" in state["accepted"] and not content_drift,
                "delivery_state": "verified" if "G4" in state["accepted"] and not drift and not delivery_drift else "delivery_pending",
                "orders": state["orders"], "deliveries": state["deliveries"], "status": "consistent"}

    def _input_name(self, name):
        safe_relative(name)
        require(name.split("/")[0] not in {"state", "accepted", "candidates"}, "input uses controller/candidate namespace")

    def _binding_drift(self, groups):
        # Never merge authorities by dict.update: overlapping paths must satisfy
        # every pin, not whichever one was inserted last.
        drift = set()
        for bindings in groups:
            for name, expected in bindings.items():
                try:
                    if digest(read_bytes(self.path(name))) != expected:
                        drift.add(name)
                except (Hold, OSError):
                    drift.add(name)
        return sorted(drift)

    def _check_bindings(self, state, order=None):
        groups = [state["policy_bindings"]]
        if order:
            groups.append(order["input_hashes"])
            # Predecessor source dependencies remain current even if omitted by a new worker.
            if order["predecessor"]:
                groups.append(self.snapshot(order["predecessor"])["input_hashes"])
        changed = self._binding_drift(groups)
        require(not changed, f"changed dependency: {', '.join(changed)}; reopen affected gate")

    def prepare(self, spec, expected):
        shape(spec, ["schema_version", "work_order_id", "gate", "author", "reviewer", "inputs", "source_revision",
                     "resource_revision", "skill_allowlist", "original_constraints", "assigned_questions",
                     "source_access_scope", "effort_bound", "stop_conditions"])
        require(type(spec["schema_version"]) is int and spec["schema_version"] == 1, "unsupported work-order schema")
        order_id = identifier(spec["work_order_id"])
        require(spec["gate"] in GATES, "invalid gate")
        for key in ("author", "source_revision", "resource_revision", "source_access_scope", "effort_bound"):
            string(spec[key])
        for key in ("inputs", "skill_allowlist", "original_constraints", "stop_conditions"):
            strings(spec[key])
        strings(spec["assigned_questions"], False)
        reviewer = shape(spec["reviewer"], ["identity", "independent", "assignment_evidence", "context_evidence"])
        string(reviewer["identity"])
        require(reviewer["independent"] is True and reviewer["identity"] != spec["author"], "independent reviewer required before dispatch")
        for key in ("assignment_evidence", "context_evidence"):
            require(reviewer[key] in spec["inputs"], f"reviewer {key} must be a hashed input")
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            require(order_id not in state["orders"], "work-order ID already used")
            require(len(state["accepted"]) < 5 and spec["gate"] == GATES[len(state["accepted"])] , "gate skip or already accepted; reopen first")
            require(not self.path(f"candidates/{order_id}").exists(), "candidate directory exists before reviewer assignment")
            for name in spec["inputs"]:
                self._input_name(name)
            order = deepcopy(spec)
            order.update({"run_id": state["run_id"], "generation": state["generation"],
                          "controller": state["controller"], "assigned_at_version": expected,
                          "predecessor": state["accepted"].get(GATES[len(state["accepted"]) - 1]),
                          "policy_hash": digest(encoded(state["policy_bindings"])),
                          "input_hashes": {p: digest(read_bytes(self.path(p))) for p in spec["inputs"]},
                          "candidate_root": f"candidates/{order_id}", "seal": None})
            predecessor = self.snapshot(order["predecessor"]) if order["predecessor"] else {}
            order.update({"policy_bindings": deepcopy(state["policy_bindings"]),
                          "required_outputs": [*state["policy"]["gates"][order["gate"]]["required_outputs"],
                                               "questions.json", "decisions.json"],
                          "required_predicates": state["policy"]["gates"][order["gate"]]["predicates"],
                          "accepted_questions": predecessor.get("questions", []),
                          "accepted_decisions": predecessor.get("decisions", []),
                          "write_targets": [f"candidates/{order_id}"],
                          "required_return_schema": "shaping-runtime.v1#/definitions/review"})
            self._check_bindings(state, order)
            state["orders"][order_id] = order
            self._commit(state, expected)
            return order

    def _current_order(self, state, order_id):
        identifier(order_id)
        require(order_id in state["orders"], "unknown work order")
        order = state["orders"][order_id]
        require(order["generation"] == state["generation"], "stale generation")
        require(len(state["accepted"]) < 5 and order["gate"] == GATES[len(state["accepted"])] , "stale stage")
        predecessor = state["accepted"].get(GATES[len(state["accepted"]) - 1])
        require(order["predecessor"] == predecessor, "stale predecessor")
        self._check_bindings(state, order)
        return order

    def _files(self, order):
        root = self.path(order["candidate_root"])
        require(root.is_dir(), "candidate directory missing")
        files = {}
        for directory, dirs, names in os.walk(root, followlinks=False):
            for name in dirs:
                guarded(Path(directory) / name)
            for name in names:
                path = guarded(Path(directory) / name)
                relative = path.relative_to(root).as_posix()
                safe_relative(relative)
                data = read_bytes(path)
                files[relative] = {"sha256": digest(data), "base64": base64.b64encode(data).decode("ascii")}
        return files

    def _candidate(self, state, order):
        files = self._files(order)
        required = set(state["policy"]["gates"][order["gate"]]["required_outputs"]) | {"questions.json", "decisions.json"}
        require(required <= files.keys(), f"missing outputs: {sorted(required - files.keys())}")
        cumulative = deepcopy(self.snapshot(order["predecessor"])["files"]) if order["predecessor"] else {}
        # Earlier prose cannot silently change under a later gate.
        for name in cumulative.keys() & files.keys() - {"questions.json", "decisions.json"}:
            require(cumulative[name] == files[name], f"upstream artifact changed: {name}; reopen its stage")
        cumulative.update(files)
        questions = decode(base64.b64decode(files["questions.json"]["base64"]))
        decisions = decode(base64.b64decode(files["decisions.json"]["base64"]))
        self._registers(questions, decisions, cumulative, order, require_closed=order["gate"] in ("G2", "G3", "G4"))
        if order["predecessor"]:
            previous = self.snapshot(order["predecessor"])
            require({q["id"] for q in previous["questions"]} <= {q["id"] for q in questions}, "uncertainty IDs cannot disappear")
            old_decisions = {d["id"]: d for d in previous["decisions"]}
            new_decisions = {d["id"]: d for d in decisions}
            require(all(new_decisions.get(key) == value for key, value in old_decisions.items()), "accepted decision changed; reopen its stage")
            old_questions = {q["id"]: q for q in previous["questions"]}
            for q in questions:
                if q["id"] in old_questions:
                    require(q["blocking"] == old_questions[q["id"]]["blocking"], "cannot downgrade blocking uncertainty")
                if order["gate"] in ("G3", "G4") and q["blocking"]:
                    old = old_questions.get(q["id"], {})
                    require(all(q[key] == old.get(key) for key in ("status", "in_scope", "evidence_standard",
                                "evidence", "decision_id", "dependency_evidence")),
                            "blocking uncertainty changed after Research; reopen G2")
        return cumulative, questions, decisions

    def _registers(self, questions, decisions, files, order, require_closed):
        require(isinstance(questions, list) and isinstance(decisions, list), "registers must be JSON arrays")
        ids = set()
        decisions_by_id = {}
        inherited_inputs = self.snapshot(order["predecessor"])["input_hashes"] if order["predecessor"] else {}
        def refs(items):
            strings(items)
            require(all(p in files or p in order["input_hashes"] or p in inherited_inputs for p in items), "register evidence missing")
        for decision in decisions:
            shape(decision, ["id", "status", "authority", "reason", "evidence"], ["details"])
            if "details" in decision:
                require(isinstance(decision["details"], dict), "decision details must be an object")
            identifier(decision["id"])
            require(decision["id"] not in decisions_by_id, "duplicate decision ID")
            require(decision["status"] in ("proposed", "confirmed", "disputed"), "invalid decision status")
            string(decision["authority"])
            string(decision["reason"])
            if decision["status"] == "confirmed": refs(decision["evidence"])
            else: strings(decision["evidence"], False)
            decisions_by_id[decision["id"]] = decision
        for q in questions:
            shape(q, ["id", "blocking", "in_scope", "status", "evidence", "decision_id", "dependency_evidence", "evidence_standard"], ["details"])
            string(q["evidence_standard"])
            if "details" in q:
                require(isinstance(q["details"], dict), "question details must be an object")
            identifier(q["id"])
            require(q["id"] not in ids, "duplicate uncertainty ID")
            ids.add(q["id"])
            boolean(q["blocking"])
            boolean(q["in_scope"])
            require(q["status"] in ("proposed", "accepted-for-investigation", "answered", "disputed", "deferred", "excluded"), "invalid uncertainty status")
            strings(q["evidence"], False)
            strings(q["dependency_evidence"], False)
            if q["decision_id"] is not None: identifier(q["decision_id"])
            if q["status"] == "answered": refs(q["evidence"])
            if not q["in_scope"] or q["status"] == "excluded":
                require(not q["in_scope"] and q["status"] == "excluded", "inconsistent scope exclusion")
                decision = decisions_by_id.get(q["decision_id"], {})
                require(decision.get("status") == "confirmed", "scope exclusion needs confirmed decision")
                refs(q["dependency_evidence"])
            if require_closed and q["blocking"] and q["in_scope"]:
                require(q["status"] == "answered", "unresolved in-scope blocking uncertainty")

    def seal(self, order_id, expected):
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            order = self._current_order(state, order_id)
            files, questions, decisions = self._candidate(state, order)
            subject = {p: f["sha256"] for p, f in files.items()}
            result = {"subject": subject, "questions": questions, "decisions": decisions,
                      "work_order_id": order_id, "generation": order["generation"], "predecessor": order["predecessor"]}
            result["return_hash"] = digest(encoded(result))
            if order["seal"] is not None:
                require(order["seal"] == result, "sealed candidate changed; use new work order")
                return result
            order["seal"] = result
            self._commit(state, expected)
            return result

    def _review(self, receipt, state, order, files):
        shape(receipt, ["schema_version", "run_id", "gate", "work_order_id", "generation", "policy_hash",
                        "resource_revision", "predecessor", "return_hash", "subject", "reviewer", "authored_candidate",
                        "independence_confirmed", "evidence", "assessments", "findings", "unresolved_blockers",
                        "verdict", "next_state", "scores", "render_evidence", "targets"])
        require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1, "unsupported receipt schema")
        integer(receipt["generation"])
        for key in ("run_id", "gate", "work_order_id", "generation", "policy_hash", "resource_revision", "predecessor"):
            require(receipt[key] == order[key], f"receipt binding mismatch: {key}")
        require(receipt["reviewer"] == order["reviewer"]["identity"] and receipt["authored_candidate"] is False
                and receipt["independence_confirmed"] is True, "review_pending: independent assessment required")
        require(receipt["subject"] == order["seal"]["subject"] and receipt["return_hash"] == order["seal"]["return_hash"], "review subject mismatch")
        require(receipt["verdict"] == "pass" and receipt["next_state"] == order["gate"], "gate not passed")
        strings(receipt["findings"], False)
        require(receipt["unresolved_blockers"] == [], "unresolved blockers")
        evidence = receipt["evidence"]
        require(isinstance(evidence, dict) and evidence, "evidence inventory missing")
        for key, path in evidence.items():
            identifier(key)
            string(path)
            require(path in files, "review evidence must be in sealed subject")
        def refs(value):
            strings(value)
            require(all(key in evidence for key in value), "missing evidence ID")
        predicates = state["policy"]["gates"][order["gate"]]["predicates"]
        shape(receipt["assessments"], predicates)
        for assessment in receipt["assessments"].values():
            shape(assessment, ["outcome", "evidence_ids", "explanation"])
            require(assessment["outcome"] == "pass", "failed or unverifiable predicate")
            refs(assessment["evidence_ids"])
            string(assessment["explanation"])
        require(isinstance(receipt["targets"], list), "targets must be an array")
        if order["gate"] == "G3":
            shape(receipt["render_evidence"], DIAGRAMS)
            for evidence_ids in receipt["render_evidence"].values():
                refs(evidence_ids)
            scores = shape(receipt["scores"], ["dimensions", "team_mean", "pitch_mean", "overall"])
            shape(scores["dimensions"], TEAM + PITCH)
            for score in scores["dimensions"].values():
                shape(score, ["score", "rationale", "evidence_ids"])
                require(number(score["score"]) >= state["policy"]["scoring"]["minimum_dimension"], "dimension below threshold")
                string(score["rationale"])
                refs(score["evidence_ids"])
            team = sum(scores["dimensions"][d]["score"] for d in TEAM) / len(TEAM)
            pitch = sum(scores["dimensions"][d]["score"] for d in PITCH) / len(PITCH)
            overall = sum(scores["dimensions"][d]["score"] for d in TEAM + PITCH) / 12
            for key, calculated in (("team_mean", team), ("pitch_mean", pitch), ("overall", overall)):
                require(math.isclose(number(scores[key]), calculated, rel_tol=0, abs_tol=1e-9), f"incorrect {key}")
            require(overall >= state["policy"]["scoring"]["minimum_overall"], "overall below threshold")
        else:
            require(receipt["scores"] is None and receipt["render_evidence"] == {}, "scores/render evidence belong to G3")
        if order["gate"] == "G4":
            requested = {(t["surface"], t["destination"]) for t in state["policy"]["delivery_targets"]}
            found = set()
            for target in receipt["targets"]:
                require(isinstance(target, dict), "target review must be an object")
                identifier(target.get("operation_id"))
                operation = state["deliveries"].get(target["operation_id"], {})
                require(operation.get("bundle") == state["accepted"]["G3"] and operation.get("status") == "verified", "delivery unresolved or stale")
                roles = delivery_roles(operation["surface"])
                shape(target, ["operation_id", *roles])
                key = (operation["surface"], operation["destination"])
                require(key not in found, "duplicate delivery target")
                found.add(key)
                for role in roles:
                    refs(target[role])
                    binding = operation["record"]["evidence"][role]
                    require(digest(read_bytes(self.path(binding["path"]))) == binding["sha256"], "delivery evidence drift")
                    require(binding["sha256"] in {files[evidence[e]]["sha256"] for e in target[role]}, "target evidence does not match readback record")
            require(found == requested and bool(found), "missing required delivery targets")
        else:
            require(receipt["targets"] == [], "targets belong to G4")

    def accept(self, receipt_path, expected):
        raw = read_bytes(receipt_path)
        receipt = decode(raw)
        require(isinstance(receipt, dict), "receipt must be an object")
        order_id = identifier(receipt.get("work_order_id"))
        with self.lock():
            state = self._load()
            prior = state["accepted_orders"].get(order_id)
            if prior:
                require(prior["receipt_hash"] == digest(raw), "conflict: different receipt for accepted work order")
                require(prior["snapshot"] in state["accepted"].values(), "stale accepted result was reopened")
                return {**prior, "replayed": True}
            self._expected(state, expected)
            order = self._current_order(state, order_id)
            require(order["seal"] is not None, "candidate must be sealed before review")
            files, questions, decisions = self._candidate(state, order)
            require({p: f["sha256"] for p, f in files.items()} == order["seal"]["subject"], "candidate bytes changed after seal")
            self._review(receipt, state, order, files)
            inputs = deepcopy(self.snapshot(order["predecessor"])["input_hashes"]) if order["predecessor"] else {}
            inputs.update(order["input_hashes"])
            snapshot = {"schema_version": 1, "run_id": state["run_id"], "gate": order["gate"],
                        "generation": state["generation"], "predecessor": order["predecessor"],
                        "files": files, "questions": questions, "decisions": decisions,
                        "policy_bindings": state["policy_bindings"], "input_hashes": inputs,
                        "work_order": order, "receipt": receipt,
                        "deliveries": deepcopy(state["deliveries"]) if order["gate"] == "G4" else {},
                        "receipt_bytes": base64.b64encode(raw).decode("ascii"), "accepted_version": expected + 1}
            key = self._immutable("accepted", snapshot)
            record = {"snapshot": key, "receipt_hash": digest(raw), "accepted_version": expected + 1}
            state["accepted"][order["gate"]] = key
            state["accepted_orders"][order_id] = record
            self._commit(state, expected)
            return {**record, "replayed": False}

    def reopen(self, gate, reason, expected, policy_path=None):
        require(gate in GATES, "invalid gate")
        string(reason)
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            require(GATES.index(gate) <= len(state["accepted"]), "cannot reopen future gate")
            if policy_path is not None:
                require(gate == "G0", "policy changes require G0 reopen")
                policy, hashes, path = self._policy_binding(policy_path)
                state.update(policy=policy, policy_bindings=hashes, policy_path=path)
            removed = {g: key for g, key in state["accepted"].items() if GATES.index(g) >= GATES.index(gate)}
            state["accepted"] = {g: key for g, key in state["accepted"].items() if g not in removed}
            state["generation"] += 1
            state["reopens"].append({"gate": gate, "reason": reason, "removed": removed, "version": expected + 1})
            self._commit(state, expected)
            return {"generation": state["generation"], "invalidated": removed, "version": expected + 1}

    def delivery_intent(self, surface, destination, expected):
        string(surface)
        string(destination)
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            require("G3" in state["accepted"], "content not ready")
            self._check_bindings(state, {"input_hashes": {}, "predecessor": state["accepted"]["G3"]})
            require({"surface": surface, "destination": destination} in state["policy"]["delivery_targets"], "target not requested")
            identity = {"run_id": state["run_id"], "bundle": state["accepted"]["G3"], "surface": surface, "destination": destination}
            operation_id = digest(encoded(identity))
            if operation_id in state["deliveries"]:
                old = state["deliveries"][operation_id]
                require(old["status"] == "verified", "reconciliation_required: locate/read back existing target; do not create again")
                return {**old, "may_create": False, "replayed": True}
            # A changed bundle cannot hide an unresolved earlier external create.
            require(not any(op["surface"] == surface and op["destination"] == destination and op["status"] != "verified"
                            for op in state["deliveries"].values()), "reconciliation_required: earlier bundle has uncertain target")
            operation = {**identity, "operation_id": operation_id, "status": "pending", "record": None,
                         "record_generation": state["generation"], "history": []}
            state["deliveries"][operation_id] = operation
            self._commit(state, expected)
            return {**operation, "may_create": True, "replayed": False}

    def delivery_record(self, operation_id, record, expected):
        identifier(operation_id)
        shape(record, ["status", "note"], ["target_id", "revision", "evidence"])
        string(record["note"])
        require(record["status"] in ("uncertain", "verified"), "invalid delivery status")
        with self.lock():
            state = self._load()
            require(operation_id in state["deliveries"], "unknown delivery operation")
            operation = state["deliveries"][operation_id]
            resolved = deepcopy(record)
            if record["status"] == "verified":
                string(record.get("target_id"))
                string(record.get("revision"))
                shape(record.get("evidence"), delivery_roles(operation["surface"]))
                for role, path in record["evidence"].items():
                    self._input_name(path)
                    data = read_bytes(self.path(path))
                    if operation["surface"] == "json" and role == "readback":
                        parsed = decode(data)
                        require(isinstance(parsed, (dict, list)) and parsed, "JSON target readback must be a nonempty structured document")
                    resolved["evidence"][role] = {"path": path, "sha256": digest(data)}
            else:
                require(set(record) == {"status", "note"}, "uncertain record contains unverified fields")
            if operation["record"] == resolved:
                return {**operation, "replayed": True}
            self._expected(state, expected)
            require(operation["status"] != "verified" or ("G4" not in state["accepted"]
                    and operation["record_generation"] < state["generation"]),
                    "conflicting verified delivery; reopen G4 for new evidence")
            if operation["record"] is not None:
                operation["history"].append({"record": operation["record"], "generation": operation["record_generation"]})
            operation.update(status=record["status"], record=resolved, record_generation=state["generation"])
            self._commit(state, expected)
            return {**operation, "replayed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "init": "Initialize controller state with a pinned policy; frame/draft-only targets may be empty.",
        "status": "Verify committed state and report content/delivery separately.",
        "prepare": "Assign author/reviewer and hash inputs BEFORE worker dispatch; emit work order.",
        "seal": "Hash candidate bytes and registers BEFORE reviewer assessment; emit subject/return hash.",
        "accept": "Validate review and commit the complete immutable snapshot atomically.",
        "reopen": "Invalidate this gate and descendants, preserving history and incrementing generation.",
        "delivery-intent": "Record intent before external write; duplicate uncertain create returns hold.",
        "delivery-record": "Reconcile intent: readback/inventory plus pixels for visual targets or structured parity for json.",
    }
    for command, description in descriptions.items():
        p = sub.add_parser(command, description=description, help=description)
        p.add_argument("--run", required=True, type=Path, help="Controller-owned run directory (no symlinks)")
        if command not in ("init", "status"):
            p.add_argument("--expected-version", required=True, type=int, help="Exact state version from status")
        if command == "init":
            p.add_argument("--run-id", required=True)
            p.add_argument("--controller", required=True, help="Host-attested label; not authentication")
            p.add_argument("--policy", required=True, type=Path, help="Policy JSON inside run root")
        if command == "prepare": p.add_argument("--spec", required=True, type=Path)
        if command == "seal": p.add_argument("--work-order", required=True)
        if command == "accept": p.add_argument("--receipt", required=True, type=Path)
        if command == "reopen":
            p.add_argument("--gate", choices=GATES, required=True)
            p.add_argument("--reason", required=True)
            p.add_argument("--policy", type=Path, help="Optional replacement policy; requires G0 reopen")
        if command == "delivery-intent":
            p.add_argument("--surface", required=True)
            p.add_argument("--destination", required=True)
        if command == "delivery-record":
            p.add_argument("--operation", required=True)
            p.add_argument("--record", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        rt = Runtime(args.run)
        if args.command == "init": result = rt.init(args.run_id, args.controller, args.policy)
        elif args.command == "status": result = rt.status()
        elif args.command == "prepare": result = rt.prepare(decode(read_bytes(args.spec)), args.expected_version)
        elif args.command == "seal": result = rt.seal(args.work_order, args.expected_version)
        elif args.command == "accept": result = rt.accept(args.receipt, args.expected_version)
        elif args.command == "reopen": result = rt.reopen(args.gate, args.reason, args.expected_version, args.policy)
        elif args.command == "delivery-intent": result = rt.delivery_intent(args.surface, args.destination, args.expected_version)
        else: result = rt.delivery_record(args.operation, decode(read_bytes(args.record)), args.expected_version)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except Hold as exc:
        print(json.dumps({"status": "hold", "reason": str(exc)}))
        return 2
    except (Recovery, OSError) as exc:
        print(json.dumps({"status": "recovery_pending" if isinstance(exc, Recovery) else "error", "reason": str(exc)}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
