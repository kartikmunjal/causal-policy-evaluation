"""Data fetching, provenance, and panel construction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile
import json
import re

import numpy as np
import pandas as pd
import requests

from causal_policy_evaluation.geography import expand_border_pairs_to_panel
from causal_policy_evaluation.policy import attach_policy_cohorts, validate_policy_table, write_policy_seed


QCEW_BASE = "https://data.bls.gov/cew/data/files"
FOOD_SERVICE_NAICS = "722"


@dataclass(frozen=True)
class SourceRecord:
    name: str
    url: str
    fetched_on: str
    vintage: str
    notes: str


NJ_PA_BORDER_PAIRS = pd.DataFrame(
    [
        ("34005", "42017", "NJ", "PA", "Burlington", "Bucks"),
        ("34007", "42101", "NJ", "PA", "Camden", "Philadelphia"),
        ("34015", "42045", "NJ", "PA", "Gloucester", "Delaware"),
        ("34021", "42017", "NJ", "PA", "Mercer", "Bucks"),
        ("34041", "42095", "NJ", "PA", "Warren", "Northampton"),
    ],
    columns=[
        "treated_fips",
        "control_fips",
        "treated_state",
        "control_state",
        "treated_county",
        "control_county",
    ],
)


MIN_WAGE_POLICY_DATES = pd.DataFrame(
    [
        ("NJ", "2019-07-01", 10.00, "First large post-2019 statutory increase used for the single-state validation design."),
        ("NJ", "2020-01-01", 11.00, "Scheduled increase."),
        ("NJ", "2021-01-01", 12.00, "Scheduled increase."),
        ("NJ", "2022-01-01", 13.00, "Scheduled increase."),
        ("PA", None, 7.25, "Control state retained federal minimum during the validation window."),
    ],
    columns=["state", "effective_date", "minimum_wage", "notes"],
)


def ensure_dirs(root: Path) -> None:
    for rel in ["data/raw", "data/processed", "report"]:
        (root / rel).mkdir(parents=True, exist_ok=True)


def write_provenance(raw_dir: Path, records: Iterable[SourceRecord]) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / "provenance.json"
    payload = [record.__dict__ for record in records]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def qcew_county_annual_url(year: int) -> str:
    return f"{QCEW_BASE}/{year}/csv/{year}_annual_by_area.zip"


def fetch_qcew_year(year: int, raw_dir: Path, timeout: int = 120) -> Path:
    """Download a BLS QCEW annual county zip and cache it under data/raw."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / f"qcew_{year}_annual_by_area.zip"
    if dest.exists():
        return dest
    url = qcew_county_annual_url(year)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest


def load_qcew_food_service(paths: Iterable[Path], fips: Iterable[str] | None = None) -> pd.DataFrame:
    """Load county-level QCEW food-service annual records from cached BLS zips."""
    frames: list[pd.DataFrame] = []
    wanted = set(fips) if fips is not None else set()
    for path in paths:
        with ZipFile(path) as zf:
            names = [name for name in zf.namelist() if name.endswith(".csv")]
            if wanted:
                names = [name for name in names if any(f" {code} " in name for code in wanted)]
            else:
                names = [name for name in names if re.search(r"annual \d{5} ", name)]
            for csv_name in names:
                with zf.open(csv_name) as handle:
                    df = pd.read_csv(handle, dtype={"area_fips": str, "industry_code": str, "own_code": str})
                df = df[(df["industry_code"] == FOOD_SERVICE_NAICS) & (df["own_code"] == "5")]
                if wanted:
                    df = df[df["area_fips"].isin(wanted)]
                estabs_col = "annual_avg_estabs_count" if "annual_avg_estabs_count" in df.columns else "annual_avg_estabs"
                keep = ["area_fips", "year", "annual_avg_emplvl", "total_annual_wages", estabs_col]
                frames.append(df[keep].copy())
    if not frames:
        return pd.DataFrame(columns=["area_fips", "year", "employment", "wages", "establishments"])
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(
        columns={
            "area_fips": "county_fips",
            "annual_avg_emplvl": "employment",
            "total_annual_wages": "wages",
            "annual_avg_estabs": "establishments",
            "annual_avg_estabs_count": "establishments",
        }
    )
    out["county_fips"] = out["county_fips"].str.zfill(5)
    return out


