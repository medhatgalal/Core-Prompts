#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema

from core_prompts_eval.attestations import validate_signed_attestation


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a candidate-hash submission.")
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--trust-root", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.submission.read_text(encoding="utf-8"))
    trust_root = json.loads(args.trust_root.read_text(encoding="utf-8"))
    schema_path = args.schema
    if schema_path is None:
        raise SystemExit("--schema must identify the reviewed CandidateSubmission.v1 schema")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)
    validate_signed_attestation(
        payload,
        trust_root=trust_root,
        expected_purpose="candidate_submission",
    )
    print(f"candidate submission valid: {payload['submission_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
