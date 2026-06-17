# Phase 4 National Panel

Phase 4 moves beyond the NJ/PA validation case and builds a national border-county-pair research sample.

## Data Inputs

- FRED/DOL state minimum-wage series, 2015-2023
- Census 2024 county adjacency file
- BLS QCEW annual county data, NAICS 722, private ownership

## Built Artifacts

- 210 FRED/DOL minimum-wage increases
- 414 state-year minimum-wage-rate rows
- 1,306 Census cross-state border-county pairs
- 23,219 national border-county-pair-year QCEW rows

FRED did not provide state series for AL, LA, MS, SC, and TN; these are recorded in `policy_fred_missing_states.txt`.

## National Results Snapshot

The national pyfixest LPDID estimate is 0.0741 log points with SE 0.0738 and p = 0.325. The estimate is positive but statistically imprecise.

The national event-study point estimates are:

- event year -4: 0.0408
- event year -3: 0.0700
- event year -2: 0.0891
- event year 0: 0.0575
- event year +1: -0.1016
- event year +2: -0.0835
- event year +3: -0.0160

The margin decomposition estimates are:

- employment: -0.0649
- establishments: -0.0049
- employment per establishment: -0.2202
- average annual pay: 0.0199

The bite/dose-response estimates are:

- employment: 0.0014
- establishments: -0.0037
- employment per establishment: 0.0600
- average annual pay: -0.0075

## Interpretation

The national panel produces real multi-state estimates, but inference remains fragile in several high-dimensional state-clustered specifications. The most defensible interpretation at this stage is that the average national employment effect is not precisely estimated, while the mechanism tables suggest adjustment may differ across margins.

This is now genuine economic evidence rather than only a validation pipeline, but the next improvement should refine cohorts, treatment dosage, and inference before making a strong causal claim.
