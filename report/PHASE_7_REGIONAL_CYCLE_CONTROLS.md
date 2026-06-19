# Phase 7: Regional-Cycle Controls

This phase connects the causal-policy repo to the live `regional-activity-nowcast` repo.

## Purpose

Minimum-wage policy changes occur in real regional economies, not in a macro vacuum. The regional nowcast repo now exports state-year activity controls and nowcast surprises from verified public FRED and BEA data. This phase merges those controls into the national border-county panel and asks whether the minimum-wage estimates are sensitive to regional cycle conditions.

## Design Discipline

These are robustness and heterogeneity checks, not the primary estimator. The headline design remains the border-county-pair DiD/event-study design. Regional controls are reported separately because contemporaneous economic activity can be a bad control if it is itself affected by policy. The preferred checks use one-year lagged activity controls.

## Outputs

- `report/regional_control_coverage.csv`
- `report/regional_cycle_adjusted_did.csv`
- `report/regional_activity_surprise_heterogeneity.csv`
- `report/regional_high_surprise_exclusion.csv`
- `data/processed/national_border_qcew_with_regional_controls.parquet`

## Interpretation

The live regional nowcast pilot currently covers 10 states. Coverage is therefore partial relative to the full national policy panel. The coverage table must be read before interpreting estimates. Any matched-state result should be described as a live-control pilot robustness check, not as a replacement for the full national estimate.

## Current Run

Using the verified `regional-activity-nowcast` export, the merge matches 5,021 of 23,219 national panel rows, covering 10 of 48 states. Treated-row coverage is 23.9 percent and control-row coverage is 18.9 percent.

The lagged regional-cycle controlled employment estimate is 0.0046 log points on 4,464 matched rows. Several clustered standard errors are unstable or undefined in the matched-state subset, so these outputs should be read as a pilot robustness screen rather than a definitive national estimate.

The lagged activity-surprise interaction for employment is -0.0036 with a very large clustered standard error. Dropping the highest absolute lagged-surprise state-years produces an employment estimate of 0.2494, again with unstable precision. The honest takeaway is not a strong new causal finding; it is that the live macro-control bridge is operational and exposes where broader state coverage is needed.
