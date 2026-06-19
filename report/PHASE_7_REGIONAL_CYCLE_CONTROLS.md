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

The live regional nowcast bridge now covers the 48 states/DC used by the national causal-policy panel. The coverage table should still be read before interpreting estimates, especially because some precision estimates remain unstable in high-dimensional clustered specifications.

## Current Run

Using the verified `regional-activity-nowcast` export, the merge matches 23,219 of 23,219 national panel rows, covering all 48 states/DC in the national panel. Treated-row and control-row coverage are both 100 percent.

The lagged regional-cycle controlled employment estimate is -0.0912 log points on 20,634 rows. Several clustered standard errors are unstable or undefined, so these outputs should be read as robustness evidence rather than a standalone definitive estimate.

The lagged activity-surprise interaction for employment is 0.0008 with undefined clustered precision. Dropping the highest absolute lagged-surprise state-years produces an employment estimate of -0.2337, again with unstable precision. The honest takeaway is not a strong new causal finding; it is that full-state live macro controls are now operational and the estimates remain sensitive enough to require careful robustness interpretation.
