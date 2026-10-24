"""Exact oracles for Converge's bounded linear model; no native/model calls."""
from fractions import Fraction as F
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "sources/capability-resources/engos-reconciliation-converge"
spec = importlib.util.spec_from_file_location("converge_linear", RESOURCES / "scripts/check_linear.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def model(scores=None, weights=None, lower=None, upper=None, relation=">="):
    scores = scores or {"A": [1, 2, 3, 4], "B": [5, 4, 4, 3]}
    n = len(next(iter(scores.values())))
    result = {"schema_version": "ConvergeLinearCheck.v1", "criteria": [f"c{i}" for i in range(n)], "scores": scores}
    if weights is not None: result["weights"] = weights
    if lower is not None:
        result["claim"] = {"left": list(scores)[1], "relation": relation, "right": list(scores)[0],
                           "domain": {"type": "bounded_simplex", "lower": lower, "upper": upper or [1] * n}}
    return result


def test_original_point_totals_and_two_retained_counterexamples():
    assert m.check(model(weights=[".45", ".25", ".20", ".10"]))["point"]["totals"] == {"A": "39/20", "B": "87/20"}
    for weights, expected in [([".15", 0, 0, ".85"], {"A": "71/20", "B": "33/10"}),
                              ([".01", ".01", ".30", ".68"], {"A": "73/20", "B": "333/100"})]:
        out = m.check(model(weights=weights))["point"]
        assert out["totals"] == expected
        assert out["ranking_with_ties"] == [["A"], ["B"]]


def test_original_false_universal_thresholds_return_valid_counterexamples():
    for lower, upper in [(["0.15", 0, 0, 0], [1, 1, 1, 1]),
                          ([0, 0, 0, 0], [1, 1, 1, "0.75"])]:
        out = m.check(model(lower=lower, upper=upper))["claim"]
        assert out["outcome"] == "counterexample"
        weights = list(map(F, out["minimum_witness"]["weights"]))
        assert sum(weights) == 1
        assert all(F(lo) <= w <= F(hi) for w, lo, hi in zip(weights, lower, upper))
        assert F(out["minimum_witness"]["left_total"]) < F(out["minimum_witness"]["right_total"])


def test_tie_and_strict_inequality_have_different_verdicts():
    data = model({"South": [2, 4], "North": [4, 2]}, weights=["1/2", "1/2"], lower=["1/2", 0])
    out = m.check(data)
    assert out["point"]["ranking_with_ties"] == [["North", "South"]]
    assert out["claim"]["outcome"] == "proved_over_declared_domain"
    assert out["claim"]["minimum_gap"] == "0"
    data["claim"]["relation"] = ">"
    assert m.check(data)["claim"]["outcome"] == "counterexample"
    data["claim"]["domain"]["lower"] = ["3/4", 0]
    assert m.check(data)["claim"]["outcome"] == "proved_over_declared_domain"


def test_general_alternatives_signed_scores_fixed_domain_and_exact_decimal():
    data = model({"red": ["-1/3", "0.1"], "blue": ["2/3", "0.1"], "green": ["5/3", "-2.5"]},
                 weights=["1/3", "2/3"], lower=["1/3", "2/3"], upper=["1/3", "2/3"])
    out = m.check(data)
    assert out["point"]["totals"]["red"] == "-2/45"
    assert out["point"]["ranking_with_ties"] == [["blue"], ["red"], ["green"]]
    assert out["claim"]["minimum_gap"] == out["claim"]["maximum_gap"] == "1/3"
    data["claim"]["left"] = "green"
    assert m.check(data)["claim"]["outcome"] == "counterexample"


def test_min_max_and_dual_certificate_match_independent_exhaustive_lattice():
    rng = random.Random(714)
    for _ in range(20):
        scores = {"before": [rng.randint(-5, 5) for _ in range(3)], "after": [rng.randint(-5, 5) for _ in range(3)]}
        lower = [F(0), F(1, 4), F(0)]
        upper = [F(3, 4), F(3, 4), F(1, 2)]
        data = model(scores, lower=list(map(str, lower)), upper=list(map(str, upper)))
        out = m.check(data)["claim"]
        feasible = [tuple(F(x, 4) for x in point) for point in itertools.product(range(5), repeat=3)
                    if sum(point) == 4 and all(lo <= F(x, 4) <= hi for x, lo, hi in zip(point, lower, upper))]
        # Independent enumeration covers every vertex because all bounds are quarters.
        gaps = [sum(w * (b-a) for w, a, b in zip(point, scores["before"], scores["after"])) for point in feasible]
        assert F(out["minimum_gap"]) == min(gaps)
        assert F(out["maximum_gap"]) == max(gaps)
        assert F(out["minimum_certificate"]["dual_lower_bound"]) == min(gaps)
        assert F(out["negative_maximum_certificate"]["dual_lower_bound"]) == -max(gaps)


@pytest.mark.parametrize("weights", [[0, 0, 0, 0], [1, 1, 0, 0], [-1, 1, 1, 0], [True, 0, 0, 0],
                                    ["NaN", 0, 0, 1], ["1/0", 0, 0, 1], ["1e3", 0, 0, 0], [1, 0], [0.1, 0, 0, "0.9"]])
def test_invalid_point_weights_are_not_normalized_or_silently_accepted(weights):
    with pytest.raises(m.ContractError): m.check(model(weights=weights))


@pytest.mark.parametrize("lower,upper", [([0, 0, 0, 0], [0, 0, 0, 0]),
    ([1, 1, 0, 0], [1, 1, 1, 1]), ([-1, 0, 0, 0], [1, 1, 1, 1]),
    ([0, 0, 0, 0], [2, 1, 1, 1]), (["1/2", 0, 0, 0], [0, 1, 1, 1])])
def test_invalid_or_infeasible_domains_produce_no_vacuous_proof(lower, upper):
    with pytest.raises(m.ContractError): m.check(model(lower=lower, upper=upper))


@pytest.mark.parametrize("fault", ["coupled", "open-domain", "probability", "unknown-alternative", "missing-domain", "score-shape", "duplicate-criterion"])
def test_unsupported_model_features_fail_closed(fault):
    data = model(lower=[0, 0, 0, 0])
    if fault == "coupled": data["claim"]["domain"]["constraints"] = ["w0+w1>=0.5"]
    elif fault == "open-domain": data["claim"]["domain"]["type"] = "open_simplex"
    elif fault == "probability": data["probability"] = "0.9"
    elif fault == "unknown-alternative": data["claim"]["left"] = "invented"
    elif fault == "missing-domain": del data["claim"]["domain"]
    elif fault == "score-shape": data["scores"]["B"] = [1]
    else: data["criteria"] = ["x"] * 4
    with pytest.raises(m.ContractError): m.check(data)


def test_relocated_stdin_cli_has_exact_decimal_semantics_and_no_local_writes(tmp_path):
    helper = tmp_path / "check_linear.py"
    helper.write_bytes((RESOURCES / "scripts/check_linear.py").read_bytes())
    raw = json.dumps(model({"one": [1, 0], "two": [0, 1]}, weights=["0.1", "0.9"])).replace('"0.1"', '0.1').replace('"0.9"', '0.9').encode()
    result = subprocess.run([sys.executable, "-B", str(helper)], input=raw, capture_output=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["point"]["totals"] == {"one": "1/10", "two": "9/10"}
    assert list(tmp_path.iterdir()) == [helper]
    assert not result.stderr
    for raw in [b'{"schema_version":"x","schema_version":"y"}', b'{"weights":NaN}', b'x' * 65537]:
        result = subprocess.run([sys.executable, "-B", str(helper)], input=raw, capture_output=True, cwd=tmp_path)
        assert result.returncode == 2
        assert json.loads(result.stdout)["status"] == "unsupported_or_invalid"


def test_numerical_route_is_lazy_and_self_contained():
    from intent_pipeline.capability_resources import load_resource_bundle
    numeric = load_resource_bundle(RESOURCES, "numerical-check")
    assert {r["path"] for r in numeric["resources"]} == {"references/numerical-checks.md", "scripts/check_linear.py"}
    old = load_resource_bundle(RESOURCES, "source-conflict")
    assert {r["path"] for r in old["resources"]} == {"examples/source-conflict.md"}


def test_oversized_integer_token_returns_structured_error_without_traceback(tmp_path):
    raw = json.dumps(model({"one": ["OVERSIZED", 0], "two": [0, 1]}, weights=[0, 1])).replace('"OVERSIZED"', "7" * 5000).encode()
    assert len(raw) < m.MAX_INPUT_BYTES
    result = subprocess.run([sys.executable, "-B", str(RESOURCES / "scripts/check_linear.py")],
                            input=raw, capture_output=True, cwd=tmp_path)
    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["status"] == "unsupported_or_invalid"
    assert output["error"] == "unsupported number; use a fixed decimal or numerator/denominator"
    assert result.stderr == b""
