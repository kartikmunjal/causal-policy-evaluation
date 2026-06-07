#!/usr/bin/env python3
"""Run the validation pipeline end to end."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--python", default=".venv/bin/python")
    args = parser.parse_args()

    py = str(Path(args.python))
    smoke = ["--smoke"] if args.smoke else []
    run([py, "scripts/fetch_data.py", *smoke], args.root)
    run([py, "scripts/run_event_study.py", *smoke], args.root)
    run([py, "scripts/run_did.py", "--skip-cs", *smoke], args.root)
    run([py, "scripts/run_synthetic_control.py", *smoke], args.root)
    run([py, "scripts/run_iv.py", *smoke], args.root)
    run([py, "scripts/run_diagnostics.py", *smoke, "--bootstrap-reps", "99"], args.root)
    run([py, "scripts/run_research_extensions.py", *smoke], args.root)
    run([py, "scripts/render_report.py"], args.root)
    run([py, "scripts/write_manifest.py"], args.root)


if __name__ == "__main__":
    main()
