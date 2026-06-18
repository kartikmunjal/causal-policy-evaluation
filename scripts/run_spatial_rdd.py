#!/usr/bin/env python3
"""Run a spatial RDD from a prepared border-distance panel."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from causal_policy_evaluation.rdd import (
    density_balance_diagnostics,
    run_local_linear_rdd,
    spatial_rdd_identification_notes,
)


def _read_frame(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--outcome", default="log_employment")
    parser.add_argument("--running-col", default="signed_distance_km")
    parser.add_argument("--bandwidth", type=float, default=None)
    parser.add_argument("--cluster-col", default="state")
    args = parser.parse_args()

    report = args.root / "report"
    report.mkdir(parents=True, exist_ok=True)
    panel = _read_frame(args.panel)
    estimate = run_local_linear_rdd(
        panel,
        outcome=args.outcome,
        running_col=args.running_col,
        bandwidth=args.bandwidth,
        cluster_col=args.cluster_col,
    ).as_frame()
    diagnostics = density_balance_diagnostics(panel, running_col=args.running_col, bandwidth=args.bandwidth)
    notes = spatial_rdd_identification_notes()
    estimate.to_csv(report / "spatial_rdd_estimates.csv", index=False)
    diagnostics.to_csv(report / "spatial_rdd_diagnostics.csv", index=False)
    notes.to_csv(report / "spatial_rdd_identification_notes.csv", index=False)
    print(estimate.to_string(index=False))
    print(diagnostics.to_string(index=False))


if __name__ == "__main__":
    main()
