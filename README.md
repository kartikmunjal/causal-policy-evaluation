# causal-policy-evaluation

Author: Kartik Munjal

## Research Question

What is the causal effect of state minimum-wage increases on county-level food-service employment in the United States?

The primary validation case starts with New Jersey's July 1, 2019 minimum-wage increase and Pennsylvania border counties as controls. The scaled design is a staggered border-county-pair panel across audited minimum-wage changes in multiple states.

## Pre-Specified Primary Design

Before reporting estimates, the primary regression is specified as:

`log(employment_cpt) = alpha_c + lambda_t + gamma_p + sum_k beta_k [treated_c x 1(event_time_ct = k)] + epsilon_cpt`

where `c` is county, `t` is year, and `p` is the border-county pair. The omitted event-time bin is `k = -1`. The outcome is QCEW annual average employment in NAICS 722, food services and drinking places. Standard errors are clustered at the state level. Event-study leads are reported as explicit parallel-trends evidence.

For staggered adoption, the repo is set up to use a modern staggered-DiD workflow with `pyfixest`, with an optional Callaway and Sant'Anna ATT(g,t) wrapper for users who install a compatible `differences` environment. Naive TWFE is not used as the final staggered-DiD estimator. A single-cohort border-pair DiD is included only to validate the first treated-state pipeline.

The national builder fails closed: it requires Census cross-state county adjacency and a verified policy table with source URLs before it will construct a scaled panel.

## Phase Structure

Phase 1 is the initial approach from the first prompt: QCEW food-service employment, NJ/PA border-county-pair validation, event-study leads/lags, modern DiD output, synthetic-control robustness, placebo inference, secondary IV, README/report/tests, and MIT license. See `report/PHASE_1_BASELINE.md`.

Phase 2 is the research-grade infrastructure pass after Phase 1: audited policy schema, Census border-pair construction, national-panel builder, fail-closed policy validation, diagnostics, joint pretrend tests, placebo policy years, wild-cluster bootstrap, reproducibility manifest, Makefile, and national scale-up hooks. These additions strengthen the original design without changing the original estimand.

Phase 3 is the economics and data-science contribution layer. It asks whether the average employment estimate hides more interesting economic adjustment. It tests:

- minimum-wage bite and dose response
- adjustment margins: establishments, employment per establishment, and average pay
- heterogeneity by baseline establishment scale and pre-period county employment growth
- whether border-spillover tests are identified in the available sample
- a compact specification curve across outcomes, windows, and weighting choices

See `report/PHASE_3_ECONOMIC_EXTENSIONS.md`.

## Identifying Assumptions

Treated and control border counties must have parallel counterfactual employment trends absent the policy change. Border counties should share local economic shocks, and the treatment should not cause large cross-border spillovers that contaminate controls. Policy timing should not be driven by county-specific food-service labor-market shocks.

## Data Provenance

Free public data sources:

- BLS QCEW county annual files, NAICS 722, ownership code 5.
- BLS CES/LAUS and FRED for macro and labor-market controls in the scaled pipeline.
- Census ACS for baseline industry shares in the shift-share IV design.
- DOL/state minimum-wage histories for policy dates, cached in `data/raw/minimum_wage_policy_dates.csv`.
- Census county adjacency for cross-state border-pair construction.

Fetch scripts cache raw files under `data/raw/` and write provenance metadata with fetch date, vintage, URL, and cleaning notes. API keys, if used for FRED or Census endpoints, should be supplied as environment variables such as `FRED_API_KEY` and `CENSUS_API_KEY`.

## Results

This repo starts with a single treated state and its control border counties to validate the pipeline before scaling. Results are not hard-coded into the README. After running the pipeline, generated tables and figures appear in `report/`.

Required outputs:

- `report/event_study.png`
- `report/event_study_coefficients.csv`
- `report/parallel_trends_preperiod.csv`
- `report/pyfixest_lpdid.csv`
- `report/treated_vs_synthetic.png`
- `report/synthetic_placebos.csv`
- `report/iv_2sls.csv`
- `report/iv_first_stage.txt`
- `report/balance_table.csv`
- `report/raw_trends.csv`
- `report/joint_pretrend_test.csv`
- `report/placebo_policy_years.csv`
- `report/wild_cluster_bootstrap.csv`
- `report/manifest.json`
- `report/phase2_margin_decomposition.csv`
- `report/phase2_bite_dose_response.csv`
- `report/phase2_heterogeneity.csv`
- `report/phase2_spillover_identification.csv`
- `report/phase2_specification_curve.csv`
- `report/phase2_specification_curve.png`

## Robustness Summary

The robustness plan includes synthetic control for the treated county path, donor weights, placebo/permutation inference, placebo policy years, joint pre-trend tests, wild-cluster bootstrap diagnostics, leave-one-state-out hooks, and raw-trend/balance tables. The secondary IV design constructs a Bartik-style shift-share instrument for local labor demand and estimates 2SLS with `linearmodels`, reporting first-stage strength.

RDD is skipped unless a genuine sharp public-data eligibility threshold is identified. No discontinuity is fabricated.

## Threats to Validity

Main risks are policy spillovers across state borders, nonparallel pre-trends, local shocks not absorbed by border-pair and time effects, other contemporaneous state policies, pandemic-era structural breaks, county industry-composition changes, and QCEW suppression or reporting noise.

## Reproduce

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python scripts/run_all.py --python .venv/bin/python
```

Run only the Phase 3 economics extensions:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_research_extensions.py
PYTHONPATH=src .venv/bin/python scripts/render_report.py
```

National scale-up:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_border_pairs.py
PYTHONPATH=src .venv/bin/python scripts/validate_policy_table.py
PYTHONPATH=src .venv/bin/python scripts/build_national_panel.py --start-year 2015 --end-year 2023
PYTHONPATH=src .venv/bin/python scripts/run_event_study.py --panel data/processed/national_border_qcew_food_service_panel.parquet
PYTHONPATH=src .venv/bin/python scripts/run_did.py --panel data/processed/national_border_qcew_food_service_panel.parquet
PYTHONPATH=src .venv/bin/python scripts/run_diagnostics.py --panel data/processed/national_border_qcew_food_service_panel.parquet
```

Offline smoke check:

```bash
PYTHONPATH=src python3 scripts/fetch_data.py --smoke
PYTHONPATH=src python3 scripts/run_event_study.py --smoke
PYTHONPATH=src python3 scripts/run_did.py --smoke --skip-cs
PYTHONPATH=src python3 scripts/run_synthetic_control.py --smoke
pytest -q
```

Make targets:

```bash
make smoke PYTHON=.venv/bin/python
make validation PYTHON=.venv/bin/python
make test PYTHON=.venv/bin/python
```

## License

MIT
