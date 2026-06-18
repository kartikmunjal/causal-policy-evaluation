#!/usr/bin/env python3
"""Run China-shock shift-share construction from prepared public-data inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.shift_share import (
    aggregate_trade_to_naics,
    build_cz_industry_shares,
    build_trade_exposure,
    cz_outcome_changes,
    industry_trade_shocks,
    load_hs_naics_crosswalk,
    rotemberg_weights,
    run_shift_share_iv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--us-imports", type=Path, required=True)
    parser.add_argument("--instrument-trade", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--qcew-industry", type=Path, required=True)
    parser.add_argument("--county-to-cz", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=1991)
    parser.add_argument("--end-year", type=int, default=2007)
    args = parser.parse_args()

    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    crosswalk = load_hs_naics_crosswalk(args.crosswalk)
    us_trade, dropped_us = aggregate_trade_to_naics(pd.read_csv(args.us_imports), crosswalk)
    inst_trade, dropped_inst = aggregate_trade_to_naics(pd.read_csv(args.instrument_trade), crosswalk)
    china_shocks = industry_trade_shocks(us_trade, args.start_year, args.end_year, prefix="china_import")
    inst_shocks = industry_trade_shocks(inst_trade, args.start_year, args.end_year, prefix="adh_import")
    qcew = pd.read_parquet(args.qcew_industry) if args.qcew_industry.suffix == ".parquet" else pd.read_csv(args.qcew_industry)
    county_to_cz = pd.read_csv(args.county_to_cz, dtype={"county_fips": str})
    shares = build_cz_industry_shares(qcew, county_to_cz, args.start_year)
    exposure = build_trade_exposure(shares, china_shocks, inst_shocks)
    outcomes = cz_outcome_changes(qcew, county_to_cz, args.start_year, args.end_year)
    analysis = outcomes.merge(exposure, on="cz", how="inner")
    iv, first_stage = run_shift_share_iv(analysis)
    weights = rotemberg_weights(shares, inst_shocks)

    exposure.to_csv(report / "shift_share_exposure.csv", index=False)
    analysis.to_csv(report / "shift_share_analysis_panel.csv", index=False)
    iv.to_csv(report / "shift_share_iv.csv", index=False)
    weights.to_csv(report / "shift_share_rotemberg_weights.csv", index=False)
    dropped_us.to_csv(report / "shift_share_dropped_us_hs6.csv", index=False)
    dropped_inst.to_csv(report / "shift_share_dropped_instrument_hs6.csv", index=False)
    (report / "shift_share_first_stage.txt").write_text(first_stage + "\n", encoding="utf-8")
    print(iv.to_string(index=False))
    print(first_stage)


if __name__ == "__main__":
    main()
