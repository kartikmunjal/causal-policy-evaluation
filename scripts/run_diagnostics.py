#!/usr/bin/env python3
"""Run balance, raw-trend, pretrend, placebo, and cluster diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.diagnostics import balance_table, raw_trends
from causal_policy_evaluation.inference import cluster_count, joint_pretrend_test, placebo_policy_years, wild_cluster_bootstrap_did


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--bootstrap-reps", type=int, default=499)
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    raw_trends(df).to_csv(report / "raw_trends.csv", index=False)
    balance_table(df).to_csv(report / "balance_table.csv", index=False)
    cluster_count(df).to_csv(report / "cluster_diagnostics.csv", index=False)
    joint_pretrend_test(df).to_csv(report / "joint_pretrend_test.csv", index=False)
    pre_years = sorted(year for year in df["year"].unique() if year < df.loc[df["treated"] == 1, "year"].max())[:3]
    placebo_policy_years(df, pre_years).to_csv(report / "placebo_policy_years.csv", index=False)
    wild_cluster_bootstrap_did(df, reps=args.bootstrap_reps).to_csv(report / "wild_cluster_bootstrap.csv", index=False)
    print(f"Wrote diagnostics to {report}")


if __name__ == "__main__":
    main()
