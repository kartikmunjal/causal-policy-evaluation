#!/usr/bin/env python3
"""Run the pre-specified event-study specification."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.did import pretrend_summary, run_event_study, save_table
from causal_policy_evaluation.plots import plot_event_study


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    results = run_event_study(df)
    report = args.root / "report"
    save_table(results, report / "event_study_coefficients.csv")
    save_table(pretrend_summary(results), report / "parallel_trends_preperiod.csv")
    plot_event_study(results, report / "event_study.png")
    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
