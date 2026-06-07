#!/usr/bin/env python3
"""Run synthetic-control robustness and placebo inference."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.plots import plot_treated_vs_synthetic
from causal_policy_evaluation.synthetic_control import fit_simple_synth, placebo_permutation_gaps, save_synth_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--treated-unit", default="34005")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    paths, weights = fit_simple_synth(df, treated_unit=args.treated_unit)
    placebo = placebo_permutation_gaps(df)
    report = args.root / "report"
    save_synth_outputs(paths, weights, placebo, report)
    plot_treated_vs_synthetic(paths, report / "treated_vs_synthetic.png")
    print(weights.to_string(index=False))
    print(placebo.to_string(index=False))


if __name__ == "__main__":
    main()
