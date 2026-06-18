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

Phase 4 moves the project from validation to a true national research sample. It fetches state minimum-wage time series from FRED/DOL, detects actual policy increases, and writes a verified cohort table that can feed the national Census border-county panel.

Phase 4 current national outputs are summarized in `report/PHASE_4_NATIONAL_PANEL.md`.

Phase 5 adds a connected labor-demand research design: a China-shock shift-share IV at the commuting-zone level. It maps HS6 trade flows to NAICS industries, combines them with baseline QCEW industry employment shares, instruments US import exposure with import growth to other high-income countries, reports first-stage strength, and writes Rotemberg-style industry influence weights. See `report/PHASE_5_TRADE_SHIFT_SHARE.md`.

Phase 6 adds a spatial RDD robustness scaffold for state-border policy jumps. It requires a documented `signed_distance_km` running variable from public geometry and refuses to manufacture a discontinuity from treatment status. See `report/PHASE_6_SPATIAL_RDD.md`.

A price-index construction project is best kept as a standalone follow-on repo because it is a measurement contribution, not a direct causal estimate in this minimum-wage border design.

## Identifying Assumptions

Treated and control border counties must have parallel counterfactual employment trends absent the policy change. Border counties should share local economic shocks, and the treatment should not cause large cross-border spillovers that contaminate controls. Policy timing should not be driven by county-specific food-service labor-market shocks.

## Data Provenance

Free public data sources:

- BLS QCEW county annual files, NAICS 722, ownership code 5.
- BLS CES/LAUS and FRED for macro and labor-market controls in the scaled pipeline.
- Census ACS for baseline industry shares in the shift-share IV design.
- DOL/state minimum-wage histories for policy dates, cached in `data/raw/minimum_wage_policy_dates.csv`.
- Census county adjacency for cross-state border-pair construction.
- Trade-shock extension inputs: public import data by HS6/year, Pierce-Schott style HS-to-NAICS concordances, and Dorn commuting-zone crosswalks.
- Spatial RDD extension inputs: public county geometry and border-distance construction with signed distance to the relevant state border.

Fetch scripts cache raw files under `data/raw/` and write provenance metadata with fetch date, vintage, URL, and cleaning notes. The FRED minimum-wage fetch uses public CSV graph endpoints and does not require an API key. Other FRED or Census endpoints, if added later, should use environment variables such as `FRED_API_KEY` and `CENSUS_API_KEY`.

## Results

This repo starts with a single treated state and its control border counties to validate the pipeline before scaling. Results are not hard-coded into the README. After running the pipeline, generated tables and figures appear in `report/`.

Current validation snapshot from the cached 2015-2023 BLS QCEW NJ/PA border-county panel:

- Sample: 90 county-pair-year rows.
- Baseline single-cohort DiD employment estimate: -0.0286 log points.
- Pyfixest LPDID validation estimate: 0.0038 log points.
- Event-study pre-period leads: 0.0137, 0.0322, and 0.0343 log points for event years -4, -3, and -2. This is not clean parallel-trends evidence.
- Margin decomposition: employment -0.0286, establishments 0.0021, employment per establishment -0.0307, average annual pay 0.0312 log points.
- Bite/dose-response estimates: employment -0.0267, employment per establishment -0.0300, average annual pay 0.0285.
- Synthetic-control Burlington County post-period treated-minus-synthetic gap: -0.1144 log points; placebo p-value 0.889.
- Secondary IV estimate: 2.1004; first-stage partial F-statistic 52.046 in the validation sample.
- Border-spillover test: not identified in the current validation panel because there are no interior or unexposed comparison controls.

These are validation findings, not final national estimates. The two-state NJ/PA panel is useful for surfacing mechanisms and checking code, but publishable inference requires the audited national panel with enough state clusters.

Current national snapshot using FRED/DOL policy timing, Census county adjacency, and cached 2015-2023 BLS QCEW data:

