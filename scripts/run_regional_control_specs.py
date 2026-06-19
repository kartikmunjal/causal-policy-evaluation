#!/usr/bin/env python3
"""Merge regional nowcast controls and run cycle-adjusted policy specs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.regional_controls import (
    estimate_activity_surprise_heterogeneity,
    estimate_excluding_high_surprise_years,
    estimate_regional_cycle_adjusted_did,
    load_regional_policy_controls,
    merge_regional_controls,
    regional_control_coverage,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path, default=Path("data/processed/national_border_qcew_food_service_panel.parquet"))
    parser.add_argument(
        "--regional-controls",
        type=Path,
        default=Path("../regional-activity-nowcast/report/state_year_policy_controls.csv"),
    )
    parser.add_argument("--out-panel", type=Path, default=Path("data/processed/national_border_qcew_with_regional_controls.parquet"))
    args = parser.parse_args()

    panel_path = args.panel if args.panel.is_absolute() else args.root / args.panel
    controls_path = args.regional_controls if args.regional_controls.is_absolute() else args.root / args.regional_controls
    out_panel = args.out_panel if args.out_panel.is_absolute() else args.root / args.out_panel
    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    out_panel.parent.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(panel_path)
    controls = load_regional_policy_controls(controls_path)
    merged = merge_regional_controls(panel, controls)
    merged.to_parquet(out_panel, index=False)

    coverage = regional_control_coverage(merged)
    matched = merged[merged["has_regional_controls"]].copy()
    adjusted = estimate_regional_cycle_adjusted_did(matched)
    heterogeneity = estimate_activity_surprise_heterogeneity(matched)
    exclusion = estimate_excluding_high_surprise_years(matched)

    coverage.to_csv(report / "regional_control_coverage.csv", index=False)
    adjusted.to_csv(report / "regional_cycle_adjusted_did.csv", index=False)
    heterogeneity.to_csv(report / "regional_activity_surprise_heterogeneity.csv", index=False)
    exclusion.to_csv(report / "regional_high_surprise_exclusion.csv", index=False)

    print(f"Read panel rows: {len(panel):,}")
    print(f"Regional control rows: {len(controls):,} from {controls_path}")
    print(coverage.to_string(index=False))
    print(adjusted.to_string(index=False))
    print(heterogeneity.to_string(index=False))
    print(exclusion.to_string(index=False))


if __name__ == "__main__":
    main()
