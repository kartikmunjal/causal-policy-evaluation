#!/usr/bin/env python3
"""Run shift-share IV specification and report first-stage strength."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import make_smoke_panel
from causal_policy_evaluation.iv import add_bartik_instrument, run_2sls, save_iv_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    df = make_smoke_panel() if args.smoke else pd.read_parquet(args.panel or args.root / "data/processed/nj_pa_qcew_food_service_panel.parquet")
    work = add_bartik_instrument(df)
    table, first_stage = run_2sls(work)
    save_iv_outputs(table, first_stage, args.root / "report")
    print(table.to_string(index=False))
    print(first_stage)


if __name__ == "__main__":
    main()