- Policy input: 210 FRED/DOL state minimum-wage increases; 414 state-year minimum-wage-rate rows.
- Missing FRED state series recorded for AL, LA, MS, SC, and TN.
- Border design input: 1,306 Census cross-state border-county pairs.
- National panel: 23,219 border-county-pair-year rows.
- Cluster count: 48 states; state-cluster warning is false.
- National event-study estimates: -4 lead 0.0408; -3 lead 0.0700; -2 lead 0.0891; event year 0 0.0575; +1 -0.1016; +2 -0.0835; +3 -0.0160.
- National pyfixest LPDID estimate: 0.0741 log points, SE 0.0738, p = 0.325.
- National margin decomposition: employment -0.0649, establishments -0.0049, employment per establishment -0.2202, average annual pay 0.0199 log points.
- National bite/dose-response estimates: employment 0.0014, employment per establishment 0.0600, average annual pay -0.0075.
- Several state-clustered SEs remain unstable or undefined in high-dimensional specs; the report preserves those missing SEs rather than manufacturing precision.

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
- `report/national_event_study_coefficients.csv`
- `report/national_pyfixest_lpdid.csv`
- `report/national_margin_decomposition.csv`
- `report/national_bite_dose_response.csv`
- `report/national_specification_curve.png`
- `report/shift_share_iv.csv`
- `report/shift_share_first_stage.txt`
- `report/shift_share_rotemberg_weights.csv`
- `report/shift_share_dropped_us_hs6.csv`
- `report/shift_share_dropped_instrument_hs6.csv`
- `report/spatial_rdd_estimates.csv`
- `report/spatial_rdd_diagnostics.csv`
- `report/spatial_rdd_identification_notes.csv`

## Robustness Summary

The robustness plan includes synthetic control for the treated county path, donor weights, placebo/permutation inference, placebo policy years, joint pre-trend tests, wild-cluster bootstrap diagnostics, leave-one-state-out hooks, and raw-trend/balance tables. The secondary IV design constructs a Bartik-style shift-share instrument for local labor demand and estimates 2SLS with `linearmodels`, reporting first-stage strength.

The trade-shock extension adds concordance-loss audits and Rotemberg-style industry influence weights so the identifying variation can be inspected. The spatial RDD extension is a robustness check only and requires a real signed distance-to-border variable.

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
PYTHONPATH=src .venv/bin/python scripts/fetch_policy_fred.py --start-year 2015 --end-year 2023
PYTHONPATH=src .venv/bin/python scripts/build_border_pairs.py
PYTHONPATH=src .venv/bin/python scripts/validate_policy_table.py
PYTHONPATH=src .venv/bin/python scripts/build_national_panel.py --start-year 2015 --end-year 2023
PYTHONPATH=src .venv/bin/python scripts/run_event_study.py --panel data/processed/national_border_qcew_food_service_panel.parquet
PYTHONPATH=src .venv/bin/python scripts/run_did.py --panel data/processed/national_border_qcew_food_service_panel.parquet
PYTHONPATH=src .venv/bin/python scripts/run_diagnostics.py --panel data/processed/national_border_qcew_food_service_panel.parquet
PYTHONPATH=src .venv/bin/python scripts/run_national_findings.py
```

Trade-shock shift-share extension, from prepared public inputs:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_shift_share.py \
  --us-imports data/raw/us_china_imports_hs6.csv \
  --instrument-trade data/raw/adh_country_china_imports_hs6.csv \
  --crosswalk data/raw/hs6_naics_crosswalk.csv \
  --qcew-industry data/processed/qcew_county_industry_panel.parquet \
  --county-to-cz data/raw/county_to_commuting_zone.csv \
  --start-year 1991 \
  --end-year 2007
```

Spatial RDD robustness, from a prepared public-geometry distance panel:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_spatial_rdd.py \
  --panel data/processed/spatial_border_distance_panel.parquet \
  --outcome log_employment \
  --running-col signed_distance_km
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
make fred-policy PYTHON=.venv/bin/python
make national-findings PYTHON=.venv/bin/python
make shift-share PYTHON=.venv/bin/python
make spatial-rdd PYTHON=.venv/bin/python
make test PYTHON=.venv/bin/python
```

## License

MIT
