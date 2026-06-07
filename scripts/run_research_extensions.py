#!/usr/bin/env python3
"""Run Phase 2 economics-focused mechanism and heterogeneity analyses."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.economics import (
    assess_border_spillover_identification,
    estimate_bite_dose_response,
    estimate_heterogeneity,
    estimate_margin_decomposition,
    save_research_outputs,
    specification_curve,
)
from causal_policy_evaluation.plots import plot_specification_curve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    outputs = {
        "phase2_margin_decomposition": estimate_margin_decomposition(df),
        "phase2_bite_dose_response": estimate_bite_dose_response(df),
        "phase2_heterogeneity": estimate_heterogeneity(df),
        "phase2_spillover_identification": assess_border_spillover_identification(df),
        "phase2_specification_curve": specification_curve(df),
    }
    report = args.root / "report"
    save_research_outputs(outputs, report)
    plot_specification_curve(outputs["phase2_specification_curve"], report / "phase2_specification_curve.png")
    for name, table in outputs.items():
        print(f"\n{name}")
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
