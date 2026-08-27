#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

ALLOWED_PURPOSES = {
    "adapter_conformance",
    "candidate_submission",
    "sealed_bundle",
    "judge_qualification",
    "execution_receipt",
    "global_token_ledger",
    "promotion_verdict",
}


def _exclusive_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.write(descriptor, data)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a protected Ed25519 evaluator key pair.")
    parser.add_argument("--private-key-out", type=Path, required=True)
    parser.add_argument("--trust-root-out", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--purpose", action="append", choices=sorted(ALLOWED_PURPOSES), required=True)
    parser.add_argument("--not-before", required=True)
    parser.add_argument("--expires-at", required=True)
    args = parser.parse_args()

    if args.private_key_out.exists() or args.trust_root_out.exists():
        parser.error("output paths must not already exist")
    try:
        not_before = dt.datetime.fromisoformat(args.not_before.replace("Z", "+00:00"))
        expires_at = dt.datetime.fromisoformat(args.expires_at.replace("Z", "+00:00"))
    except ValueError:
        parser.error("valid RFC 3339 timestamps are required")
    if not_before.tzinfo is None or expires_at.tzinfo is None or expires_at <= not_before:
        parser.error("expires-at must be timezone-aware and later than not-before")
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    trust_root = {
        "schema_version": "ProtectedTrustRoot.v1",
        "key_id": args.key_id,
        "algorithm": "Ed25519",
        "public_key_base64": base64.b64encode(public_raw).decode("ascii"),
        "purposes": sorted(set(args.purpose)),
        "not_before": args.not_before,
        "expires_at": args.expires_at,
        "revoked_at": None,
    }
    _exclusive_write(args.private_key_out, base64.b64encode(private_raw) + b"\n", 0o600)
    try:
        _exclusive_write(
            args.trust_root_out,
            (json.dumps(trust_root, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            0o644,
        )
    except Exception:
        args.private_key_out.unlink(missing_ok=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
