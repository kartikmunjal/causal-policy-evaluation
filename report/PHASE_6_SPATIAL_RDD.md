# Phase 6: Spatial RDD Robustness

This phase adds a spatial regression-discontinuity scaffold for state-border policy jumps. It is intentionally a robustness design, not the primary estimator.

## Why This Is Secondary

State borders can create sharp minimum-wage differences, but they also bundle many other discontinuities: taxes, labor laws, demographics, land use, commuting patterns, enforcement, and pandemic policies. A spatial RDD is therefore useful as a local robustness check only when the running variable and policy jump are documented carefully.

## Required Running Variable

The script requires `signed_distance_km`, with:

- negative distance for counties on the lower-minimum-wage side of the relevant border
- positive distance for counties on the higher-minimum-wage side
- zero as the state-border cutoff

The repo does not fabricate this variable from treatment status. A credible run should build it from public county geometry, border geometry, and a documented side assignment.

## Estimator

The built-in estimator runs a local-linear RDD:

`Y_i = alpha + tau RightSide_i + beta distance_i + gamma RightSide_i * distance_i + e_i`

inside a chosen bandwidth, using triangular kernel weights. If a cluster column is supplied, it reports clustered covariance; otherwise it reports HC1 robust covariance.

## Diagnostics

The phase writes:

- `report/spatial_rdd_estimates.csv`
- `report/spatial_rdd_diagnostics.csv`
- `report/spatial_rdd_identification_notes.csv`

The diagnostics include left/right counts near the cutoff and whether a formal `rddensity` package is installed. The built-in count imbalance is a screen, not a formal McCrary test.

## Interpretation

Use this phase to ask whether the border-local discontinuity tells the same story as the border-pair DiD and synthetic-control evidence. Do not interpret it as definitive if pre-policy covariates jump at the border or if the minimum-wage difference is not sharp.