def build_nj_pa_border_panel(qcew: pd.DataFrame) -> pd.DataFrame:
    """Construct the single-treated-state border-county-pair validation panel."""
    pairs = NJ_PA_BORDER_PAIRS.copy()
    treated = pairs[["treated_fips", "control_fips"]].rename(columns={"treated_fips": "county_fips"})
    treated["pair_id"] = treated["county_fips"] + "_" + treated["control_fips"]
    treated["state"] = "NJ"
    treated["treated"] = 1
    control = pairs[["treated_fips", "control_fips"]].rename(columns={"control_fips": "county_fips"})
    control["pair_id"] = control["treated_fips"] + "_" + control["county_fips"]
    control["state"] = "PA"
    control["treated"] = 0
    counties = pd.concat(
        [treated[["county_fips", "pair_id", "state", "treated"]], control[["county_fips", "pair_id", "state", "treated"]]],
        ignore_index=True,
    )
    panel = qcew.merge(counties, on="county_fips", how="inner")
    panel["policy_year"] = np.where(panel["state"].eq("NJ"), 2019, np.nan)
    panel["relative_year"] = panel["year"] - 2019
    panel["post"] = (panel["year"] >= 2019).astype(int)
    panel["log_employment"] = np.log(panel["employment"].clip(lower=1))
    panel["log_wages"] = np.log(panel["wages"].clip(lower=1))
    return panel.sort_values(["pair_id", "county_fips", "year"]).reset_index(drop=True)


def write_policy_table(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / "minimum_wage_policy_dates.csv"
    if not path.exists():
        write_policy_seed(path)
    return path


def make_smoke_panel() -> pd.DataFrame:
    """Small deterministic panel used by tests and offline examples."""
    rows = []
    rng = np.random.default_rng(7)
    counties = [
        ("34005", "NJ", 1, "34005_42017"),
        ("42017", "PA", 0, "34005_42017"),
        ("34007", "NJ", 1, "34007_42101"),
        ("42101", "PA", 0, "34007_42101"),
    ]
    for county, state, treated, pair in counties:
        for year in range(2014, 2024):
            trend = 0.025 * (year - 2015)
            treatment = -0.03 * treated * (year >= 2019) * (year - 2018)
            base = 8.0 + trend + treatment + rng.normal(0, 0.005)
            employment = int(np.exp(base))
            wages = int(employment * (28000 + 800 * (year - 2015) + 1200 * treated))
            rows.append(
                {
                    "county_fips": county,
                    "year": year,
                    "employment": employment,
                    "wages": wages,
                    "establishments": 100 + year - 2015,
                    "pair_id": pair,
                    "state": state,
                    "treated": treated,
                    "policy_year": 2019 if treated else np.nan,
                    "relative_year": year - 2019,
                    "post": int(year >= 2019),
                    "log_employment": np.log(max(employment, 1)),
                    "log_wages": np.log(max(wages, 1)),
                }
            )
    return pd.DataFrame(rows)


def fetch_validation_data(root: Path, years: Iterable[int]) -> pd.DataFrame:
    ensure_dirs(root)
    raw_dir = root / "data" / "raw"
    paths = [fetch_qcew_year(year, raw_dir) for year in years]
    fips = pd.concat([NJ_PA_BORDER_PAIRS["treated_fips"], NJ_PA_BORDER_PAIRS["control_fips"]]).unique()
    qcew = load_qcew_food_service(paths, fips=fips)
    panel = build_nj_pa_border_panel(qcew)
    processed = root / "data" / "processed" / "nj_pa_qcew_food_service_panel.parquet"
    panel.to_parquet(processed, index=False)
    write_policy_table(raw_dir)
    write_provenance(
        raw_dir,
        [
            SourceRecord(
                name="BLS QCEW annual county data",
                url=qcew_county_annual_url(min(years)),
                fetched_on=date.today().isoformat(),
                vintage=f"{min(years)}-{max(years)} annual files",
                notes="County ownership code 5, NAICS 722 food services and drinking places.",
            ),
            SourceRecord(
                name="State minimum wage dates",
                url="https://www.dol.gov/agencies/whd/state/minimum-wage/history",
                fetched_on=date.today().isoformat(),
                vintage="Documented project table; verify against state/DOL sources before final reporting.",
                notes="Cached as data/raw/minimum_wage_policy_dates.csv.",
            ),
        ],
    )
    return panel


def build_national_border_panel(
    qcew: pd.DataFrame,
    border_pairs: pd.DataFrame,
    policy: pd.DataFrame,
    require_verified_policy: bool = True,
) -> pd.DataFrame:
    """Build all-state border-county-pair panel from QCEW, Census adjacency, and policy cohorts."""
    checks = validate_policy_table(policy, require_verified=require_verified_policy)
    invalid = checks[~checks["valid"]]
    if not invalid.empty:
        raise ValueError("Policy table failed validation:\n" + invalid.to_string(index=False))
    panel = expand_border_pairs_to_panel(qcew, border_pairs)
    panel = attach_policy_cohorts(panel, policy)
    panel["log_employment"] = np.log(panel["employment"].clip(lower=1))
    panel["log_wages"] = np.log(panel["wages"].clip(lower=1))
    return panel.sort_values(["pair_id", "county_fips", "year"]).reset_index(drop=True)
