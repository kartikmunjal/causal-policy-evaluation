#!/usr/bin/env python3
"""Validate the audited minimum-wage policy table."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.policy import load_policy_table, validate_policy_table, write_policy_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--write-seed", action="store_true")
    parser.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args()

    path = args.policy or args.root / "data" / "raw" / "minimum_wage_policy_dates.csv"
    if args.write_seed or not path.exists():
        write_policy_seed(path)
    policy = load_policy_table(path)
    checks = validate_policy_table(policy, require_verified=not args.allow_unverified)
    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    checks.to_csv(report / "policy_validation.csv", index=False)
    print(checks.to_string(index=False))
    if not checks["valid"].all():
        raise SystemExit("Policy table validation failed.")


if __name__ == "__main__":
    main()
