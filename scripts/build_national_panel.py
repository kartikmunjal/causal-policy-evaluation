#!/usr/bin/env python3
"""Build the all-state border-county-pair panel from audited inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import build_national_border_panel, fetch_qcew_year, load_qcew_food_service
from causal_policy_evaluation.policy import load_policy_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--border-pairs", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--state-min-wage", type=Path)
    parser.add_argument("--allow-unverified-policy", action="store_true")
    args = parser.parse_args()

    raw = args.root / "data" / "raw"
    processed = args.root / "data" / "processed"
    pairs_path = args.border_pairs or processed / "state_border_county_pairs.csv"
    policy_path = args.policy or raw / "minimum_wage_policy_dates.csv"
    min_wage_path = args.state_min_wage or raw / "state_minimum_wage_annual.csv"
    if not pairs_path.exists():
        raise SystemExit(f"Missing border pairs file: {pairs_path}. Run scripts/build_border_pairs.py first.")
    paths = [fetch_qcew_year(year, raw) for year in range(args.start_year, args.end_year + 1)]
    qcew = load_qcew_food_service(paths)
    pairs = pd.read_csv(pairs_path, dtype=str)
    policy = load_policy_table(policy_path)
    panel = build_national_border_panel(
        qcew,
        pairs,
        policy,
        require_verified_policy=not args.allow_unverified_policy,
    )
    if min_wage_path.exists():
        min_wage = pd.read_csv(min_wage_path, dtype={"state": str})
        min_wage["year"] = min_wage["year"].astype(int)
        panel = panel.merge(min_wage[["state", "year", "minimum_wage"]], on=["state", "year"], how="left")
    out = processed / "national_border_qcew_food_service_panel.parquet"
    panel.to_parquet(out, index=False)
    print(f"Wrote {len(panel):,} rows to {out}")


if __name__ == "__main__":
    main()
