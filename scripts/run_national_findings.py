#!/usr/bin/env python3
"""Run national border-panel findings without overwriting validation outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.did import pretrend_summary, run_event_study, run_pyfixest_lpdid, save_table
from causal_policy_evaluation.diagnostics import balance_table, raw_trends
from causal_policy_evaluation.economics import (
    assess_border_spillover_identification,
    estimate_bite_dose_response,
    estimate_heterogeneity,
    estimate_margin_decomposition,
    specification_curve,
)
from causal_policy_evaluation.inference import cluster_count, joint_pretrend_test
from causal_policy_evaluation.plots import plot_event_study, plot_specification_curve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--skip-pyfixest", action="store_true")
    parser.add_argument("--full-spec-curve", action="store_true", help="Run the full high-dimensional national specification curve.")
    args = parser.parse_args()

    panel_path = args.panel or args.root / "data/processed/national_border_qcew_food_service_panel.parquet"
    df = pd.read_parquet(panel_path)
    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)

    event = run_event_study(df)
    save_table(event, report / "national_event_study_coefficients.csv")
    save_table(pretrend_summary(event), report / "national_parallel_trends_preperiod.csv")
    plot_event_study(event, report / "national_event_study.png")

    if not args.skip_pyfixest:
        try:
            save_table(run_pyfixest_lpdid(df), report / "national_pyfixest_lpdid.csv")
        except Exception as exc:
            (report / "national_pyfixest_lpdid_error.txt").write_text(str(exc) + "\n", encoding="utf-8")

    raw_trends(df).to_csv(report / "national_raw_trends.csv", index=False)
    balance_table(df).to_csv(report / "national_balance_table.csv", index=False)
    cluster_count(df).to_csv(report / "national_cluster_diagnostics.csv", index=False)
    joint_pretrend_test(df).to_csv(report / "national_joint_pretrend_test.csv", index=False)

    margins = estimate_margin_decomposition(df)
    bite = estimate_bite_dose_response(df)
    heterogeneity = estimate_heterogeneity(df)
    spillovers = assess_border_spillover_identification(df)
    spec_sample = df if args.full_spec_curve else df[df["year"].between(2017, 2022)].copy()
    spec = specification_curve(spec_sample)
    margins.to_csv(report / "national_margin_decomposition.csv", index=False)
    bite.to_csv(report / "national_bite_dose_response.csv", index=False)
    heterogeneity.to_csv(report / "national_heterogeneity.csv", index=False)
    spillovers.to_csv(report / "national_spillover_identification.csv", index=False)
    spec.to_csv(report / "national_specification_curve.csv", index=False)
    plot_specification_curve(spec, report / "national_specification_curve.png")

    print(f"Read {len(df):,} national panel rows from {panel_path}")
    print(event.to_string(index=False))
    print(margins.to_string(index=False))
    print(bite.to_string(index=False))


if __name__ == "__main__":
    main()
