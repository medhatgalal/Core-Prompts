# Verify numerical comparisons before reporting them

Load this route when Converge itself chooses numerical scores or when the caller
supplies them. Qualitative comparisons do not require invented numerical inputs.
Scores and proposed weights are assumptions unless sources establish otherwise;
calculation accuracy does not turn them into measured outcomes or user preferences.
Hard requirements are eligibility gates, not automatically finite weights.

## Claim and evidence contract

Before publishing a numerical total, difference, range, threshold, probability or
universal sensitivity claim, bind the actual input values, score direction/scale,
weight normalization, assumptions and admissible domain to a reproducible check
or complete explicit symbolic proof. Read the observed result; do not substitute
an intended tool call, plausible arithmetic or sampling for verification. Preserve
counterexamples and ties. A few scenarios prove only those scenarios; a universal
claim requires proof over the entire declared domain. State strict versus inclusive
bounds and tie treatment. Do not extend a proof beyond its input scores/constraints.

For additive higher-is-better linear scores, the bundled standard-library helper
checks point totals and pairwise inequalities on a declared closed bounded simplex.
Other models require a suitable actually available verifier or explicit proof.
If verification is unavailable, unsupported or fails, omit unsupported numerical
certainty and give a qualified qualitative comparison or state the dependent
numerical claim unverified. Do not silently change the model, enlarge the domain,
normalize invalid weights, turn a hard gate into a weight, or repair facts to pass.
Honor the caller's bounded-return/no-write scope and existing review requirements.

Probabilities require a specified probability model/distribution, supported input
sources and actual calculation or simulation evidence, including method, sample
size/seed where applicable and uncertainty. Uniformly sampling a weight region is
not a user-preference distribution or real-world success probability. This helper
computes no probabilities, Monte Carlo simulation or behavioral superiority.

## Portable helper, including read-only stdin use

Run from the effective skill package, without writing an input or output file:

```bash
python3 -B resources/scripts/check_linear.py <<'JSON'
{"schema_version":"ConvergeLinearCheck.v1","criteria":["usefulness","simplicity"],"scores":{"North":[4,2],"South":[2,4]},"weights":["0.75","0.25"],"claim":{"left":"North","relation":">=","right":"South","domain":{"type":"bounded_simplex","lower":["0.5",0],"upper":[1,1]}}}
JSON
```

Use the absolute helper path when cwd must remain your project. `--input FILE`
reads an existing JSON file instead. Python 3.11+ and its standard library suffice;
there are no subprocesses, network calls, package imports, model calls or file
writes. `-B` makes the no-bytecode intent explicit. The helper writes one JSON
result to stdout; exit 0 means a completed check, including a counterexample.
Exit 2 means unsupported/invalid input and certifies no numerical claim.

Input fields are exact: `schema_version`, ordered unique `criteria`, `scores`
mapping alternative names to equally sized arrays, and at least one of `weights`
or `claim`. A claim contains `left`, `relation` (`>` or `>=`), `right`, and `domain`.
The only domain is `{"type":"bounded_simplex","lower":[...],"upper":[...]}`:
all weights sum exactly to one and each lies between its inclusive lower/upper
bounds. Give every bound explicitly. Feasible bounds satisfy
`0 <= lower[i] <= upper[i] <= 1` and `sum(lower) <= 1 <= sum(upper)`.
Point weights must separately be nonnegative and sum exactly to one; they do not
need to belong to a separately tested claim domain. Input supports 1–32 criteria,
2–32 named alternatives and at most 65536 bytes. Unknown fields, duplicate keys,
nonfinite values, wrong dimensions and infeasible domains are rejected.

Use integers, fixed-decimal JSON numbers/strings or rational strings such as
`"1/3"`. They are interpreted exactly, without binary floating-point rounding or
implicit normalization. Scientific notation and number tokens longer than 128
characters are unsupported. Scores may be negative and must already use the
intended common utility scale/direction; this helper does not infer units or
convert costs, missing data, ordinal judgments or eligibility rules.

The example gives exact totals North `7/2`, South `5/2`. The inclusive claim
holds over its declared domain, with a tie at weights `(1/2,1/2)`. Changing its
relation to `>` produces that tie as a counterexample. Neither conclusion applies
to arbitrary weights outside the domain or different source scores.

## Reading the certificate

Point output includes exact rational totals and ranking groups that retain ties.
Claim output includes the exact normalized domain, minimum and maximum of
`score(left)-score(right)`, attaining weight vectors and both alternatives' totals.
It reports `proved_over_declared_domain` only when the minimum is nonnegative for
`>=`, or strictly positive for `>`; otherwise the minimum witness is a counterexample.
The raw-input SHA-256 binds the actual CLI input, not its provenance or correctness.

For coefficients `c[i]` and bounds `l[i],u[i]`, start at all lower bounds and
allocate the remaining mass to increasing coefficients up to each capacity.
An exchange from a higher to a lower unsaturated coefficient cannot increase the
objective, so this greedy allocation minimizes the linear objective. Exact
rational arithmetic avoids rounded threshold decisions. With `r=1-sum(l)` and
a reported dual value lambda, every feasible vector has objective at least:

`sum(c*l) + lambda*r + sum(min(0,c-lambda)*(u-l))`.

The helper checks equality of that bound with its witness value. Maximum uses the
same proof on negated coefficients, so the negative-maximum certificate concerns
`-(score(left)-score(right))`. This covers only independent closed interval bounds
plus sum-one. Coupled constraints, open bounds, nonlinear utilities, changing
scores and probabilistic models are unsupported. Do not approximate them with a
box and present its result as the original claim.
