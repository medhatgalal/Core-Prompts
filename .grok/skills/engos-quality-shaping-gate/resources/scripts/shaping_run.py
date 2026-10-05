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
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
from urllib.parse import quote, unquote


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


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp(value):
    string(value)
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "expected UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Hold("invalid timestamp") from exc


def progress_link(path):
    """Only run-relative references; never turn destination labels into URLs."""
    safe_relative(path)
    require(not any(c in path for c in "%?#") and not any(ord(c) < 32 or ord(c) == 127 for c in path),
            "unsafe progress link")
    return quote(path, safe="/")


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


def line_span(data, locator):
    """Validate canonical 1-based N:M locators and return exact retained UTF-8 line bytes."""
    string(locator)
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", locator)
    require(match is not None, "locator must use canonical N:M line-range form")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Hold("opened source must be valid UTF-8") from exc
    lines = data.splitlines(keepends=True)
    first, last = map(int, match.groups())
    require(first <= last <= len(lines), f"locator {locator} is outside retained source line bounds")
    return tuple(lines[first - 1:last])


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
    shape(policy, ["schema_version", "policy_id", "gates", "scoring", "delivery_targets", "references"],
          ["shaping_loop", "review_evidence"])
    require(type(policy["schema_version"]) is int and policy["schema_version"] == 1, "unsupported policy schema")
    string(policy["policy_id"])
    if "shaping_loop" in policy:
        boolean(policy["shaping_loop"])
    if policy["policy_id"] == "shaping-gates.v3+rubric.v4":
        require(policy.get("shaping_loop") is True,
                "shaping-gates.v3+rubric.v4 requires shaping_loop=true")
    if "review_evidence" in policy:
        boolean(policy["review_evidence"])
    if policy.get("review_evidence"):
        require(policy["policy_id"] != "shaping-gates.v3+rubric.v4", "review evidence requires new policy ID")
    if policy["policy_id"] == "shaping-gates.v4+rubric.v4":
        require(policy.get("review_evidence") is True and policy.get("shaping_loop") is True, "current profile requires review evidence and shaping loop")
    shape(policy["gates"], GATES)
    for i, gate in enumerate(GATES):
        entry = shape(policy["gates"][gate], ["predicates", "required_outputs"])
        strings(entry["predicates"])
        strings(entry["required_outputs"])
        require(set(PREDICATES[gate]) <= set(entry["predicates"]), f"missing mandatory {gate} predicates")
        require(set(MIN_OUTPUTS[i]) <= set(entry["required_outputs"]), f"missing mandatory {gate} outputs")
        for name in entry["required_outputs"]:
            safe_relative(name)
    if policy.get("shaping_loop", False):
        require("research-coverage.json" in policy["gates"]["G2"]["required_outputs"],
                "shaping loop requires G2 research-coverage.json")
        require("shape-set.json" in policy["gates"]["G3"]["required_outputs"],
                "shaping loop requires G3 shape-set.json")
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


def validate_review_png(raw):
    """Decode bounded noninterlaced 8-bit PNG scanlines; other profiles hold.

    This deliberately narrow stdlib decoder avoids optional runner dependencies.
    Pixel variation is only a blank-image guard, never semantic visual judgment.
    """
    import struct
    import zlib
    require(raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) <= 20_000_000, 'invalid PNG')
    offset, chunks, compressed, header = 8, [], bytearray(), None
    while offset < len(raw):
        require(offset + 12 <= len(raw), 'truncated PNG')
        length = struct.unpack('>I', raw[offset:offset+4])[0]
        tag = raw[offset+4:offset+8]
        end = offset + 12 + length
        require(end <= len(raw), 'truncated PNG')
        data = raw[offset+8:end-4]
        require(zlib.crc32(tag + data) & 0xffffffff == struct.unpack('>I', raw[end-4:end])[0], 'PNG checksum')
        chunks.append(tag)
        if tag == b'IHDR':
            require(len(chunks) == 1 and length == 13, 'PNG header')
            header = struct.unpack('>IIBBBBB', data)
        elif tag == b'IDAT': compressed.extend(data)
        elif tag == b'IEND':
            require(length == 0 and end == len(raw), 'PNG trailing bytes')
            break
        else:
            require(tag[0] & 32 or tag == b'PLTE', 'unsupported PNG critical chunk')
        offset = end
    require(header and chunks[-1:] == [b'IEND'] and compressed, 'incomplete PNG')
    width, height, depth, color, compression, filtering, interlace = header
    require(0 < width * height <= 4_000_000 and width > 1 and height > 1, 'PNG dimensions')
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color)
    require(channels and depth == 8 and compression == filtering == interlace == 0, 'unsupported PNG profile')
    expected = height * (1 + width * channels)
    try:
        decoder = zlib.decompressobj()
        scanlines = decoder.decompress(bytes(compressed), expected + 1)
    except zlib.error as exc:
        raise Hold('PNG decode failure') from exc
    require(len(scanlines) == expected and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail, 'PNG decoded length')
    stride, previous, pixels = width * channels, [0] * (width * channels), set()
    for row in range(height):
        start = row * (stride + 1)
        kind = scanlines[start]
        require(kind <= 4, 'PNG filter')
        values = list(scanlines[start+1:start+1+stride])
        for index in range(stride):
            left = values[index-channels] if index >= channels else 0
            up = previous[index]
            corner = previous[index-channels] if index >= channels else 0
            if kind == 1: predictor = left
            elif kind == 2: predictor = up
            elif kind == 3: predictor = (left + up) // 2
            elif kind == 4:
                candidate = left + up - corner
                distances = [abs(candidate - v) for v in (left, up, corner)]
                predictor = (left, up, corner)[distances.index(min(distances))]
            else: predictor = 0
            values[index] = (values[index] + predictor) & 255
        for index in range(0, stride, channels):
            pixel = tuple(values[index:index+channels])
            alpha = pixel[-1] if color in (4, 6) else 255
            if alpha: pixels.add(pixel)
        previous = values
    require(len(pixels) > 1, 'blank PNG')
    return width, height


