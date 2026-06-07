#!/usr/bin/env python3
"""Render the markdown research write-up from generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.reporting import render_research_grade_writeup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    out = render_research_grade_writeup(args.root / "report")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
