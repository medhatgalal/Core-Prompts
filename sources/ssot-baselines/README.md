# SSOT Baseline Sources

This directory is the canonical source library for fidelity baselines used by UAC quality judging.

## Purpose
- preserve the strongest known prompt-body source for each capability inside the repo
- avoid relying on git commit SHAs as the operational baseline selector
- give future UAC `judge` and `apply` runs a durable source snapshot even in workspace copies without `.git`

## Structure
- `index.json`: machine-readable baseline catalog
- `<slug>/baseline.md`: canonical baseline prompt source for that capability

## Rules
- baseline selection must read `index.json` and `baseline.md` first
- commit hashes may be retained only as lineage evidence in `historical_proof`
- new or newly imported capabilities should materialize a baseline source here before or during `apply`
- baseline sources are prompt-body fidelity oracles, not generated surfaces

## Maintenance
- bootstrap or refresh materialized baseline sources with `scripts/materialize-baseline-sources.py`
- when a capability gains a stronger prompt-body source, update the baseline source snapshot and its metadata together
- do not replace a curated baseline with a weaker normalized or flattened SSOT body
