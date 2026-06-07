"""County adjacency and border-county-pair construction."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import io

import pandas as pd
import requests


CENSUS_ADJACENCY_URL = "https://www2.census.gov/geo/docs/reference/county_adjacency/county_adjacency2024.zip"

STATE_FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
    "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
    "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}


def fetch_county_adjacency(raw_dir: Path, timeout: int = 120) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / "county_adjacency2024.zip"
    if dest.exists():
        return dest
    response = requests.get(CENSUS_ADJACENCY_URL, timeout=timeout)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest


def load_county_adjacency(path: Path) -> pd.DataFrame:
    """Load Census county adjacency and normalize to county FIPS pairs.

    Census publishes a fixed-width-ish text file inside a zip. The first county
    name appears only on the first adjacent row, so forward-fill is required.
    """
    with ZipFile(path) as zf:
        name = next(item for item in zf.namelist() if item.endswith(".txt"))
        text = zf.read(name).decode("latin1")
    raw = pd.read_fwf(
        io.StringIO(text),
        names=["county_name", "county_fips", "neighbor_name", "neighbor_fips"],
        dtype=str,
    )
    raw["county_name"] = raw["county_name"].ffill()
    raw["county_fips"] = raw["county_fips"].ffill().str.zfill(5)
    raw["neighbor_fips"] = raw["neighbor_fips"].str.zfill(5)
    raw = raw[raw["county_fips"].str.match(r"^\d{5}$", na=False)]
    raw = raw[raw["neighbor_fips"].str.match(r"^\d{5}$", na=False)]
    return raw.drop_duplicates()


def build_state_border_pairs(adjacency: pd.DataFrame) -> pd.DataFrame:
    pairs = adjacency.copy()
    pairs["state"] = pairs["county_fips"].str[:2].map(STATE_FIPS_TO_ABBR)
    pairs["neighbor_state"] = pairs["neighbor_fips"].str[:2].map(STATE_FIPS_TO_ABBR)
    pairs = pairs[pairs["state"].notna() & pairs["neighbor_state"].notna()]
    pairs = pairs[pairs["state"] != pairs["neighbor_state"]]
    pairs["pair_low"] = pairs[["county_fips", "neighbor_fips"]].min(axis=1)
    pairs["pair_high"] = pairs[["county_fips", "neighbor_fips"]].max(axis=1)
    pairs["border_pair_id"] = pairs["pair_low"] + "_" + pairs["pair_high"]
    return pairs[
        ["border_pair_id", "county_fips", "state", "neighbor_fips", "neighbor_state", "county_name", "neighbor_name"]
    ].drop_duplicates("border_pair_id")


def expand_border_pairs_to_panel(qcew: pd.DataFrame, border_pairs: pd.DataFrame) -> pd.DataFrame:
    left = border_pairs[["border_pair_id", "county_fips", "state"]].rename(columns={"border_pair_id": "pair_id"})
    right = border_pairs[["border_pair_id", "neighbor_fips", "neighbor_state"]].rename(
        columns={"border_pair_id": "pair_id", "neighbor_fips": "county_fips", "neighbor_state": "state"}
    )
    membership = pd.concat([left, right], ignore_index=True).drop_duplicates()
    return qcew.merge(membership, on="county_fips", how="inner")
