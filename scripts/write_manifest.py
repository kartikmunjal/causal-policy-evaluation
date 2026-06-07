#!/usr/bin/env python3
"""Write a reproducibility manifest with file hashes."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_policy_evaluation.reproducibility import write_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(f"Wrote {write_manifest(args.root)}")


if __name__ == "__main__":
    main()
