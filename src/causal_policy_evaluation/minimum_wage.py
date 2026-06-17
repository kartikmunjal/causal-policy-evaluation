"""FRED/DOL state minimum-wage time-series ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io

import pandas as pd
import requests
from requests import HTTPError, RequestException


FRED_GRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

STATE_ABBRS = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
    "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY",
]


@dataclass(frozen=True)
class FredMinimumWageSource:
    state: str
    series_id: str
    url: str


def fred_series_id(state: str) -> str:
    return f"STTMINWG{state.upper()}"


def fred_min_wage_url(series_id: str) -> str:
    return f"{FRED_GRAPH_URL}?id={series_id}"


def fetch_state_minimum_wage(state: str, timeout: int = 120, retries: int = 3) -> pd.DataFrame:
    series = fred_series_id(state)
    url = fred_min_wage_url(series)
    last_exc: RequestException | None = None
    for _ in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            break
        except RequestException as exc:
            last_exc = exc
    else:
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"Failed to fetch {series}")
    df = pd.read_csv(io.StringIO(response.text))
    if series not in df.columns:
        raise ValueError(f"FRED response for {state} did not include {series}")
    out = df.rename(columns={"observation_date": "date", series: "minimum_wage"})
    out["state"] = state.upper()
    out["series_id"] = series
    out["source_url"] = url
    out["date"] = pd.to_datetime(out["date"])
    out["minimum_wage"] = pd.to_numeric(out["minimum_wage"], errors="coerce")
    return out.dropna(subset=["minimum_wage"])


def detect_minimum_wage_changes(series: pd.DataFrame, start_year: int, end_year: int, min_change: float = 0.0) -> pd.DataFrame:
    work = series.sort_values(["state", "date"]).copy()
    work["old_minimum_wage"] = work.groupby("state")["minimum_wage"].shift(1)
    changes = work[work["old_minimum_wage"].notna() & (work["minimum_wage"] != work["old_minimum_wage"])].copy()
    changes = changes[changes["date"].dt.year.between(start_year, end_year)]
    changes["nominal_change"] = changes["minimum_wage"] - changes["old_minimum_wage"]
    changes = changes[changes["nominal_change"] > min_change]
    changes["pct_change"] = changes["nominal_change"] / changes["old_minimum_wage"]
    changes["effective_date"] = changes["date"].dt.strftime("%Y-%m-%d")
    changes["policy_year"] = changes["date"].dt.year
    changes["new_minimum_wage"] = changes["minimum_wage"]
    changes["source_name"] = "FRED state minimum wage series, sourced from US Department of Labor"
    changes["verified"] = True
    changes["notes"] = "Detected increase in FRED state minimum wage time series."
    return changes[
        [
            "state",
            "effective_date",
            "old_minimum_wage",
            "new_minimum_wage",
            "nominal_change",
            "pct_change",
            "policy_year",
            "source_url",
            "source_name",
            "verified",
            "notes",
        ]
    ]


def build_fred_policy_table(
    states: list[str] | None = None,
    start_year: int = 2015,
    end_year: int = 2023,
    min_change: float = 0.0,
    skip_missing: bool = True,
) -> pd.DataFrame:
    frames = []
    missing = []
    for state in states or STATE_ABBRS:
        try:
            frames.append(fetch_state_minimum_wage(state))
        except HTTPError as exc:
            if not skip_missing or exc.response is None or exc.response.status_code != 404:
                raise
            missing.append(state)
    if not frames:
        return pd.DataFrame(
            columns=[
                "state",
                "effective_date",
                "old_minimum_wage",
                "new_minimum_wage",
                "nominal_change",
                "pct_change",
                "policy_year",
                "source_url",
                "source_name",
                "verified",
                "notes",
            ]
        )
    series = pd.concat(frames, ignore_index=True)
    policy = detect_minimum_wage_changes(series, start_year=start_year, end_year=end_year, min_change=min_change)
    policy.attrs["missing_states"] = missing
    return policy


def build_fred_series(
    states: list[str] | None = None,
    skip_missing: bool = True,
) -> pd.DataFrame:
    frames = []
    missing = []
    for state in states or STATE_ABBRS:
        try:
            frames.append(fetch_state_minimum_wage(state))
        except HTTPError as exc:
            if not skip_missing or exc.response is None or exc.response.status_code != 404:
                raise
            missing.append(state)
    if not frames:
        out = pd.DataFrame(columns=["date", "minimum_wage", "state", "series_id", "source_url"])
    else:
        out = pd.concat(frames, ignore_index=True)
    out.attrs["missing_states"] = missing
    return out


def annual_panel_from_series(series: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    if series.empty:
        return pd.DataFrame(columns=["state", "year", "minimum_wage", "series_id", "source_url"])
    work = series.copy()
    work["year"] = work["date"].dt.year
    panel = work[work["year"].between(start_year, end_year)].copy()
    panel = panel.sort_values(["state", "date"]).groupby(["state", "year"], as_index=False).last()
    return panel[["state", "year", "minimum_wage", "series_id", "source_url"]]


def build_fred_minimum_wage_panel(
    states: list[str] | None = None,
    start_year: int = 2015,
    end_year: int = 2023,
    skip_missing: bool = True,
) -> pd.DataFrame:
    series = build_fred_series(states=states, skip_missing=skip_missing)
    panel = annual_panel_from_series(series, start_year=start_year, end_year=end_year)
    panel.attrs["missing_states"] = series.attrs.get("missing_states", [])
    return panel


def write_fred_policy_table(path: Path, policy: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    policy.to_csv(path, index=False)
    return path
