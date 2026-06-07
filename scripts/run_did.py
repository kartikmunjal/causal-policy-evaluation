#!/usr/bin/env python3
"""Run single-cohort validation DiD and, when available, Callaway-Sant'Anna DiD."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.did import run_border_pair_did, run_callaway_santanna, run_pyfixest_lpdid, save_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip-cs", action="store_true", help="Skip Callaway-Sant'Anna estimator.")
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    report = args.root / "report"
    validation = run_border_pair_did(df)
    save_table(validation, report / "border_pair_did.csv")
    print(validation.to_string(index=False))

    modern = run_pyfixest_lpdid(df)
    save_table(modern, report / "pyfixest_lpdid.csv")
    print(modern.to_string(index=False))

    if not args.skip_cs:
        try:
            cs = run_callaway_santanna(df)
            save_table(cs, report / "callaway_santanna_attgt.csv")
        except RuntimeError as exc:
            print(f"Callaway-Sant'Anna skipped: {exc}")


if __name__ == "__main__":
    main()
