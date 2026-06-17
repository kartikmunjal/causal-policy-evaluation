#!/usr/bin/env python3
"""Fetch FRED/DOL state minimum-wage histories and detect policy increases."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.minimum_wage import (
    STATE_ABBRS,
    annual_panel_from_series,
    build_fred_series,
    detect_minimum_wage_changes,
    write_fred_policy_table,
)
from causal_policy_evaluation.policy import validate_policy_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--states", nargs="*", default=STATE_ABBRS)
    parser.add_argument("--min-change", type=float, default=0.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--annual-output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail if a state FRED series is missing.")
    args = parser.parse_args()

    output = args.output or args.root / "data" / "raw" / "minimum_wage_policy_dates.csv"
    annual_output = args.annual_output or args.root / "data" / "raw" / "state_minimum_wage_annual.csv"
    series = build_fred_series(states=args.states, skip_missing=not args.strict)
    policy = detect_minimum_wage_changes(series, start_year=args.start_year, end_year=args.end_year, min_change=args.min_change)
    policy.attrs["missing_states"] = series.attrs.get("missing_states", [])
    annual = annual_panel_from_series(series, start_year=args.start_year, end_year=args.end_year)
    annual.attrs["missing_states"] = series.attrs.get("missing_states", [])
    write_fred_policy_table(output, policy)
    annual.to_csv(annual_output, index=False)
    checks = validate_policy_table(policy)
    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    checks.to_csv(report / "policy_validation.csv", index=False)
    missing = policy.attrs.get("missing_states", [])
    if missing:
        (report / "policy_fred_missing_states.txt").write_text("\n".join(missing) + "\n", encoding="utf-8")
    print(f"Wrote {len(policy):,} policy changes to {output}")
    print(f"Wrote {len(annual):,} annual state minimum-wage rows to {annual_output}")
    if missing:
        print(f"Skipped {len(missing)} states with missing FRED series: {', '.join(missing)}")
    print(checks.to_string(index=False))


if __name__ == "__main__":
    main()