def validate_review_svg(raw):
    """Same passive SVG contract as artifact_export; host supplies rendered PNG.

    No renderer or normalization is introduced here. Renderer animation CSS
    must first follow the existing exporter normalization path.
    """
    import xml.etree.ElementTree as ET
    try: text = raw.decode('utf-8-sig')
    except UnicodeError as exc: raise Hold('SVG must be UTF-8') from exc
    require(len(raw) <= 20_000_000 and '\x00' not in text and not re.search(r'<!DOCTYPE|<!ENTITY|<\?', text, re.I), 'unsafe SVG declaration')
    try: root = ET.fromstring(text)
    except ET.ParseError as exc: raise Hold('invalid SVG') from exc
    namespace = '{http://www.w3.org/2000/svg}'
    tags = {'svg', 'g', 'defs', 'marker', 'path', 'rect', 'line', 'polyline', 'polygon',
            'circle', 'ellipse', 'text', 'tspan', 'title', 'desc', 'style', 'clipPath',
            'linearGradient', 'radialGradient', 'stop', 'use', 'symbol', 'filter', 'feDropShadow'}
    ids, references = set(), []
    def passive_css(value):
        require(not re.search(r'[\\@<]|/\*|expression\s*\(|(?:https?|file|data|javascript)\s*:|(?:-webkit-)?image(?:-set)?\s*\(|\banimation(?:-[\w-]+)?\s*:', value, re.I), 'unsafe SVG CSS')
        without_local = re.sub(r'url\(\s*[\'"]?#[A-Za-z_][\w:.-]*[\'"]?\s*\)', '', value, flags=re.I)
        require(not re.search(r'url\s*\(', without_local, re.I), 'external SVG resource')
    for element in root.iter():
        require(element.tag in {namespace + tag for tag in tags}, 'unsafe SVG element')
        if element.tag == namespace + 'style':
            require(not len(element), 'SVG style child element')
            passive_css(element.text or '')
        for attribute, value in element.attrib.items():
            require(not attribute.startswith('{') or attribute in ('{http://www.w3.org/1999/xlink}href', '{http://www.w3.org/XML/1998/namespace}space'), 'unsafe SVG attribute namespace')
            local = attribute.rsplit('}', 1)[-1].lower()
            require(not local.startswith('on') and local not in ('src', 'srcset', 'base', 'tabindex'), 'unsafe SVG attribute')
            if local == 'href':
                require(re.fullmatch(r'#[A-Za-z_][\w:.-]*', value), 'external SVG reference')
                references.append(value[1:])
            elif local == 'id':
                require(value not in ids, 'duplicate SVG ID'); ids.add(value)
            else: passive_css(value)
    require(root.tag == namespace + 'svg' and all(ref in ids for ref in references), 'invalid SVG root/local reference')
    try:
        if 'viewBox' in root.attrib:
            box = [float(value) for value in re.split(r'[\s,]+', root.attrib['viewBox'].strip())]
            require(len(box) == 4 and all(math.isfinite(value) for value in box), 'SVG viewBox')
            dimensions = box[2:]
        else: dimensions = [float(re.sub(r'px$', '', root.attrib[key])) for key in ('width', 'height')]
        require(all(math.isfinite(value) and 0 < value <= 100000 for value in dimensions), 'SVG dimensions')
    except (KeyError, ValueError) as exc: raise Hold('SVG needs finite positive dimensions') from exc
    require(any(element.tag in {namespace+tag for tag in ('path', 'rect', 'line', 'text', 'circle', 'polyline', 'polygon', 'use')} for element in root.iter()), 'blank SVG')
    return dimensions


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

    def _observation_evidence(self, path):
        self._input_name(path)
        progress_link(path)
        return {"path": path, "sha256": digest(read_bytes(self.path(path)))}

    def progress_context(self, spec, expected):
        """Controller attribution and requested scope, not authority to advance gates."""
        shape(spec, ["name", "evidence_mode", "requested_stop", "observed_at", "evidence", "investment_appetite"])
        string(spec["name"])
        string(spec["investment_appetite"])
        require(spec["evidence_mode"] in ("real", "simulated"), "invalid evidence mode")
        require(spec["requested_stop"] in GATES, "invalid requested stopping point")
        require(timestamp(spec["observed_at"]) <= timestamp(utc_now()), "future observation")
        with self.lock():
            state = self._load()
            evidence = self._observation_evidence(spec["evidence"])
            prior = state.get("progress_context")
            if prior and prior["spec"] == spec and prior["provenance"] == evidence:
                return {**prior, "replayed": True}
            self._expected(state, expected)
            if prior:
                require(prior["spec"]["evidence_mode"] == spec["evidence_mode"], "cannot relabel run evidence mode")
            record = {"spec": deepcopy(spec), "provenance": evidence,
                      "recorded_version": expected + 1, "controller": state["controller"]}
            state["progress_context"] = record
            self._commit(state, expected)
            return {**record, "replayed": False}

    def observe(self, record, expected):
        """Append a host observation to the sole controller journal; never accept."""
        shape(record, ["event_id", "run_id", "version", "generation", "work_order_id", "kind",
                       "observed_at", "actor", "evidence"],
              ["hold_type", "reason", "needed", "respondent", "next_action", "resolves",
               "operation_id", "result", "target_revision"])
        identifier(record["event_id"])
        integer(record["version"])
        integer(record["generation"])
        kinds = {"dispatched", "started", "candidate_returned", "review_requested", "review_returned",
                 "held", "released", "stopped", "accepted", "reopened", "delivery_result"}
        require(record["kind"] in kinds, "invalid observation kind")
        optional = {"hold_type", "reason", "needed", "respondent", "next_action", "resolves",
                    "operation_id", "result", "target_revision"}
        allowed = {"held": {"hold_type", "reason", "needed", "respondent", "next_action"},
                   "released": {"resolves"}, "delivery_result": {"operation_id", "result", "target_revision"}}
        require(set(record) & optional <= allowed.get(record["kind"], set()), "fields not applicable to observation kind")
        require(timestamp(record["observed_at"]) <= timestamp(utc_now()), "future observation")
        with self.lock():
            state = self._load()
            require(record["run_id"] == state["run_id"] and record["generation"] == state["generation"],
                    "observation run/generation mismatch")
            evidence = self._observation_evidence(record["evidence"])
            events = state.setdefault("observations", [])
            for prior in events:
                if prior["record"]["event_id"] == record["event_id"]:
                    require(prior["record"] == record and prior["provenance"] == evidence, "observation ID conflict")
                    return {**prior, "replayed": True}
            self._expected(state, expected)
            require(record["version"] == expected, "observation version mismatch")
            order = state["orders"].get(record["work_order_id"])
            require(order is not None, "unknown observed work order")
            kind = record["kind"]
            accepted = state["accepted_orders"].get(record["work_order_id"], {}).get("snapshot")
            if kind == "reopened":
                require(state["reopens"] and accepted in state["reopens"][-1]["removed"].values(),
                        "reopen observation lacks invalidated acceptance")
            else:
                require(order["generation"] == state["generation"], "stale observed attempt")
                if accepted in state["accepted"].values():
                    require(kind in ("accepted", "stopped", "delivery_result"), "late observation after acceptance")
                    self._check_bindings(state, order)
                else:
                    self._current_order(state, order["work_order_id"])
                    require(kind != "accepted", "observation cannot grant acceptance")
            require(record["actor"] in (order["author"], order["reviewer"]["identity"], state["controller"]),
                    "actor has no controller assignment")
            if kind in ("review_requested", "review_returned", "candidate_returned"):
                require(order["seal"] is not None, "observation needs sealed subject")
                files, _, _ = self._candidate(state, order)
                require({p: f["sha256"] for p, f in files.items()} == order["seal"]["subject"], "sealed subject drift")
            entry = {"record": deepcopy(record), "provenance": evidence, "recorded_version": expected + 1,
                     "gate": order["gate"], "return_hash": order["seal"]["return_hash"] if order["seal"] else None}
            if kind == "review_returned":
                require(record["actor"] == order["reviewer"]["identity"], "review actor mismatch")
                review = decode(read_bytes(self.path(record["evidence"])))
                self._review(review, state, order, files, acceptance=False)
                entry["review"] = review
            if kind == "held":
                require(record.get("hold_type") in ("prerequisite", "decision"), "invalid hold type")
                for key in ("reason", "needed", "next_action"): string(record.get(key))
                require("respondent" in record, "respondent required; null means unassigned")
                if record["respondent"] is not None: string(record["respondent"])
            elif kind == "released":
                require(record["actor"] == state["controller"], "only controller records hold resolution")
                strings(record.get("resolves"))
                held = {e["record"]["event_id"] for e in events if e["record"]["kind"] == "held"
                        and e["record"]["work_order_id"] == record["work_order_id"]}
                require(set(record["resolves"]) <= held, "unknown hold resolution")
            else:
                require(not (set(record) & {"hold_type", "reason", "needed", "respondent", "next_action", "resolves"}),
                        "fields not applicable to observation kind")
            previous = [e for e in events if e["record"]["work_order_id"] == record["work_order_id"]]
            require(not previous or record["observed_at"] >= previous[-1]["record"]["observed_at"], "out-of-order observation")
            if kind == "delivery_result":
                require(order["gate"] == "G4" and state["deliveries"], "delivery result lacks recorded operation")
                operation = state["deliveries"].get(record.get("operation_id"))
                require(operation and operation["bundle"] == state["accepted"].get("G3"), "unknown/stale observed operation")
                require(record.get("result") in ("changed", "failed", "unchanged"), "invalid target observation result")
                string(record.get("target_revision"))
                if record["result"] == "unchanged":
                    require(operation["status"] == "verified" and operation["record"]["revision"] == record["target_revision"],
                            "unchanged observation must match verified target revision")
                entry["operation_record_hash"] = digest(encoded(operation["record"]))
            else:
                require(not (set(record) & {"operation_id", "result", "target_revision"}), "target fields require delivery_result")
            events.append(entry)
            self._commit(state, expected)
            return {**entry, "replayed": False}

    def progress(self, as_of=None, activity_max_age_seconds=900):
        """Deterministic projection at one committed revision and explicit as-of time."""
        as_of = as_of or utc_now()
        timestamp(as_of)
        integer(activity_max_age_seconds, 1)
        try:
            state = self._load()
            return self._progress(state, as_of, activity_max_age_seconds)
        except (Recovery, Hold, OSError, KeyError, TypeError, AttributeError, IndexError, binascii.Error) as exc:
            return {"schema_version": "shaping-progress.v1", "status": "unverifiable", "snapshot_at": as_of,
                    "reason": str(exc), "verified_count": 0, "applicable_count": None,
                    "requested_complete": False, "gates": [{"gate": g, "state": "unverifiable"} for g in GATES]}

    def _progress(self, state, as_of, max_age):
        # Never call status()/policy() here: those would reload a possibly newer pointer.
        context = state.get("progress_context")
        spec = context["spec"] if context else {}
        context_drift = self._binding_drift([{context["provenance"]["path"]: context["provenance"]["sha256"]}]) if context else []
        stop = spec.get("requested_stop")
        require(stop is None or stop in GATES, "invalid stored stopping point")
        policy_drift = self._binding_drift([state["policy_bindings"]])
        history = {}
        for record in sorted(state["accepted_orders"].values(), key=lambda r: r["accepted_version"]):
            snap = self.snapshot(record["snapshot"])
            history[snap["gate"]] = (record["snapshot"], snap)
        accepted = {}
        for gate, (key, snap) in history.items():
            drift = self._binding_drift([state["policy_bindings"], snap["policy_bindings"], snap["input_hashes"]])
            accepted[gate] = {"snapshot": key, "href": progress_link(f"accepted/{key}.json"),
                              "accepted_version": snap["accepted_version"], "source_revision": snap["work_order"]["source_revision"],
                              "state": "verified" if state["accepted"].get(gate) == key and not drift else "stale",
                              "drift": drift, "gate": gate, "accepted_at": snap.get("accepted_at")}
        events, invalid = [], []
        # Committed negative knowledge survives evidence drift and unrelated
        # generation changes. Only activity/positive freshness uses current events.
        knowledge = state.get("observations", [])
        valid_observations = set()
        for event in knowledge:
            record = event["record"]
            order = state["orders"].get(record["work_order_id"])
            require(order is not None and record["run_id"] == state["run_id"], "invalid stored observation binding")
            drift = self._binding_drift([{event["provenance"]["path"]: event["provenance"]["sha256"]}])
            if drift or timestamp(record["observed_at"]) > timestamp(as_of):
                invalid.append({"event_id": record["event_id"], "reason": "evidence drift" if drift else "observation after snapshot time",
                                "work_order_id": record["work_order_id"]})
                continue
            valid_observations.add(record["event_id"])
            if record["generation"] == state["generation"]:
                events.append(event)
        targets = []
        for target in state["policy"]["delivery_targets"]:
            operations = [op for op in state["deliveries"].values()
                          if op["surface"] == target["surface"] and op["destination"] == target["destination"]]
            current = [op for op in operations if op["bundle"] == state["accepted"].get("G3")]
            operation = current[-1] if current else (operations[-1] if operations else {})
            record = operation.get("record") or {}
            bindings = {e["path"]: e["sha256"] for e in record.get("evidence", {}).values()}
            drift = self._binding_drift([bindings])
            source_stale = bool(operation) and (not current or accepted.get("G3", {}).get("state") != "verified")
            local = "stale" if drift or source_stale else ("verified" if record.get("status") == "verified" else "unknown")
            observations = [e for e in knowledge if e["record"]["kind"] == "delivery_result"
                            and e["record"].get("operation_id") == operation.get("operation_id")]
            observed, unresolved = {}, []
            for event in observations:
                observation = event["record"]
                if observation["result"] in ("changed", "failed"):
                    # Only a later, intact, timestamped reconciliation can retire
                    # this negative. Changing a hash or generation is not repair.
                    reconciled = (local == "verified" and operation.get("recorded_version", -1) > event["recorded_version"]
                                  and record.get("observed_at", "") >= observation["observed_at"])
                    if not reconciled:
                        unresolved.append(event)
                elif (observation["event_id"] in valid_observations
                      and event["operation_record_hash"] == digest(encoded(operation.get("record")))
                      and local == "verified"):
                    unresolved = [prior for prior in unresolved
                                  if prior["record"]["observed_at"] > observation["observed_at"]]
                    observed = observation
            if unresolved:
                # Changed target bytes outrank a later failed access/read attempt.
                observed = next((e["record"] for e in reversed(unresolved) if e["record"]["result"] == "changed"),
                                unresolved[-1]["record"])
            remote = observed.get("result", "unknown")
            if remote == "unchanged":
                remote = "observed_unchanged" if (timestamp(as_of) - timestamp(observed["observed_at"])).total_seconds() <= max_age else "stale_observation"
            targets.append({**target, "local_integrity": local, "source_stale": source_stale, "drift": drift,
                            "placement": operation.get("status", "not_reached"), "target_revision": record.get("revision"),
                            "last_read_at": observed.get("observed_at", record.get("observed_at")), "remote_freshness": remote,
                            "observed_target_revision": observed.get("target_revision"),
                            "unresolved_observations": [e["record"]["event_id"] for e in unresolved],
                            "observation_integrity": ("verified" if observed.get("event_id") in valid_observations else "stale") if observed else "unknown",
                            "note": record.get("note"), "evidence": record.get("evidence", {}),
                            "next_action": "Reconcile saved target and obtain fresh readback" if local != "verified" or unresolved
                            else "Read back target again to establish remote freshness"})
        if "G4" in accepted and any(t["local_integrity"] == "stale" for t in targets):
            accepted["G4"]["state"] = "stale"
        gate_rows, drafts = [], []
        for i, gate in enumerate(GATES):
            orders = sorted([o for o in state["orders"].values() if o["gate"] == gate
                             and o["generation"] == state["generation"] and o["work_order_id"] not in state["accepted_orders"]],
                            key=lambda o: (o["assigned_at_version"], o["work_order_id"]))
            # Multiple outstanding attempts remain explicit. Never infer a winning draft.
            candidates = [self._progress_candidate(state, o, events, invalid, as_of, max_age, knowledge) for o in orders]
            drafts.extend(candidates)
            accepted_gate = accepted.get(gate)
            review_conflict = False
            review_issues = []
            if accepted_gate and accepted_gate["state"] == "verified":
                receipt = history[gate][1]["receipt"]
                order = history[gate][1]["work_order"]
                for event in knowledge:
                    review = event.get("review")
                    if not review or review["return_hash"] != receipt["return_hash"]: continue
                    failure = self._progress_review_failure(state, order, review)
                    if failure or self._progress_review_signature(review) != self._progress_review_signature(receipt):
                        review_issues.append({"event_id": event["record"]["event_id"],
                                              "reason": failure or "conflicting acceptance assessments",
                                              "evidence_integrity": "verified" if event["record"]["event_id"] in valid_observations else "stale"})
                review_conflict = bool(review_issues)
            upstream_stale = any(a["state"] == "stale" for g, a in accepted.items() if GATES.index(g) <= i)
            if policy_drift or (upstream_stale and gate not in state["accepted"]):
                gate_state = "stale"
            elif accepted_gate and accepted_gate["state"] == "verified":
                gate_state = "verified"
            elif candidates:
                gate_state = candidates[-1]["state"] if len(candidates) == 1 else "blocked"
            elif accepted_gate:
                gate_state = "stale"
            else:
                gate_state = "not_reached"
            predecessor = self.snapshot(state["accepted"][GATES[i - 1]]) if i and GATES[i - 1] in state["accepted"] else {}
            # A validated sealed candidate has the pending register for this
            # attempt. Do not re-add questions it answered from accepted history.
            inherited_holds = self._progress_questions(predecessor.get("questions", [])) if gate not in state["accepted"] and not candidates else []
            if inherited_holds and gate_state in ("not_reached", "queued", "last_observed_active", "review_pending"):
                gate_state = "awaiting_input"
            if gate == "G4" and gate_state != "stale":
                if any(t["remote_freshness"] == "changed" or t["local_integrity"] == "stale" for t in targets): gate_state = "stale"
                elif any(t["remote_freshness"] == "failed" or t["placement"] == "uncertain" for t in targets): gate_state = "blocked"
            if review_conflict and gate_state != "stale": gate_state = "blocked"
            row = {"gate": gate, "name": ["Intake", "Framed", "Research", "Shaped", "Bet-ready"][i],
                   "applicable": None if stop is None else i <= GATES.index(stop),
                   "state": gate_state, "accepted": accepted_gate, "candidates": candidates,
                   "review_conflict": review_conflict, "review_issues": review_issues, "blockers": inherited_holds}
            if row["applicable"] is False: row["state"] = "outside_scope"
            gate_rows.append(row)
        latest = max(accepted.values(), key=lambda a: a["accepted_version"], default=None)
        draft = max(drafts, key=lambda d: d["assigned_at_version"], default=None)
        applicable = [g for g in gate_rows if g["applicable"] is not False]
        summaries = self._progress_summaries(gate_rows, stop, bool(context) and not context_drift)
        current_gate = next((g for g in applicable if g["state"] != "verified"), None)
        current = {"gate": current_gate["gate"] if current_gate else None, "actor": None, "role": None,
                   "label": current_gate["gate"] if current_gate else
                       "requested finish" if summaries["requested_complete"] is True else "context revalidation",
                   "assignment": None, "blockers": [], "next_action": "Requested stopping point reached"
                       if summaries["requested_complete"] is True else "Revalidate requested stopping point and evidence provenance"}
        if current_gate:
            candidates = current_gate["candidates"]
            if len(candidates) == 1:
                current.update({k: candidates[0][k] for k in ("actor", "role", "assignment", "blockers", "next_action")})
            elif candidates:
                current["next_action"] = "Resolve concurrent candidate attempts; no attempt selected"
            elif current_gate["state"] == "stale":
                current["next_action"] = "Refresh changed dependencies and reopen the earliest affected gate"
            else:
                current["next_action"] = "Assign the next gate after confirming required inputs"
            if current_gate["blockers"]:
                current["blockers"].extend(current_gate["blockers"])
                if current_gate["state"] == "awaiting_input": current["next_action"] = current_gate["blockers"][0]["next_action"]
            if current_gate["review_conflict"]: current["next_action"] = "Resolve conflicting assessments of the accepted subject"
            if current_gate["gate"] == "G4" and current_gate["state"] in ("blocked", "stale"):
                current["next_action"] = "Reconcile changed or failed target and obtain fresh readback; retain unchanged content approval"
        active_orders = {d["work_order_id"] for d in drafts if d["gate"] not in state["accepted"]}
        # Select the latest committed event BEFORE checking evidence. Dropping an
        # invalid terminal/hold would resurrect an older started observation.
        activity_events = [e for e in knowledge if e["record"]["kind"] in ("started", "dispatched", "stopped", "candidate_returned", "review_requested", "review_returned", "held", "released")
                           and e["record"]["generation"] == state["generation"]
                           and state["orders"][e["record"]["work_order_id"]]["generation"] == state["generation"]
                           and (e["record"]["work_order_id"] in active_orders or
                                (not active_orders and e["record"]["kind"] == "stopped"))]
        last = max(activity_events, key=lambda e: e["recorded_version"], default=None)
        activity = {"state": "unknown", "observed_at": None, "actor": None, "max_age_seconds": max_age}
        if last:
            record = last["record"]
            age = (timestamp(as_of) - timestamp(record["observed_at"])).total_seconds()
            evidence_current = record["event_id"] in valid_observations and not self._binding_drift(
                [state["orders"][record["work_order_id"]]["input_hashes"], state["policy_bindings"]])
            activity.update(state="unknown" if not evidence_current else
                            "stopped" if record["kind"] == "stopped" else "stale" if age > max_age else
                            "last_observed_active" if record["kind"] == "started" else record["kind"],
                            observed_at=record["observed_at"], actor=record["actor"] if evidence_current else None,
                            work_order_id=record["work_order_id"], last_recorded_kind=record["kind"],
                            evidence_integrity="verified" if evidence_current else "unverifiable")
        latest_snap = history[latest["gate"]][1] if latest else {}
        questions, decisions = latest_snap.get("questions", []), latest_snap.get("decisions", [])
        return {"schema_version": "shaping-progress.v1", "status": "projected", "snapshot_at": as_of,
                "run_id": state["run_id"], "name": spec.get("name", state["run_id"]),
                "version": state["version"], "generation": state["generation"], "revision": digest(encoded(state)),
                "evidence": {"mode": spec.get("evidence_mode", "unknown") if not context_drift else "unknown",
                             "provenance": context["provenance"] if context else None, "drift": context_drift,
                             "observed_at": spec.get("observed_at")},
                "requested_stop": stop, **summaries,
                "local_integrity": "verified", "remote_freshness": "unknown", "policy_drift": policy_drift,
                "gates": gate_rows, "current": current, "activity": activity, "latest_accepted": latest,
                "latest_draft": draft, "targets": targets, "observations": state.get("observations", []),
                "invalid_observations": invalid, "investment_appetite": spec.get("investment_appetite", "unknown"),
                "warnings": ["Record current requested stopping point and evidence provenance"] if not context or context_drift else [],
                "checkpoint_effort": draft["effort_bound"] if draft else "unknown",
                "registers": {"source_snapshot": latest["snapshot"] if latest else None,
                              "state": latest["state"] if latest else "unknown",
                              "questions": questions, "decisions": decisions,
                              "answered": sum(q["status"] == "answered" for q in questions),
                              "blocking": sum(q["blocking"] and q["in_scope"] and q["status"] != "answered" for q in questions),
                              "confirmed": sum(d["status"] == "confirmed" for d in decisions)}}

    @staticmethod
    def _progress_summaries(gates, stop, context_valid):
        """Readiness summaries share one authority: projected gates and context.

        Accepted snapshots remain historical evidence, not a second summary input.
        Diagram readiness is conservatively bounded by the whole G3 gate; detailed
        predicate receipts remain available in the accepted/observation history.
        """
        applicable = [g for g in gates if g["applicable"] is not False]
        verified = sum(g["state"] == "verified" for g in applicable)
        shaped = next(g["state"] for g in gates if g["gate"] == "G3")
        if shaped == "verified" and not context_valid: shaped = "unknown"
        return {"requested_complete": None if stop is None else bool(context_valid and verified == len(applicable)),
                "verified_count": verified, "applicable_count": len(applicable) if stop else None,
                "content_review": shaped,
                "visual_review": {"local_diagrams": shaped, "document_presentation": "unknown"}}

    def _progress_candidate(self, state, order, events, invalid, as_of, max_age, knowledge):
        self.path(order["candidate_root"])
        drift = self._binding_drift([state["policy_bindings"], order["policy_bindings"], order["input_hashes"]])
        if order["predecessor"]:
            drift += self._binding_drift([self.snapshot(order["predecessor"])["input_hashes"]])
        subject_error = None
        if order["seal"]:
            try:
                files, _, _ = self._candidate(state, order)
                require({p: f["sha256"] for p, f in files.items()} == order["seal"]["subject"], "sealed candidate changed")
            except (Hold, OSError) as exc:
                subject_error = str(exc)
        selected = [e for e in events if e["record"]["work_order_id"] == order["work_order_id"]]
        resolved = {item for e in selected for item in e["record"].get("resolves", [])}
        holds = [e["record"] for e in selected if e["record"]["kind"] == "held" and e["record"]["event_id"] not in resolved]
        holds += self._progress_questions(order["seal"]["questions"] if order["seal"] else order["accepted_questions"])
        reviews = [e["review"] for e in knowledge if "review" in e and e["record"]["work_order_id"] == order["work_order_id"]]
        verdicts = {r["verdict"] for r in reviews}
        conflict = len({encoded(self._progress_review_signature(r)) for r in reviews}) > 1
        review_issues = [issue for r in reviews if (issue := self._progress_review_failure(state, order, r))]
        failed = bool(review_issues)
        unverifiable = "unverifiable" in verdicts or any(a["outcome"] == "unverifiable" for r in reviews for a in r["assessments"].values())
        state_name, action = "queued", "Dispatch assigned work and record a host observation"
        last = selected[-1]["record"] if selected else None
        if last and last["kind"] == "started" and (timestamp(as_of) - timestamp(last["observed_at"])).total_seconds() <= max_age:
            state_name, action = "last_observed_active", "Await a candidate return or a new host observation"
        if order["seal"]: state_name, action = "review_pending", "Obtain independent review of the sealed subject"
        if holds:
            prerequisite = [h for h in holds if h["hold_type"] == "prerequisite"]
            hold = (prerequisite or holds)[0]
            state_name, action = ("blocked" if prerequisite else "awaiting_input"), hold["next_action"]
        if unverifiable: state_name, action = "blocked", "Resolve unverifiable review evidence"
        if failed and not unverifiable: state_name, action = "changes_requested", "Repair candidate in a fresh work order and obtain review"
        if conflict: state_name, action = "blocked", "Resolve conflicting assessments of the same subject"
        if drift or subject_error or any(e["work_order_id"] == order["work_order_id"] for e in invalid):
            state_name, action = "stale", "Refresh evidence and reopen the affected gate or prepare a new candidate"
        reviewer = state_name == "review_pending"
        return {"gate": order["gate"], "state": state_name, "work_order_id": order["work_order_id"],
                "assigned_at_version": order["assigned_at_version"], "generation": order["generation"],
                "href": progress_link(order["candidate_root"]), "source_revision": order["source_revision"],
                "return_hash": order["seal"]["return_hash"] if order["seal"] else None,
                "actor": order["reviewer"]["identity"] if reviewer else order["author"],
                "role": "reviewer" if reviewer else "author", "assignment": {
                    "work_order_id": order["work_order_id"], "controller": order["controller"],
                    "version": order["assigned_at_version"], "evidence": order["reviewer"]["assignment_evidence"]},
                "blockers": holds, "next_action": action, "drift": sorted(set(drift)),
                "subject_error": subject_error, "review_issues": review_issues, "effort_bound": order["effort_bound"]}

    def _progress_review_failure(self, state, order, review):
        """Use the gate's acceptance checks, including scores, blockers and targets."""
        files = order["seal"].get("review_files") or {name: {"sha256": sha} for name, sha in order["seal"]["subject"].items()}
        try:
            self._review(review, state, order, files)
        except (Hold, OSError) as exc:
            return str(exc)
        return None

    @staticmethod
    def _progress_review_signature(review):
        # Narrative/evidence wording can differ without conflicting outcomes.
        return {"verdict": review["verdict"], "outcomes": {key: a["outcome"] for key, a in review["assessments"].items()},
                "scores": {key: score["score"] for key, score in (review["scores"] or {}).get("dimensions", {}).items()},
                "unresolved_blockers": sorted(review["unresolved_blockers"])}

    @staticmethod
    def _progress_questions(questions):
        result = []
        for question in questions:
            if not question["blocking"] or not question["in_scope"] or question["status"] == "answered": continue
            details = question.get("details", {})
            respondent = details.get("respondent")
            if respondent == "owner_unassigned": respondent = None
            result.append({"id": question["id"], "hold_type": "decision", "reason": "Unanswered required uncertainty",
                           "needed": details.get("question", question["evidence_standard"]), "respondent": respondent,
                           "next_action": "Obtain an evidenced answer to " + question["id"], "evidence": question["evidence"]})
        return result

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
                     "source_access_scope", "effort_bound", "stop_conditions"], ["shape_basis", "participation_evidence", "accepted_proof", "seam_applicability"])
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
        retry_new_facts = []
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            require(order_id not in state["orders"], "work-order ID already used")
            require(len(state["accepted"]) < 5 and spec["gate"] == GATES[len(state["accepted"])] , "gate skip or already accepted; reopen first")
            if spec["gate"] == "G3" and state["policy"].get("shaping_loop", False):
                require("shape_basis" in spec and isinstance(spec["shape_basis"], list),
                        "current shaping-loop G3 prepare requires shape_basis evidence")
                g2_key = state["accepted"].get("G2")
                require(g2_key is not None, "accepted G2 evidence coverage is required before G3 prepare")
                opened = {"snapshot": self.snapshot(g2_key), "sources": self._opened_index(self.snapshot(g2_key))}
                declared_basis_facts = self._evidence_line_facts(
                    spec["shape_basis"], opened, purpose="declared shape_basis", state=state)
                retry_new_facts = self._check_floor_only_repeat(state, declared_basis_facts)
            if spec["gate"] == "G3" and state["policy"].get("review_evidence"):
                require(spec.get("participation_evidence") in spec["inputs"], "host participation evidence required")
                self._participation(spec, state)
                proof = shape(spec.get("accepted_proof"), ["text", "source"])
                string(proof["text"])
                require(isinstance(spec.get("seam_applicability"), dict) and spec["seam_applicability"], "controller seam applicability inventory required")
                for key, value in spec["seam_applicability"].items():
                    identifier(key); require(value in ("existing", "new", "nontechnical"), "invalid controller seam applicability")
                source = shape(proof["source"], ["path", "sha256", "locator", "quote"])
                require(source["quote"].rstrip("\r\n") == proof["text"], "accepted proof text must match exact quoted proof")
                prior = self.snapshot(state["accepted"]["G2"])
                owned = dict(prior["input_hashes"])
                owned.update({p: f["sha256"] for p, f in prior["files"].items()})
                require(owned.get(source["path"]) == source["sha256"], "accepted proof source must belong to accepted G2")
                raw = (base64.b64decode(prior["files"][source["path"]]["base64"]) if source["path"] in prior["files"] else read_bytes(self.path(source["path"])))
                require(b"".join(line_span(raw, source["locator"])).decode("utf-8") == source["quote"], "accepted proof quote mismatch")
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
            if spec["gate"] == "G3" and state["policy"].get("review_evidence"):
                order["required_return_schema"] = "shaping-review-evidence.v1#/definitions/reviewV2"
            if spec["gate"] == "G3" and state["policy"].get("shaping_loop", False):
                order["retry_new_facts"] = retry_new_facts
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
        if order["gate"] == "G3" and state["policy"].get("review_evidence"):
            require("review-plan.json" in files, "review-plan.json required before seal")
        cumulative = deepcopy(self.snapshot(order["predecessor"])["files"]) if order["predecessor"] else {}
        # Earlier prose cannot silently change under a later gate.
        for name in cumulative.keys() & files.keys() - {"questions.json", "decisions.json"}:
            require(cumulative[name] == files[name], f"upstream artifact changed: {name}; reopen its stage")
        cumulative.update(files)
        if state["policy"].get("shaping_loop", False):
            self._validate_shaping_candidate(state, order, files)
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

    def _bookkeeping_path(self, snapshot, path, state=None):
        reviewer = snapshot["work_order"]["reviewer"]
        excluded = (set(snapshot["policy_bindings"]) | set(snapshot["files"])
                    | {reviewer["assignment_evidence"], reviewer["context_evidence"]})
        if state is not None:
            for event in state.get("observations", []):
                record = event.get("record", {}) if isinstance(event, dict) else {}
                if isinstance(record, dict) and record.get("kind") in ("review_requested", "review_returned"):
                    provenance = event.get("provenance", {})
                    if isinstance(provenance, dict) and isinstance(provenance.get("path"), str):
                        excluded.add(provenance["path"])
        return path in excluded or PurePosixPath(path).parts[0] in {"state", "accepted", "candidates"}

    def _snapshot_source_bytes(self, snapshot, path, expected_hash):
        artifact = snapshot["files"].get(path)
        if artifact is not None:
            data = base64.b64decode(artifact["base64"], validate=True)
        elif path in snapshot["work_order"]["inputs"]:
            data = read_bytes(self.path(path))
        else:
            raise Hold(f"research source is not retained by accepted G2: {path}")
        require(digest(data) == expected_hash, f"research source bytes changed: {path}")
        return data

    def _opened_index(self, snapshot):
        """Map eligible opened sources to covered line numbers and exact line bytes."""
        try:
            raw = base64.b64decode(snapshot["files"]["research-coverage.json"]["base64"], validate=True)
            coverage = decode(raw)
            shape(coverage, ["schema_version", "opened"])
            require(type(coverage["schema_version"]) is int and coverage["schema_version"] == 1,
                    "unsupported research coverage schema")
            require(isinstance(coverage["opened"], list), "research coverage opened must be an array")
            index = {}
            for item in coverage["opened"]:
                shape(item, ["path", "sha256", "locators"])
                path, sha = safe_relative(item["path"]), item["sha256"]
                require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
                        "invalid research source sha256")
                locators = strings(item["locators"])
                data = self._snapshot_source_bytes(snapshot, path, sha)
                lines = data.splitlines(keepends=True)
                row = index.setdefault((path, sha), {"data": data, "opened_lines": set()})
                require(row["data"] == data, "conflicting retained source bytes")
                for locator in locators:
                    line_span(data, locator)
                    first, last = map(int, locator.split(":"))
                    row["opened_lines"].update(range(first, last + 1))
            return index
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise Hold("return to research: accepted G2 research-coverage.json is missing or invalid") from exc

    def _evidence_line_facts(self, evidence, opened, *, purpose, state=None):
        require(isinstance(evidence, list), f"{purpose} must be an evidence array")
        facts = set()
        for item in evidence:
            shape(item, ["path", "sha256", "locators"])
            path, sha = safe_relative(item["path"]), item["sha256"]
            require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
                    f"invalid {purpose} sha256")
            require(not self._bookkeeping_path(opened["snapshot"], path, state),
                    f"{purpose} cannot use policy, resource, review, assignment, context, or draft evidence: {path}")
            row = opened["sources"].get((path, sha))
            require(row is not None, f"return to research: {purpose} source was not opened in accepted G2: {path}")
            locators = strings(item["locators"])
            lines = row["data"].splitlines(keepends=True)
            for locator in locators:
                span = line_span(row["data"], locator)
                first, last = map(int, locator.split(":"))
                positions = set(range(first, last + 1))
                require(positions <= row["opened_lines"],
                        f"return to research: {purpose} span was not opened in accepted G2: {path}:{locator}")
                for position in positions:
                    facts.add((path, sha, digest(lines[position - 1])))
        return facts

    def _opened_facts(self, snapshot, state=None):
        """Identity is the exact bytes of opened source lines, independent of path/locator format."""
        opened = {"snapshot": snapshot, "sources": self._opened_index(snapshot)}
        return {fact[2] for key, row in opened["sources"].items()
                if not self._bookkeeping_path(snapshot, key[0], state)
                for line_no in row["opened_lines"]
                for fact in [(key[0], key[1], digest(row["data"].splitlines(keepends=True)[line_no - 1]))]}

    def _validate_coverage(self, state, order, files):
        raw = base64.b64decode(files["research-coverage.json"]["base64"], validate=True)
        coverage = decode(raw)
        shape(coverage, ["schema_version", "opened"])
        require(type(coverage["schema_version"]) is int and coverage["schema_version"] == 1,
                "unsupported research coverage schema")
        require(isinstance(coverage["opened"], list), "research coverage opened must be an array")
        predecessor = self.snapshot(order["predecessor"]) if order["predecessor"] else {}
        source_hashes = dict(order["input_hashes"])
        for name, item in predecessor.get("files", {}).items():
            source_hashes[name] = item["sha256"]
        seen = set()
        for item in coverage["opened"]:
            shape(item, ["path", "sha256", "locators"])
            path = safe_relative(item["path"])
            sha = item["sha256"]
            require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
                    "invalid research source sha256")
            locators = strings(item["locators"])
            key = (path, sha, tuple(locators))
            require(key not in seen, "duplicate research coverage record")
            seen.add(key)
            require(source_hashes.get(path) == sha,
                    f"return to research: {path} is not a hashed G2 input or cumulative artifact")
            if path in order["input_hashes"]:
                data = read_bytes(self.path(path))
            else:
                artifact = predecessor.get("files", {}).get(path)
                require(artifact is not None, f"return to research: source is not a hashed G2 input or cumulative artifact: {path}")
                data = base64.b64decode(artifact["base64"], validate=True)
            require(digest(data) == sha, f"return to research: source bytes do not match coverage for {path}")
            for locator in locators:
                line_span(data, locator)
        return coverage

    def _validate_shaping_candidate(self, state, order, files):
        if order["gate"] == "G2":
            self._validate_coverage(state, order, files)
            return
        if order["gate"] != "G3":
            return
        g2_key = state["accepted"].get("G2")
        require(g2_key is not None, "return to research: accepted G2 evidence coverage is required")
        g2 = self.snapshot(g2_key)
        opened = {"snapshot": g2, "sources": self._opened_index(g2)}
        basis_facts = self._evidence_line_facts(order["shape_basis"], opened,
                                                purpose="declared shape_basis", state=state)
        raw = base64.b64decode(files["shape-set.json"]["base64"], validate=True)
        shape_set = decode(raw)
        shape(shape_set, ["schema_version", "selected_parts", "walk_away_item", "claims"])
        require(type(shape_set["schema_version"]) is int and shape_set["schema_version"] == 1,
                "unsupported shape-set schema")
        selected = strings(shape_set["selected_parts"], False)
        for part in selected:
            identifier(part)
        string(shape_set["walk_away_item"])
        if not selected:
            raise Hold(f"no selected solution; walk-away item: {shape_set['walk_away_item']}")
        require(isinstance(shape_set["claims"], list), "shape-set claims must be an array")
        claims_by_id, grounded_existing = {}, set()
        for claim in shape_set["claims"]:
            shape(claim, ["id", "status", "load_bearing", "evidence", "basis_claims"])
            claim_id = identifier(claim["id"])
            require(claim_id not in claims_by_id, "duplicate shape claim ID")
            require(claim["status"] in ("existing", "proposed_extension"), "invalid shape claim status")
            boolean(claim["load_bearing"])
            require(isinstance(claim["evidence"], list), "claim evidence must be an array")
            for basis_id in strings(claim["basis_claims"], False):
                identifier(basis_id)
            evidence_facts = self._evidence_line_facts(claim["evidence"], opened,
                                                       purpose=f"claim {claim_id} evidence", state=state)
            require(evidence_facts <= basis_facts,
                    f"claim {claim_id} evidence is outside the declared shape_basis")
            if claim["status"] == "existing" and claim["load_bearing"]:
                require(evidence_facts, f"return to research: load-bearing existing claim {claim_id} lacks opened evidence")
            if claim["status"] == "existing" and evidence_facts:
                grounded_existing.add(claim_id)
            claims_by_id[claim_id] = {"status": claim["status"], "evidence": evidence_facts,
                                      "basis": strings(claim["basis_claims"], False)}
        for claim in shape_set["claims"]:
            if claim["status"] == "proposed_extension":
                basis = strings(claim["basis_claims"])
                require(set(basis) <= grounded_existing,
                        f"proposed extension {claim['id']} needs grounded existing basis claims")
        used_facts = set()
        for selected_id in selected:
            claim = claims_by_id.get(selected_id)
            require(claim is not None, f"selected part {selected_id} has no corresponding shape claim")
            if claim["status"] == "existing":
                require(claim["evidence"], f"selected existing claim {selected_id} needs opened evidence")
                used_facts.update(fact[2] for fact in claim["evidence"])
            else:
                require(claim["basis"] and set(claim["basis"]) <= grounded_existing,
                        f"selected extension {selected_id} needs grounded existing basis claims")
                for basis_id in claim["basis"]:
                    used_facts.update(fact[2] for fact in claims_by_id[basis_id]["evidence"])
        if order.get("retry_new_facts"):
            require(bool(used_facts & set(order["retry_new_facts"])),
                    "floor-only G3 retry blocked: selected claim basis does not use newly opened evidence")
        self._validate_sequence(files)

    @staticmethod
    def _validate_sequence(files):
        raw = base64.b64decode(files["sequence.mmd"]["base64"], validate=True)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise Hold("sequence.mmd must be valid UTF-8 Mermaid source") from exc
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("%%")]
        require(bool(lines) and lines[0] == "sequenceDiagram",
                "shaping loop requires sequence.mmd to be a Mermaid sequenceDiagram")
        require(not any(re.match(r"^(?:alt|else)(?:\s|$)", line) for line in lines[1:]),
                "sequence.mmd alt/else blocks are unsupported by the shaping renderer")

    def _floor_only_failure_facts(self, state):
        failures = []
        events = state.get("observations", [])
        if not isinstance(events, list):
            raise Recovery("observation journal is not an array")
        current_bindings = state.get("policy_bindings")
        if not isinstance(current_bindings, dict) or not current_bindings:
            raise Recovery("current policy bindings are missing or malformed")
        current_policy_hash = digest(encoded(current_bindings))
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                raise Recovery("malformed observation may hide a G3 review_returned failure")
            record = event.get("record", {})
            if not isinstance(record, dict):
                if event.get("gate") == "G3":
                    raise Recovery("malformed G3 review_returned observation record")
                continue
            kind = record.get("kind")
            if kind != "review_returned":
                if event.get("gate") == "G3" and kind is None:
                    raise Recovery("malformed G3 observation kind")
                continue
            work_order_id = record.get("work_order_id")
            if not isinstance(work_order_id, str):
                raise Recovery("review_returned observation work-order ID is malformed")
            orders = state.get("orders")
            if not isinstance(orders, dict):
                raise Recovery("work-order journal is missing or malformed")
            order = orders.get(work_order_id)
            if not isinstance(order, dict):
                raise Recovery("review_returned observation references an unknown work order")
            if order.get("gate") != "G3":
                if event.get("gate") == "G3":
                    raise Recovery("G3 review_returned observation references a non-G3 work order")
                continue
            try:
                bindings = order.get("policy_bindings")
                require(isinstance(bindings, dict) and bool(bindings), "work-order policy bindings are missing")
                for path, pinned_hash in bindings.items():
                    safe_relative(path)
                    require(isinstance(pinned_hash, str) and re.fullmatch(r"[0-9a-f]{64}", pinned_hash),
                            "work-order policy binding digest is malformed")
                recorded_policy_hash = order.get("policy_hash")
                require(isinstance(recorded_policy_hash, str)
                        and re.fullmatch(r"[0-9a-f]{64}", recorded_policy_hash),
                        "work-order policy hash is missing or malformed")
                require(recorded_policy_hash == digest(encoded(bindings)),
                        "work-order policy hash does not match its stored policy bindings")

                require(record.get("event_id") and record.get("run_id") == state.get("run_id")
                        and record.get("generation") == order.get("generation")
                        and record.get("work_order_id") == work_order_id,
                        "review observation identity does not match its work order")
                integer(record.get("version"))
                integer(event.get("recorded_version"), 1)
                require(event["recorded_version"] == record["version"] + 1,
                        "review observation version binding is invalid")
                require(event.get("gate") == "G3" and order.get("run_id") == state.get("run_id"),
                        "review event gate/run binding is missing")
                require(record.get("actor") == order.get("reviewer", {}).get("identity"),
                        "review observation actor does not match its assigned reviewer")
                seal = shape(order.get("seal"), ["subject", "questions", "decisions", "work_order_id",
                                                  "generation", "predecessor", "return_hash"], ["review_packet", "review_files", "review_inputs"])
                require(seal["work_order_id"] == work_order_id
                        and seal["generation"] == order.get("generation")
                        and seal["predecessor"] == order.get("predecessor"),
                        "sealed subject identity does not match its work order")
                require(isinstance(seal["subject"], dict), "sealed subject inventory is malformed")
                for name, sha in seal["subject"].items():
                    safe_relative(name)
                    require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha),
                            "sealed subject digest is malformed")
                seal_payload = {key: seal[key] for key in
                                ("subject", "questions", "decisions", "work_order_id", "generation", "predecessor")}
                if "review_packet" in seal:
                    require("review_files" in seal and "review_inputs" in seal, "review evidence retained bytes missing")
                    seal_payload.update(review_files=seal["review_files"], review_inputs=seal["review_inputs"])
                require(isinstance(seal["return_hash"], str)
                        and seal["return_hash"] == digest(encoded(seal_payload)),
                        "sealed subject return hash is invalid")
                require(event.get("return_hash") == seal["return_hash"],
                        "review event return hash does not match its sealed G3 subject")

                provenance = shape(event.get("provenance"), ["path", "sha256"])
                require(record.get("evidence") == provenance["path"], "review receipt path binding is missing")
                safe_relative(provenance["path"])
                require(isinstance(provenance["sha256"], str)
                        and re.fullmatch(r"[0-9a-f]{64}", provenance["sha256"]),
                        "review receipt digest is malformed")
                # The immutable journal captured this parsed review at observation.
                # Legacy entries do not retain raw bytes: their provenance digest
                # cannot be recomputed from parsed JSON or authenticated by rereading
                # a mutable original path. Validate the captured envelope instead.
                review = event.get("review")
                shape(review, ["schema_version", "run_id", "gate", "work_order_id", "generation", "policy_hash",
                               "resource_revision", "predecessor", "return_hash", "subject", "reviewer",
                               "authored_candidate", "independence_confirmed", "evidence", "assessments",
                               "findings", "unresolved_blockers", "verdict", "next_state", "scores",
                               "render_evidence", "targets"], ["review_evidence"])
                require(type(review["schema_version"]) is int and review["schema_version"] in (1, 2),
                        "unsupported review receipt schema")
                for key in ("run_id", "gate", "work_order_id", "generation", "policy_hash",
                            "resource_revision", "predecessor"):
                    expected = "G3" if key == "gate" else order.get(key)
                    require(review[key] == expected, f"review receipt binding mismatch: {key}")
                require(review["return_hash"] == seal["return_hash"]
                        and review["subject"] == seal["subject"], "review receipt subject binding mismatch")
                require(review["reviewer"] == order.get("reviewer", {}).get("identity")
                        and review["authored_candidate"] is False
                        and review["independence_confirmed"] is True,
                        "review receipt reviewer binding is invalid")
                require(review["next_state"] == "G3"
                        and review["verdict"] in ("pass", "fail", "unverifiable"),
                        "review receipt verdict/state binding is invalid")

                predecessor = order.get("predecessor")
                require(isinstance(predecessor, str) and re.fullmatch(r"[0-9a-f]{64}", predecessor),
                        "G3 review has no immutable G2 predecessor")
                prior = self.snapshot(predecessor)
                require(prior.get("gate") == "G2" and prior.get("run_id") == state.get("run_id")
                        and prior.get("policy_bindings") == bindings,
                        "G3 predecessor does not match the recorded policy binding")

                # Older policy receipts remain auditable history. Their scoring
                # and coverage contracts cannot be interpreted through today's policy.
                if recorded_policy_hash != current_policy_hash:
                    continue

                subject_files = seal.get("review_files") or {name: {"sha256": sha} for name, sha in seal["subject"].items()}
                review_policy = deepcopy(state["policy"])
                review_policy["gates"]["G3"]["predicates"] = order["required_predicates"]
                self._review(review, {**state, "policy": review_policy}, order, subject_files,
                             acceptance=False)
                if review["verdict"] != "fail":
                    continue
                scores = review["scores"]["dimensions"]
                values = [scores[key]["score"] for key in TEAM + PITCH]
                assessments = review["assessments"]
                if min(values) < 3 or sum(values) / 12 >= 4:
                    continue
                if any(assessments[name]["outcome"] != "pass"
                       for name in order["required_predicates"] if name != "rubric_assessment"):
                    continue
                failures.append((index, self._opened_facts(self.snapshot(predecessor), state)))
            except (Hold, OSError, KeyError, TypeError, ValueError, AttributeError,
                    IndexError, binascii.Error) as exc:
                raise Recovery(f"cannot verify recorded G3 review_returned event "
                               f"{record.get('event_id', '<unknown>')}: {exc}") from exc
        return failures[-1][1] if failures else None

    def _check_floor_only_repeat(self, state, declared_basis_facts):
        failed_facts = self._floor_only_failure_facts(state)
        if failed_facts is None:
            return []
        current = self.snapshot(state["accepted"]["G2"])
        new_facts = self._opened_facts(current, state) - failed_facts
        require(bool(new_facts),
                "floor-only G3 retry blocked: return to research and open new evidence before preparing another writer")
        declared_lines = {fact[2] for fact in declared_basis_facts}
        require(bool(new_facts & declared_lines),
                "floor-only G3 retry blocked: newly opened evidence must be included in declared shape_basis")
        return sorted(new_facts)

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
            if state["policy"].get("review_evidence") and order["gate"] == "G3":
                result["review_files"] = deepcopy(files)
                inputs = dict(order["policy_bindings"])
                if order["predecessor"]: inputs.update(self.snapshot(order["predecessor"])["input_hashes"])
                inputs.update(order["input_hashes"])
                result["review_inputs"] = {p: base64.b64encode(read_bytes(self.path(p))).decode("ascii") for p in inputs}
            result["return_hash"] = digest(encoded(result))
            if state["policy"].get("review_evidence") and order["gate"] == "G3":
                result["review_packet"] = self._review_packet(state, order, files, result)
            if order["seal"] is not None:
                require(order["seal"] == result, "sealed candidate changed; use new work order")
                return result
            order["seal"] = result
            self._commit(state, expected)
            return result

    def review_observation(self, order_id, path, expected):
        """Controller records independent host observations after seal, before return.

        The host enforces controller-only access. This method binds and retains
        observations; it cannot authenticate who supplied the bytes.
        """
        with self.lock():
            state = self._load()
            self._expected(state, expected)
            order = self._current_order(state, order_id)
            require(state['policy'].get('review_evidence') and order['gate'] == 'G3' and order['seal'], 'post-seal review observation required')
            self._input_name(path)
            raw = read_bytes(self.path(path)); record = decode(raw)
            shape(record, ['schema_version', 'run_id', 'work_order_id', 'packet_hash', 'host', 'openings', 'renders', 'answers', 'contributors'])
            require(type(record['schema_version']) is int and record['schema_version'] == 1, 'invalid host record schema')
            packet = order['seal']['review_packet']
            require(record['run_id'] == order['run_id'] and record['work_order_id'] == order_id and record['packet_hash'] == digest(encoded(packet)), 'host observation packet mismatch')
            host = shape(record['host'], ['identity', 'reviewer', 'observed', 'return_hash'])
            string(host['identity'])
            require(host['observed'] is True and host['reviewer'] == packet['reviewer'] and host['return_hash'] == packet['return_hash'], 'host capability unavailable')
            participation = self._participation(order, state)
            require(set(strings(record['contributors'])) == set(participation['contributors']), 'sealed revision contributors changed; prepare a fresh work order')
            require(host['reviewer'] not in record['contributors'], 'sealed revision contributor cannot grade')
            require(record['openings'] == packet['entries'], 'host ordered openings mismatch')
            require(isinstance(record['renders'], dict) and isinstance(record['answers'], dict), 'host observation inventories missing')
            value = {'binding': {'path': path, 'sha256': digest(raw)}, 'record': record}
            if order.get('review_observation'):
                require(order['review_observation'] == value, 'controller host observation conflict')
                return value
            order['review_observation'] = value
            self._commit(state, expected)
            return value

    def _participation(self, order, state):
        """Bind host-issued stable IDs, without pretending to authenticate them."""
        path = order.get('participation_evidence')
        require(path is not None, 'host participation evidence required')
        raw = (base64.b64decode(order['seal']['review_inputs'][path]) if order.get('seal') and 'review_inputs' in order['seal'] else read_bytes(self.path(path)))
        record = decode(raw)
        shape(record, ['schema_version', 'run_id', 'work_order_id', 'host', 'observed',
                       'author', 'reviewer', 'contributors', 'repairs'])
        require(type(record['schema_version']) is int and record['schema_version'] == 1 and record['observed'] is True, 'identity capability unavailable')
        string(record['host'])
        require(record['run_id'] == state['run_id'] and record['work_order_id'] == order['work_order_id'], 'participation binding mismatch')
        require(record['author'] == order['author'] and record['reviewer'] == order['reviewer']['identity'], 'stable identity mismatch')
        contributors = strings(record['contributors'])
        require(record['author'] in contributors, 'author absent from participation')
        require(isinstance(record['repairs'], list), 'repair participation missing')
        for repair in record['repairs']:
            shape(repair, ['identity', 'original_author', 'original_reviewer', 'consent', 'contributed', 'work_order_id', 'return_hash', 'finding_id'])
            string(repair['identity'])
            require(repair['identity'] not in (repair['original_author'], repair['original_reviewer']), 'fixer must be independent')
            boolean(repair['contributed'])
            if repair['contributed']:
                consent = shape(repair['consent'], ['accepted', 'user', 'reference', 'before_contribution'])
                require(consent['accepted'] is True and consent['before_contribution'] is True, 'fixer consent required before contribution')
                string(consent['user']); string(consent['reference'])
                require(repair['identity'] in contributors, 'fixer absent from authorship')
                origin = state['orders'].get(repair['work_order_id'])
                require(origin and origin.get('seal') and origin['seal']['return_hash'] == repair['return_hash'], 'repair origin is not a sealed work order')
                require(origin['author'] == repair['original_author'] and origin['reviewer']['identity'] == repair['original_reviewer'], 'repair original stable identities mismatch')
                reviews = [event.get('review') for event in state.get('observations', []) if event.get('record', {}).get('kind') == 'review_returned' and event.get('record', {}).get('work_order_id') == repair['work_order_id']]
                require(any(review and review.get('verdict') != 'pass' and review.get('return_hash') == repair['return_hash'] and any(isinstance(f, dict) and f.get('id') == repair['finding_id'] for f in review.get('findings', [])) for review in reviews), 'repair must bind a failed finding in this run')
        prior_contributors = set()
        for prior in state['orders'].values():
            if prior.get('participation_evidence'):
                # Re-read only immutable hashed observations; changed host evidence holds.
                prior_raw = (base64.b64decode(prior['seal']['review_inputs'][prior['participation_evidence']]) if prior.get('seal') and 'review_inputs' in prior['seal'] else read_bytes(self.path(prior['participation_evidence'])))
                require(digest(prior_raw) == prior['input_hashes'][prior['participation_evidence']], 'participation history drift')
                prior_record = decode(prior_raw)
                prior_contributors.update(prior_record['contributors'])
        require(record['reviewer'] not in set(contributors) | prior_contributors, 'contributor/fixer cannot grade revision')
        return record

    def _review_packet(self, state, order, files, seal):
        inputs = dict(order['policy_bindings'])
        if order['predecessor']:
            inputs.update(self.snapshot(order['predecessor'])['input_hashes'])
        inputs.update(order['input_hashes'])
        entries = []
        for path, sha in sorted(inputs.items()):
            raw = base64.b64decode(seal['review_inputs'][path])
            require(digest(raw) == sha, 'packet input drift')
            entries.append((path, sha, raw))
        for path, item in sorted(files.items()):
            require(path not in inputs, 'packet path collision')
            entries.append((path, item['sha256'], base64.b64decode(item['base64'])))
        packet = {key: order[key] for key in ('run_id', 'work_order_id', 'policy_hash', 'generation')}
        packet.update(schema_version=1, return_hash=seal['return_hash'], reviewer=order['reviewer']['identity'], entries=[])
        for path, sha, raw in entries:
            try:
                raw.decode('utf-8')
                locators = [f'1:{len(raw.splitlines())}'] if raw.splitlines() else []
            except UnicodeDecodeError: locators = []
            packet['entries'].append({'path': path, 'sha256': sha, 'locators': locators})
        return packet

    def _review_evidence(self, receipt, state, order, files, acceptance):
        packet = self._review_packet(state, order, files, order['seal'])
        require(packet == order['seal']['review_packet'], 'sealed packet drift')
        record = shape(receipt.get('review_evidence'), ['schema_version', 'packet_hash', 'host',
                    'openings', 'renders', 'seams', 'questions', 'semantic_audit', 'host_record'])
        require(type(record['schema_version']) is int and record['schema_version'] == 1 and record['packet_hash'] == digest(encoded(packet)), 'review packet binding mismatch')
        host = shape(record['host'], ['identity', 'reviewer', 'observed', 'return_hash'])
        string(host['identity'])
        require(host['observed'] is True and host['reviewer'] == packet['reviewer'] and host['return_hash'] == packet['return_hash'], 'host observation/identity unavailable or unbound')
        binding = shape(record['host_record'], ['path', 'sha256'])
        observed = order.get('review_observation')
        require(observed is not None and observed['binding'] == binding, 'controller post-seal host record required')
        observation = observed['record']
        require(observation['packet_hash'] == record['packet_hash'] and observation['host'] == host, 'controller host record binding mismatch')
        self._participation(order, state)
        require(isinstance(record['openings'], list), 'ordered host openings required')
        expected_openings = [{'path': e['path'], 'sha256': e['sha256'], 'locators': e['locators']} for e in packet['entries']]
        require(record['openings'] == expected_openings, 'ordered host openings missing or changed')
        require(observation['openings'] == expected_openings, 'controller ordered host openings missing or changed')
        entries = {entry['path']: entry for entry in packet['entries']}
        def quote(item):
            shape(item, ['path', 'sha256', 'locator', 'quote'])
            require(item['path'] in entries and item['sha256'] == entries[item['path']]['sha256'], 'quote packet membership/hash mismatch')
            raw = (base64.b64decode(files[item['path']]['base64']) if item['path'] in files else base64.b64decode(order['seal']['review_inputs'][item['path']]))
            actual = b''.join(line_span(raw, item['locator'])).decode('utf-8')
            require(item['quote'] == actual and actual.strip(), 'source quote/span mismatch')
        plan = decode(base64.b64decode(files['review-plan.json']['base64']))
        shape(plan, ['schema_version', 'proof', 'proof_source', 'seams'])
        require(type(plan['schema_version']) is int and plan['schema_version'] == 1, 'unsupported review plan')
        string(plan['proof']); quote(plan['proof_source'])
        require(plan['proof'] == order['accepted_proof']['text'] and plan['proof_source'] == order['accepted_proof']['source'], 'accepted proof binding mismatch')
        require(isinstance(plan['seams'], list) and plan['seams'] and isinstance(record['seams'], list), 'explicit seam applicability inventory required')
        declared = {}
        for seam in plan['seams']:
            shape(seam, ['id', 'applicability', 'reason', 'receiver', 'field', 'field_type',
                         'expression', 'input', 'message', 'proof', 'read'])
            identifier(seam['id']); require(seam['id'] not in declared, 'duplicate seam')
            require(seam['applicability'] in ('existing', 'new', 'nontechnical'), 'unsupported seam applicability')
            for key in ('reason', 'receiver', 'field', 'field_type', 'expression', 'input', 'message', 'proof'): string(seam[key])
            require(seam['proof'] == plan['proof'], 'seam proof mismatch')
            quote(seam['read']); declared[seam['id']] = seam
        if state['policy'].get('shaping_loop'):
            shape_set = decode(base64.b64decode(files['shape-set.json']['base64']))
            existing_ids = {claim['id'] for claim in shape_set['claims'] if claim['status'] == 'existing' and claim['load_bearing']}
            require(existing_ids <= declared.keys(), 'existing claim seam omitted from review inventory')
            require(existing_ids <= order['seam_applicability'].keys(), 'existing seam lacks controller applicability')
            require(all(declared[key]['applicability'] == order['seam_applicability'][key] and declared[key]['applicability'] != 'new' for key in existing_ids), 'existing seam cannot be relabelled against controller applicability')
        judgments = {}
        for judgment in record['seams']:
            shape(judgment, ['id', 'predicate_status', 'read_support', 'applicability_supported', 'message_matches', 'explanation'])
            require(judgment['id'] in declared and judgment['id'] not in judgments, 'unknown/duplicate seam judgment')
            require(judgment['predicate_status'] in ('grounded', 'missing', 'not_applicable'), 'invalid predicate status')
            for key in ('read_support', 'applicability_supported', 'message_matches'): boolean(judgment[key])
            string(judgment['explanation'])
            judgments[judgment['id']] = judgment
        require(judgments.keys() == declared.keys(), 'missing seam assessment')
        failures = []
        for key, judgment in judgments.items():
            seam = declared[key]
            supported = judgment['applicability_supported'] and (judgment['read_support'] if seam['applicability'] == 'existing' else True)
            grounded = supported and judgment['predicate_status'] == ('grounded' if seam['applicability'] == 'existing' else 'not_applicable')
            if not grounded: failures.append(('research', 'contracts_security', key))
            elif not judgment['message_matches']: failures.append(('shaping', 'contracts_security', key))
        require(isinstance(record['questions'], list), 'question review inventory required')
        questions = {q['id']: q for q in order['seal']['questions'] if q['in_scope']}
        reviewed = set()
        for review in record['questions']:
            shape(review, ['id', 'text', 'proof', 'depends', 'source', 'independence_supported', 'respondent', 'answer_observation'])
            require(review['id'] in questions and review['id'] not in reviewed, 'unknown/duplicate question review')
            reviewed.add(review['id'])
            q = questions[review['id']]
            require(review['text'] == q.get('details', {}).get('text') and review['proof'] == plan['proof'], 'question/proof binding mismatch')
            boolean(review['depends']); boolean(review['independence_supported']); quote(review['source'])
            if review['depends']:
                require(review['respondent'] == q.get('details', {}).get('respondent') and review['respondent'], 'named respondent binding required')
                answer = review['answer_observation']
                valid = False
                if answer is not None:
                    shape(answer, ['identity', 'authority', 'observed', 'source'])
                    require(answer['identity'] == review['respondent'] and answer['observed'] is True, 'unauthorized respondent substitution')
                    string(answer['authority']); quote(answer['source'])
                    require(observation['answers'].get(review['id']) == answer, 'controller respondent provenance missing')
                    valid = q['status'] == 'answered'
                if not valid: failures.append(('respondent', 'workstreams_proof', review['id']))
            elif q['status'] != 'answered' and not review['independence_supported']:
                failures.append(('respondent', 'workstreams_proof', review['id']))
        require(reviewed == questions.keys(), 'missing question-specific independence evidence')
        require(isinstance(record['renders'], dict), 'render inventory required')
        require(record['renders'].keys() <= set(DIAGRAMS), 'unknown diagram')
        for source in DIAGRAMS:
            render = record['renders'].get(source)
            if render is None:
                failures.append(('review_hold', 'diagrams_visual', source)); continue
            shape(render, ['source_hash', 'path', 'sha256', 'pixels_path', 'pixels_sha256', 'opened', 'visible', 'labels', 'connectors', 'source_agreement', 'explanation'])
            require(render['source_hash'] == files[source]['sha256'], 'render/source binding mismatch')
            for pathkey, hashkey in [('path', 'sha256'), ('pixels_path', 'pixels_sha256')]:
                require(render[pathkey] in files and render[hashkey] == files[render[pathkey]]['sha256'], 'render packet binding mismatch')
            host_render = {key: render[key] for key in ('source_hash', 'path', 'sha256', 'pixels_path', 'pixels_sha256', 'opened')}
            require(observation['renders'].get(source) == host_render, 'controller rendered opening record mismatch')
            raw = base64.b64decode(files[render['path']]['base64'])
            usable = True
            try:
                if render['path'].endswith('.svg'): validate_review_svg(raw)
                else:
                    require(render['path'].endswith('.png'), 'unsupported PNG/SVG render')
                    require(render['path'] == render['pixels_path'], 'PNG pixels mismatch')
                require(render['pixels_path'].endswith('.png'), 'SVG requires actual PNG rasterization')
                validate_review_png(base64.b64decode(files[render['pixels_path']]['base64']))
            except Hold: usable = False
            for key in ('opened', 'visible', 'labels', 'connectors', 'source_agreement'): boolean(render[key])
            string(render['explanation'])
            if not usable or not all(render[key] for key in ('opened', 'visible', 'labels', 'connectors', 'source_agreement')):
                failures.append(('review_hold', 'diagrams_visual', source))
        audit = shape(record['semantic_audit'], ['performed', 'consistent', 'explanation', 'contradictions'])
        require(audit['performed'] is True, 'independent semantic contradiction audit required')
        boolean(audit['consistent']); string(audit['explanation'])
        require(isinstance(audit['contradictions'], list), 'structured contradiction inventory required')
        contradictions = {}
        special_failures = tuple(failures)
        special_failure_checks = {failure[1] for failure in special_failures}
        for contradiction in audit['contradictions']:
            shape(contradiction, ['id', 'check', 'item', 'route', 'rationale_path', 'rationale_quote', 'source', 'explanation'])
            identifier(contradiction['id']); require(contradiction['id'] not in contradictions, 'duplicate contradiction ID')
            require(contradiction['check'] in receipt['assessments'] and contradiction['route'] in ('research', 'shaping', 'respondent'), 'invalid contradiction check/route')
            subject = contradiction['item']
            assessment_owned = subject == 'assessment:' + contradiction['check']
            require(subject in declared or subject in questions or assessment_owned, 'contradiction subject unowned')
            if assessment_owned:
                require(contradiction['route'] == 'shaping' and receipt['assessments'][contradiction['check']]['outcome'] != 'pass', 'assessment contradiction requires failed owned check and shaping route')
            else:
                require((contradiction['route'], contradiction['check'], subject) in failures, 'contradiction route/check must match structured subject failure')
            rationale_path = contradiction['rationale_path'].split('.')
            require((len(rationale_path) == 3 and rationale_path[0] == 'assessments' and rationale_path[1] == contradiction['check'] and rationale_path[2] == 'explanation') or (len(rationale_path) == 4 and rationale_path[:2] == ['scores', 'dimensions'] and rationale_path[2] in TEAM + PITCH and rationale_path[3] == 'rationale'), 'invalid contradiction rationale locator')
            rationale = receipt
            for part in rationale_path: rationale = rationale[part]
            require(string(contradiction['rationale_quote']) == rationale, 'contradiction rationale quote mismatch')
            quote(contradiction['source']); string(contradiction['explanation'])
            if assessment_owned and contradiction['check'] in special_failure_checks:
                require(rationale_path[0] == 'scores', 'special subject failure cannot be relabelled as generic assessment contradiction')
                generic_source = contradiction['source']
                generic_first, generic_last = map(int, generic_source['locator'].split(':'))
                for _, check, special_item in special_failures:
                    if check != contradiction['check']: continue
                    if special_item in declared: special_source = declared[special_item]['read']
                    elif special_item in questions:
                        special_source = next(q['source'] for q in record['questions'] if q['id'] == special_item)
                    else: continue
                    special_first, special_last = map(int, special_source['locator'].split(':'))
                    same_source = generic_source['path'] == special_source['path'] or generic_source['sha256'] == special_source['sha256']
                    require(not same_source or generic_last < special_first or special_last < generic_first, 'generic contradiction overlaps special subject evidence')
            if subject in declared: require(contradiction['source'] == declared[subject]['read'], 'contradiction seam source mismatch')
            elif subject in questions:
                question_review = next(q for q in record['questions'] if q['id'] == subject)
                require(contradiction['source'] == question_review['source'], 'contradiction question source mismatch')
            else:
                evidence_ids = receipt['assessments'][contradiction['check']]['evidence_ids']
                if rationale_path[0] == 'scores': evidence_ids = receipt['scores']['dimensions'][rationale_path[2]]['evidence_ids']
                require(contradiction['source']['path'] in {receipt['evidence'].get(key) for key in evidence_ids}, 'assessment contradiction requires relevant cited evidence')
            contradictions[contradiction['id']] = contradiction
            failures.append((contradiction['route'], contradiction['check'], contradiction['id']))
        require(audit['consistent'] == (not contradictions), 'semantic audit consistency/inventory mismatch')
        require(isinstance(receipt['findings'], list), 'typed findings required')
        finding_ids, bound = set(), []
        for finding in receipt['findings']:
            shape(finding, ['id', 'check', 'item', 'route', 'status', 'source', 'repair', 'respondent', 'prerequisite'])
            identifier(finding['id']); require(finding['id'] not in finding_ids, 'duplicate finding')
            finding_ids.add(finding['id'])
            require(finding['check'] in receipt['assessments'] and receipt['assessments'][finding['check']]['outcome'] != 'pass', 'finding/check outcome inconsistency')
            require(finding['status'] == 'unresolved' and finding['route'] in ('review_hold', 'research', 'shaping', 'respondent'), 'invalid return route/status')
            quote(finding['source']); string(finding['repair'])
            if finding['item'] in declared:
                require(finding['source'] == declared[finding['item']]['read'], 'finding lacks relevant seam evidence')
            elif finding['item'] in DIAGRAMS:
                require(finding['source']['path'] == finding['item'], 'finding lacks relevant diagram evidence')
            elif finding['item'] in contradictions:
                require(finding['source'] == contradictions[finding['item']]['source'], 'finding lacks relevant rationale contradiction evidence')
            elif finding['item'] in questions:
                question_review = next(q for q in record['questions'] if q['id'] == finding['item'])
                require(finding['source'] == question_review['source'], 'finding lacks relevant question evidence')
            if finding['route'] == 'respondent':
                question_id = contradictions[finding['item']]['item'] if finding['item'] in contradictions else finding['item']
                require(question_id in questions and finding['respondent'] == questions[question_id].get('details', {}).get('respondent') and finding['respondent'], 'return requires named respondent')
            else: require(finding['respondent'] is None, 'respondent belongs to question route')
            bound.append((finding['route'], finding['check'], finding['item']))
        require(len(set(bound)) == len(bound), 'exactly one return per finding/check/item')
        allowed = set(failures)
        for check, assessment in receipt['assessments'].items():
            if assessment['outcome'] != 'pass' and not any(f[1] == check for f in failures):
                allowed.add(('shaping', check, check))
        require(set(failures) <= set(bound), 'missing relevant typed finding for failed check')
        require(set(bound) <= allowed, 'return route/item not owned by failed check')
        for finding in receipt['findings']:
            require(finding['prerequisite'] is None or finding['prerequisite'] in finding_ids - {finding['id']}, 'unknown/self prerequisite')
        dependencies = {f['id']: f['prerequisite'] for f in receipt['findings']}
        for start in dependencies:
            seen, current = set(), start
            while current is not None:
                require(current not in seen, 'cyclic return prerequisites')
                seen.add(current); current = dependencies[current]
        for check, assessment in receipt['assessments'].items():
            if assessment['outcome'] != 'pass': require(any(f['check'] == check for f in receipt['findings']), 'failed assessment lacks finding')
        if failures or receipt['findings']:
            require(receipt['verdict'] != 'pass', 'unresolved finding/predicate cannot pass')
        if acceptance: require(not failures and not receipt['findings'], 'review evidence unresolved')

    def _review(self, receipt, state, order, files, acceptance=True):
        current_evidence = order["gate"] == "G3" and state["policy"].get("review_evidence", False)
        if current_evidence:
            shape(receipt, ["schema_version", "run_id", "gate", "work_order_id", "generation", "policy_hash",
                "resource_revision", "predecessor", "return_hash", "subject", "reviewer", "authored_candidate",
                "independence_confirmed", "evidence", "assessments", "findings", "unresolved_blockers",
                "verdict", "next_state", "scores", "render_evidence", "targets", "review_evidence"])
            shape(receipt["assessments"], order["required_predicates"])
            for assessment in receipt["assessments"].values():
                shape(assessment, ["outcome", "evidence_ids", "explanation"])
            require(isinstance(receipt["evidence"], dict) and receipt["evidence"], "evidence inventory missing")
            scores = shape(receipt["scores"], ["dimensions", "team_mean", "pitch_mean", "overall"])
            shape(scores["dimensions"], TEAM + PITCH)
            for score in scores["dimensions"].values(): shape(score, ["score", "rationale", "evidence_ids"])
            require(receipt.get("schema_version") == 2, "review evidence requires G3 receipt v2")
            self._review_evidence(receipt, state, order, files, acceptance)
            receipt = deepcopy(receipt)
            receipt.pop("review_evidence")
            receipt["schema_version"] = 1
            receipt["findings"] = [item["id"] for item in receipt["findings"]]
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
        require(receipt["verdict"] in ("pass", "fail", "unverifiable") and receipt["next_state"] == order["gate"], "invalid review verdict/state")
        if acceptance: require(receipt["verdict"] == "pass", "gate not passed")
        strings(receipt["findings"], False)
        strings(receipt["unresolved_blockers"], False)
        if acceptance: require(receipt["unresolved_blockers"] == [], "unresolved blockers")
        evidence = receipt["evidence"]
        require(isinstance(evidence, dict) and evidence, "evidence inventory missing")
        for key, path in evidence.items():
            identifier(key)
            string(path)
            require(path in files or (current_evidence and path in order["seal"]["review_inputs"]), "review evidence must be in sealed subject or pinned review packet")
        def refs(value):
            strings(value)
            require(all(key in evidence for key in value), "missing evidence ID")
        predicates = state["policy"]["gates"][order["gate"]]["predicates"]
        shape(receipt["assessments"], predicates)
        for assessment in receipt["assessments"].values():
            shape(assessment, ["outcome", "evidence_ids", "explanation"])
            require(assessment["outcome"] in ("pass", "fail", "unverifiable"), "invalid assessment outcome")
            if acceptance: require(assessment["outcome"] == "pass", "failed or unverifiable predicate")
            refs(assessment["evidence_ids"])
            string(assessment["explanation"])
        require(isinstance(receipt["targets"], list), "targets must be an array")
        if order["gate"] == "G3":
            shape(receipt["render_evidence"], DIAGRAMS if acceptance or not current_evidence else [], DIAGRAMS)
            for evidence_ids in receipt["render_evidence"].values():
                refs(evidence_ids)
            scores = shape(receipt["scores"], ["dimensions", "team_mean", "pitch_mean", "overall"])
            shape(scores["dimensions"], TEAM + PITCH)
            for score in scores["dimensions"].values():
                shape(score, ["score", "rationale", "evidence_ids"])
                require(number(score["score"]) >= (state["policy"]["scoring"]["minimum_dimension"] if acceptance else 1), "dimension below threshold")
                string(score["rationale"])
                refs(score["evidence_ids"])
            team = sum(scores["dimensions"][d]["score"] for d in TEAM) / len(TEAM)
            pitch = sum(scores["dimensions"][d]["score"] for d in PITCH) / len(PITCH)
            overall = sum(scores["dimensions"][d]["score"] for d in TEAM + PITCH) / 12
            for key, calculated in (("team_mean", team), ("pitch_mean", pitch), ("overall", overall)):
                require(math.isclose(number(scores[key]), calculated, rel_tol=0, abs_tol=1e-9), f"incorrect {key}")
            if acceptance: require(overall >= state["policy"]["scoring"]["minimum_overall"], "overall below threshold")
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
            if acceptance: require(found == requested and bool(found), "missing required delivery targets")
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
        shape(record, ["status", "note"], ["target_id", "revision", "evidence", "observed_at"])
        string(record["note"])
        if "observed_at" in record:
            require(timestamp(record["observed_at"]) <= timestamp(utc_now()), "future target readback")
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
            operation.update(status=record["status"], record=resolved, record_generation=state["generation"],
                             recorded_version=expected + 1)
            self._commit(state, expected)
            return {**operation, "replayed": False}


