# Phase 1 Baseline Design

This phase preserves the original research design exactly: estimate the effect of state minimum-wage increases on county-level food-service employment using QCEW data and a border-county-pair DiD/event-study validation pipeline.

The Phase 1 deliverables are:

- `event_study_coefficients.csv`
- `parallel_trends_preperiod.csv`
- `border_pair_did.csv`
- `pyfixest_lpdid.csv`
- `treated_vs_synthetic.png`
- `synthetic_placebos.csv`
- `iv_2sls.csv`
- `iv_first_stage.txt`

Phase 1 is intentionally conservative. It validates the causal pipeline and reports weak or fragile inference honestly, especially the two-state cluster limitation in the NJ/PA validation case.
