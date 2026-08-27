#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys


def main() -> int:
    request = json.load(sys.stdin)
    forbidden = {"case_id", "arm", "repetition", "seed"}.intersection(request)
    if forbidden:
        raise ValueError(f"blinding fields leaked into adapter request: {sorted(forbidden)}")
    model = str(request["resolved_model_identifier"])
    output = "fixture:" + hashlib.sha256(
        f"{request['trial_id']}\0{request['artifact_sha256']}".encode("utf-8")
    ).hexdigest()
    payload = {
        "schema_version": "EvalAdapterResponse.v1",
        "output": output,
        "resolved_model_identifier": model,
        "model_version": str(request["model_version"]),
        "usage": {"raw": 8, "cached": 0, "billed": 8},
    }
    json.dump(payload, sys.stdout, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