def render_progress(projection, format="json"):
    """Both human views consume this projection only; never reopen the journal."""
    require(format in ("json", "markdown", "html"), "invalid progress format")
    if format == "json": return json.dumps(projection, sort_keys=True, allow_nan=False)
    p = projection
    lines = [("Snapshot", p["snapshot_at"]), ("Status", p["status"])]
    links = []
    if p["status"] == "unverifiable":
        lines.append(("Reason", p["reason"]))
    else:
        current = p["current"]
        lines += [("Run", f'{p["name"]} ({p["run_id"]})'),
                  ("Revision", f'version {p["version"]}; generation {p["generation"]}; {p["revision"]}'),
                  ("Evidence", p["evidence"]["mode"]), ("Requested stop", p["requested_stop"] or "unknown"),
                  ("Gates", f'{p["verified_count"]}/{p["applicable_count"] or "unknown"} verified; counts are not effort'),
                  ("Current stage", current["label"]),
                  ("Responsible role / assigned actor", f'{current["role"] or "unassigned"} / {current["actor"] or "unknown"}'),
                  ("Next action", current["next_action"]),
                  ("Activity", f'{p["activity"]["state"]}; observed {p["activity"]["observed_at"] or "unknown"}'),
                  ("Content review", p["content_review"]),
                  ("Visual review", f'local diagrams: {p["visual_review"]["local_diagrams"]}; document presentation: {p["visual_review"]["document_presentation"]}'),
                  ("Investment appetite", p["investment_appetite"]), ("Checkpoint effort", p["checkpoint_effort"]),
                  ("Registers", f'{p["registers"]["answered"]} answered; {p["registers"]["blocking"]} blocking; {p["registers"]["confirmed"]} confirmed decisions'),
                  ("Freshness", "Local integrity checked; remote freshness unknown. This is an as-of snapshot.")]
        for key, label in (("latest_accepted", "Latest accepted artifact"), ("latest_draft", "Latest draft")):
            item = p[key]
            lines.append((label, f'{item["gate"]}: {item["state"]}' if item else "none"))
            if item:
                url = item["href"]
                require(progress_link(unquote(url)) == url, "unsafe rendered progress link")
                links.append((label, url))
        for blocker in current["blockers"]:
            lines.append(("Hold", f'{blocker["reason"]}; needs {blocker["needed"]}; respondent {blocker["respondent"] or "unassigned"}'))
        for target in p["targets"]:
            lines.append((f'Target {target["surface"]}', f'{target["destination"]}: placement {target["placement"]}; local integrity {target["local_integrity"]}; '
                          f'revision {target["target_revision"] or "unknown"}; last read {target["last_read_at"] or "unknown"}; remote freshness {target["remote_freshness"]}'))
        for warning in p["warnings"]: lines.append(("Missing context", warning))
    # Escape Markdown metacharacters as entities too: source text cannot make links,
    # raw tags or headings. Target labels are never made into external links.
    def md(value):
        value = html.escape(str(value), quote=True)
        return re.sub(r"[\\`*_{\[\]()!|#\r\n]", lambda m: f"&#{ord(m[0])};", value)
    readable = lambda value: str(value).replace('_', ' ')
    names = {g['gate']: g.get('name', g['gate']) for g in p['gates']}
    title, summary = 'Shaping progress', [('Status', p['status'])]
    if p['status'] == 'unverifiable':
        summary.append(('Next action', 'Restore or inspect the run record: '+p['reason']))
    else:
        title = p['name']
        current = p['current']
        stage = names.get(current['gate'], current['label'])
        if p['requested_complete'] is True:
            stage = names.get(p['requested_stop'], stage)
        state = next((g['state'] for g in p['gates'] if g['gate'] == current['gate']),
                     'verified' if p['requested_complete'] is True else 'unverifiable')
        summary = [('Current stage', stage+' — '+readable(state)),
                   ('Next action', current['next_action']),
                   ('Assigned role', current['role'] or 'not recorded'),
                   ('Assigned person or worker', current['actor'] or 'not recorded'),
                   ('Evidence mode', 'Simulation' if p['evidence']['mode'] == 'simulated' else p['evidence']['mode'])]
        for blocker in current['blockers']:
            summary += [('What is blocking', blocker['reason']), ('Needed input', blocker['needed']),
                        ('Needed respondent', blocker['respondent'] or 'unassigned')]
        summary += [('Gate coverage', f'{p["verified_count"]}/{p["applicable_count"] or "unknown"} verified; counts are not effort'),
                    ('Requested result', names.get(p['requested_stop'], 'unknown'))]
    if format == "markdown":
        result = ['# '+md(title), '', 'As of '+md(p['snapshot_at'])+'; not live monitoring.', '']
        result += [f'**{md(label)}:** {md(value)}  ' for label,value in summary]
        result += ["", "## Gate states", "", "| Gate | State |", "| --- | --- |"]
        result += [f'| {md(g["gate"])} {md(g.get("name", ""))} | {md(readable(g["state"]))} |' for g in p["gates"]]
        result += ["", *[f"[{label}]({url})" for label, url in links]]
        result += ["", "<details><summary>Revision and evidence details</summary>", ""]
        result += [f'{md(label)}: {md(value)}  ' for label,value in lines]
        result += ["", "<pre>" + html.escape(json.dumps(p, indent=2, sort_keys=True)) + "</pre></details>"]
        return "\n".join(result) + "\n"
    esc = lambda value: html.escape(str(value), quote=True)
    def tone(state):
        if state == 'verified': return 'verified'
        if state in ('blocked','awaiting_input','stale','changes_requested','unverifiable'): return 'attention'
        if state in ('queued','last_observed_active','review_pending'): return 'working'
        return 'neutral'
    cards = ''.join('<li class="stage '+tone(g['state'])+'"><strong>'+esc(g['gate']+' '+g.get('name',''))
                    +'</strong><span>'+esc(readable(g['state']))+'</span></li>' for g in p['gates'])
    immediate = ''.join('<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>' for label,value in summary)
    outcomes = []
    if p['status'] != 'unverifiable':
        outcomes = [('Content review',readable(p['content_review'])),
                    ('Visual review','Local diagrams: '+readable(p['visual_review']['local_diagrams'])+
                     '; separate document-layout review: '+readable(p['visual_review']['document_presentation'])),
                    ('Activity',readable(p['activity']['state'])+'; last observation '+str(p['activity']['observed_at'] or 'not recorded'))]
        for target in p['targets']:
            outcomes.append(('Target '+target['surface'],target['destination']+
                ': Recorded placement '+readable(target['placement'])+' at revision '+str(target['target_revision'] or 'unknown')+
                '; local evidence integrity '+readable(target['local_integrity'])+
                '; latest target observation '+readable(target['remote_freshness'])+
                '; observed revision '+str(target['observed_target_revision'] or 'unknown')+
                '; last read '+str(target['last_read_at'] or 'not recorded')))
    outcomes_html = ''.join('<dt>'+esc('Shaped content review' if label=='Content review' else label)+'</dt><dd>'+esc(value)+'</dd>' for label,value in outcomes)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+esc(title)+'</title><style>body{font:16px/1.5 system-ui;max-width:72rem;margin:auto;padding:24px;color:#243344;background:#fff}'
            'h1,h2{color:#185abc}h1{font-size:1.9rem;margin-bottom:.35rem}h2{font-size:1.2rem;margin-top:1.5rem}.asof{color:#526171}'
            'dt{font-weight:650}dd{margin:0 0 .6rem;overflow-wrap:anywhere}.summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 28px}'
            '.summary>div:first-child,.summary>div:nth-child(2){grid-column:1/-1}.summary>div:first-child dd{font-size:1.35rem;font-weight:650}'
            '.stages{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;list-style:none;padding:0}.stage{padding:12px;border:1px solid #b7c5d2;border-radius:6px;overflow-wrap:anywhere}'
            '.stage span{display:block;margin-top:7px}.verified{background:#e8f5e9;color:#185c32}.attention{background:#fff3df;color:#754700}.working{background:#e7f0ff;color:#174b87}.neutral{background:#f3f5f7;color:#526171}'
            'details{margin-top:24px;border-top:1px solid #d9e1e8;padding-top:14px}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#185abc}'
            '@media(max-width:700px){body{padding:16px}.summary{grid-template-columns:1fr}.stages{grid-template-columns:1fr}.stage{display:flex;justify-content:space-between;gap:12px}.stage span{margin:0}}</style></head>'
            '<body><main><h1>'+esc(title)+'</h1><p class="asof">As of '+esc(p['snapshot_at'])+' · Not live monitoring</p>'
            '<section id="flow-summary" aria-label="Current work"><h2>What happens next</h2><dl class="summary">'+immediate+'</dl></section>'
            '<h2>Gate states</h2><ol class="stages">'+cards+'</ol>'
            + ('<h2>Review and delivery</h2><dl>'+outcomes_html+'</dl>' if outcomes else '')
            + ''.join(f'<p><a href="{esc(url)}">{esc(label)}</a></p>' for label, url in links)
            + ('<p class="asof">Accepted links open immutable evidence snapshots; draft links open assigned working files.</p>' if links else '')
            + '<details><summary>Revision and evidence details</summary><dl>'+''.join('<dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd>' for label,value in lines)
            + '</dl><pre>' + html.escape(json.dumps(p, indent=2, sort_keys=True))
            + '</pre></details></main></body></html>\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "init": "Initialize controller state with a pinned policy; frame/draft-only targets may be empty.",
        "status": "Verify committed state and report content/delivery separately.",
        "progress": "Read-only, as-of progress projection; no remote or continuous liveness claim.",
        "progress-context": "Record evidence provenance and the requested stopping point in the controller journal.",
        "observe": "Record a timestamped, evidence-bound host observation; never accept a gate.",
        "review-observation": "Bind controller host opening/pixel/answer records after seal; does not authenticate the host.",
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
        if command not in ("init", "status", "progress"):
            p.add_argument("--expected-version", required=True, type=int, help="Exact state version from status")
        if command == "init":
            p.add_argument("--run-id", required=True)
            p.add_argument("--controller", required=True, help="Host-attested label; not authentication")
            p.add_argument("--policy", required=True, type=Path, help="Policy JSON inside run root")
        if command == "prepare": p.add_argument("--spec", required=True, type=Path)
        if command == "progress-context": p.add_argument("--spec", required=True, type=Path)
        if command == "observe": p.add_argument("--record", required=True, type=Path)
        if command == "review-observation":
            p.add_argument("--work-order", required=True)
            p.add_argument("--record", required=True, help="Run-relative controller host observation path")
        if command == "progress":
            p.add_argument("--format", choices=("json", "markdown", "html"), default="json")
            p.add_argument("--as-of", help="UTC snapshot timestamp; defaults to current UTC")
            p.add_argument("--activity-max-age-seconds", type=int, default=900,
                           help="Observation freshness window, not a worker timeout (default: 900)")
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
        elif args.command == "progress":
            result = rt.progress(args.as_of, args.activity_max_age_seconds)
            print(render_progress(result, args.format))
            return 3 if result["status"] == "unverifiable" else 0
        elif args.command == "progress-context": result = rt.progress_context(decode(read_bytes(args.spec)), args.expected_version)
        elif args.command == "observe": result = rt.observe(decode(read_bytes(args.record)), args.expected_version)
        elif args.command == "review-observation": result = rt.review_observation(args.work_order, args.record, args.expected_version)
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
