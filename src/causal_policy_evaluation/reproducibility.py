"""Reproducibility manifest helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(root: Path, output: Path | None = None) -> Path:
    output = output or root / "report" / "manifest.json"
    include_roots = [root / "README.md", root / "requirements.txt", root / "data" / "raw", root / "report", root / "src", root / "scripts", root / "tests"]
    files = []
    for item in include_roots:
        if item.is_file():
            candidates = [item]
        elif item.exists():
            candidates = [path for path in item.rglob("*") if path.is_file()]
        else:
            candidates = []
        for path in candidates:
            rel = path.relative_to(root).as_posix()
            if rel == "report/manifest.json":
                continue
            if rel.endswith("_sample.csv"):
                continue
            if ".venv" in rel or "__pycache__" in rel or rel.endswith(".zip") or rel.endswith(".parquet"):
                continue
            files.append({"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "files": sorted(files, key=lambda item: item["path"]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output
