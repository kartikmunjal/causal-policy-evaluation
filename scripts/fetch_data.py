#!/usr/bin/env python3
"""Fetch and cache public data for the single-state validation pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.data import fetch_validation_data, make_smoke_panel, write_policy_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--smoke", action="store_true", help="Write a tiny offline panel instead of downloading BLS data.")
    args = parser.parse_args()

    processed = args.root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        panel = make_smoke_panel()
        panel.to_parquet(processed / "nj_pa_qcew_food_service_panel.parquet", index=False)
        write_policy_table(args.root / "data" / "raw")
    else:
        panel = fetch_validation_data(args.root, range(args.start_year, args.end_year + 1))
    print(f"Wrote {len(panel):,} panel rows")


if __name__ == "__main__":
    main()
