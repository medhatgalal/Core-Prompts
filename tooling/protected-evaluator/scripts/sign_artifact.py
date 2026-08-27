#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from core_prompts_eval.attestations import signature_message
from core_prompts_eval.contracts import artifact_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign one immutable public evaluation artifact.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--trust-root", type=Path, required=True)
    parser.add_argument("--purpose", required=True)
    args = parser.parse_args()

    if args.output.exists():
        parser.error("output path already exists")
    if os.stat(args.private_key).st_mode & 0o077:
        parser.error("private key file must not be group- or world-readable")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "signature" in payload:
        parser.error("input must be one unsigned JSON object")
    trust_root = json.loads(args.trust_root.read_text(encoding="utf-8"))
    private_raw = base64.b64decode(args.private_key.read_text(encoding="ascii").strip(), validate=True)
    private = Ed25519PrivateKey.from_private_bytes(private_raw)
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    if base64.b64encode(public_raw).decode("ascii") != trust_root.get("public_key_base64"):
        parser.error("private key does not match the reviewed trust root")
    if args.purpose not in trust_root.get("purposes", []):
        parser.error("trust root does not authorize the requested purpose")
    signature = private.sign(signature_message(payload))
    signed = {
        **payload,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": trust_root["key_id"],
            "purpose": args.purpose,
            "signed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload_sha256": artifact_hash(payload),
            "value_base64": base64.b64encode(signature).decode("ascii"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(descriptor, (json.dumps(signed, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
