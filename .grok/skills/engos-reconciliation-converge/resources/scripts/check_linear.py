#!/usr/bin/env python3
"""Exact linear scores and pairwise claims on a declared bounded simplex."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_INPUT_BYTES = 65536


class ContractError(ValueError):
    pass


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or set(value) - set(required) - set(optional):
        raise ContractError("missing or unsupported object fields")


def rational(value):
    if type(value) not in (str, int):
        raise ContractError("numbers must be exact integers, fixed decimals or rational strings")
    text = str(value)
    if len(text) > 128 or not re.fullmatch(r"-?(?:(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)|[0-9]+/[0-9]+)", text):
        raise ContractError("unsupported number; use a fixed decimal or numerator/denominator")
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise ContractError("invalid rational number") from exc


def vector(value, length):
    if not isinstance(value, list) or len(value) != length:
        raise ContractError("vector length must match criteria")
    return [rational(x) for x in value]


def dot(a, b):
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def minimize(coefficients, lower, upper):
    """Greedy box-simplex optimum, with an exact matching dual lower bound."""
    weights = lower.copy()
    remaining = 1 - sum(lower)
    order = sorted(range(len(coefficients)), key=lambda i: (coefficients[i], i))
    dual_lambda = coefficients[order[0]]
    for i in order:
        amount = min(remaining, upper[i] - lower[i])
        if amount:
            weights[i] += amount
            remaining -= amount
            dual_lambda = coefficients[i]
        if not remaining:
            break
    if remaining:
        raise ContractError("infeasible weight domain")
    value = dot(coefficients, weights)
    # For y=w-l and sum(y)=r: c.y >= lambda*r + sum(min(0,c-lambda)*capacity).
    bound = (dot(coefficients, lower) + dual_lambda * (1 - sum(lower))
             + sum((min(Fraction(0), c - dual_lambda) * (hi - lo)
                    for c, lo, hi in zip(coefficients, lower, upper)), Fraction(0)))
    if value != bound:
        raise ContractError("internal certificate mismatch")
    return value, weights, {"dual_lambda": str(dual_lambda), "dual_lower_bound": str(bound)}


def check(data):
    fields(data, {"schema_version", "criteria", "scores"}, {"weights", "claim"})
    if data["schema_version"] != "ConvergeLinearCheck.v1":
        raise ContractError("unsupported input schema")
    criteria = data["criteria"]
    if (not isinstance(criteria, list) or not 1 <= len(criteria) <= 32
            or any(not isinstance(x, str) or not x.strip() or len(x) > 128 for x in criteria)
            or len(set(criteria)) != len(criteria)):
        raise ContractError("criteria must be 1 to 32 unique nonempty names")
    n = len(criteria)
    raw_scores = data["scores"]
    if (not isinstance(raw_scores, dict) or not 2 <= len(raw_scores) <= 32
            or any(not isinstance(k, str) or not k.strip() or len(k) > 128 for k in raw_scores)):
        raise ContractError("scores must name 2 to 32 alternatives")
    scores = {key: vector(value, n) for key, value in raw_scores.items()}
    if "weights" not in data and "claim" not in data:
        raise ContractError("supply point weights, a scoped claim, or both")
    result = {"schema_version": "ConvergeLinearResult.v1", "status": "checked",
              "model": {"criteria": criteria, "scores": {k: list(map(str, v)) for k, v in scores.items()}},
              "scope": "Declared higher-is-better linear scores only; no preference, empirical or probability evidence."}
    if "weights" in data:
        weights = vector(data["weights"], n)
        if any(w < 0 for w in weights) or sum(weights) != 1:
            raise ContractError("point weights must be nonnegative and sum exactly to one")
        totals = {key: dot(row, weights) for key, row in scores.items()}
        result["point"] = {"weights": list(map(str, weights)),
                           "totals": {k: str(v) for k, v in totals.items()},
                           "ranking_with_ties": [sorted(k for k, v in totals.items() if v == score)
                                                 for score in sorted(set(totals.values()), reverse=True)]}
    if "claim" in data:
        claim = data["claim"]
        fields(claim, {"left", "relation", "right", "domain"})
        left, right, relation = claim["left"], claim["right"], claim["relation"]
        if (not isinstance(left, str) or not isinstance(right, str)
                or left not in scores or right not in scores or relation not in (">", ">=")):
            raise ContractError("claim needs known alternatives and relation > or >=")
        domain = claim["domain"]
        fields(domain, {"type", "lower", "upper"})
        if domain["type"] != "bounded_simplex":
            raise ContractError("only a closed bounded_simplex domain is supported")
        lower, upper = vector(domain["lower"], n), vector(domain["upper"], n)
        if any(not 0 <= lo <= hi <= 1 for lo, hi in zip(lower, upper)) or not sum(lower) <= 1 <= sum(upper):
            raise ContractError("infeasible or invalid bounded-simplex domain")
        coefficients = [a - b for a, b in zip(scores[left], scores[right])]
        minimum, argmin, certificate = minimize(coefficients, lower, upper)
        negative_max, argmax, max_certificate = minimize([-x for x in coefficients], lower, upper)
        holds = minimum > 0 if relation == ">" else minimum >= 0
        def witness(weights):
            return {"weights": list(map(str, weights)), "left_total": str(dot(scores[left], weights)),
                    "right_total": str(dot(scores[right], weights))}
        result["claim"] = {"left": left, "relation": relation, "right": right,
                           "domain": {"type": "bounded_simplex", "lower": list(map(str, lower)),
                                      "upper": list(map(str, upper)), "sum": "1"},
                           "outcome": "proved_over_declared_domain" if holds else "counterexample",
                           "minimum_gap": str(minimum), "maximum_gap": str(-negative_max),
                           "minimum_witness": witness(argmin), "maximum_witness": witness(argmax),
                           "minimum_certificate": certificate,
                           "negative_maximum_certificate": max_certificate,
                           "certificate_scope": "Exact linear min/max only on the stated closed bounded simplex."}
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("duplicate JSON object key")
        result[key] = value
    return result


def reject_constant(_value):
    raise ContractError("nonfinite JSON number")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON input file; omit to read stdin without creating a file")
    args = parser.parse_args(argv)
    try:
        if args.input:
            with Path(args.input).open("rb") as stream:
                raw = stream.read(MAX_INPUT_BYTES + 1)
        else:
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ContractError("input exceeds 65536 bytes")
        data = json.loads(raw.decode("utf-8"), parse_int=str, parse_float=str, parse_constant=reject_constant,
                          object_pairs_hook=unique_object)
        result = check(data)
        result["input_sha256"] = hashlib.sha256(raw).hexdigest()
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, ContractError) else "input could not be read as supported JSON"
        print(json.dumps({"schema_version": "ConvergeLinearResult.v1", "status": "unsupported_or_invalid",
                          "error": message}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
