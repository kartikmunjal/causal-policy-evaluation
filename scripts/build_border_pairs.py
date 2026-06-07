#!/usr/bin/env python3
"""Fetch Census adjacency and build cross-state county border pairs."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.geography import build_state_border_pairs, fetch_county_adjacency, load_county_adjacency


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--adjacency-zip", type=Path)
    args = parser.parse_args()

    raw = args.root / "data" / "raw"
    processed = args.root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    path = args.adjacency_zip or fetch_county_adjacency(raw)
    adjacency = load_county_adjacency(path)
    pairs = build_state_border_pairs(adjacency)
    out = processed / "state_border_county_pairs.csv"
    pairs.to_csv(out, index=False)
    print(f"Wrote {len(pairs):,} cross-state border pairs to {out}")


if __name__ == "__main__":
    main()
