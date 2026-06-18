"""China-shock shift-share construction and IV estimation.

The functions in this module are intentionally source-agnostic: Comtrade pulls,
Pierce-Schott concordances, Dorn county-to-CZ crosswalks, and QCEW
county-industry panels can be fetched by scripts and then passed here as
ordinary data frames. This keeps the publication-grade data construction
auditable and testable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.iv import IV2SLS


ADH_INSTRUMENT_COUNTRIES = [
    "Australia",
    "Denmark",
    "Finland",
    "Germany",
    "Japan",
    "New Zealand",
    "Spain",
    "Switzerland",
]


def normalize_hs6(value: object) -> str:
    text = str(value).strip().replace(".", "")
    return text.zfill(6)[:6]


def load_hs_naics_crosswalk(path: Path) -> pd.DataFrame:
    """Load an HS6-to-NAICS crosswalk with optional allocation shares.

    Expected columns are flexible but must include HS and NAICS identifiers.
    If no share column exists, equal weights are assigned within HS6.
    """
    raw = pd.read_csv(path, dtype=str)
    hs_col = next((col for col in raw.columns if col.lower() in {"hs6", "hs", "commodity", "commodity_code"}), None)
    naics_col = next((col for col in raw.columns if "naics" in col.lower()), None)
    if hs_col is None or naics_col is None:
        raise ValueError("Crosswalk must include HS6 and NAICS columns.")
    share_col = next((col for col in raw.columns if col.lower() in {"share", "weight", "allocation_share"}), None)
    out = raw[[hs_col, naics_col] + ([share_col] if share_col else [])].copy()
    out = out.rename(columns={hs_col: "hs6", naics_col: "naics", share_col: "share"} if share_col else {hs_col: "hs6", naics_col: "naics"})
    out["hs6"] = out["hs6"].map(normalize_hs6)
    out["naics"] = out["naics"].str.extract(r"(\d+)")[0]
    out = out.dropna(subset=["hs6", "naics"])
    if "share" not in out.columns:
        out["share"] = 1.0 / out.groupby("hs6")["hs6"].transform("count")
    else:
        out["share"] = pd.to_numeric(out["share"], errors="coerce")
        out["share"] = out["share"].fillna(1.0 / out.groupby("hs6")["hs6"].transform("count"))
    out["share"] = out["share"] / out.groupby("hs6")["share"].transform("sum")
    return out[["hs6", "naics", "share"]]


def aggregate_trade_to_naics(
    trade: pd.DataFrame,
    crosswalk: pd.DataFrame,
    value_col: str = "trade_value",
    year_col: str = "year",
    hs_col: str = "hs6",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map HS6 trade flows to NAICS and report dropped HS codes."""
    work = trade.copy()
    work["hs6"] = work[hs_col].map(normalize_hs6)
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce").fillna(0.0)
    merged = work.merge(crosswalk, on="hs6", how="left", indicator=True)
    dropped = (
        merged[merged["_merge"] == "left_only"][["hs6", year_col, value_col]]
        .drop_duplicates()
        .sort_values(["hs6", year_col])
        .reset_index(drop=True)
    )
    merged = merged[merged["_merge"] == "both"].copy()
    merged["allocated_value"] = merged[value_col] * merged["share"]
    out = merged.groupby([year_col, "naics"], as_index=False)["allocated_value"].sum()
    return out.rename(columns={year_col: "year", "allocated_value": value_col}), dropped


def industry_trade_shocks(
    trade_naics: pd.DataFrame,
    start_year: int,
    end_year: int,
    value_col: str = "trade_value",
    prefix: str = "china_import",
) -> pd.DataFrame:
    pivot = trade_naics[trade_naics["year"].isin([start_year, end_year])].pivot_table(
        index="naics", columns="year", values=value_col, aggfunc="sum", fill_value=0.0
    )
    for year in [start_year, end_year]:
        if year not in pivot.columns:
            pivot[year] = 0.0
    out = pivot.reset_index()
    out[f"delta_{prefix}"] = out[end_year] - out[start_year]
    return out[["naics", f"delta_{prefix}"]]


def build_cz_industry_shares(
    qcew_industry: pd.DataFrame,
    county_to_cz: pd.DataFrame,
    base_year: int,
    employment_col: str = "employment",
) -> pd.DataFrame:
    base = qcew_industry[qcew_industry["year"] == base_year].copy()
    base["county_fips"] = base["county_fips"].astype(str).str.zfill(5)
    if "cz" in base.columns:
        work = base.copy()
    else:
        cross = county_to_cz.copy()
        cross["county_fips"] = cross["county_fips"].astype(str).str.zfill(5)
        work = base.merge(cross[["county_fips", "cz"]], on="county_fips", how="inner")
    cz_industry = work.groupby(["cz", "naics"], as_index=False)[employment_col].sum()
    cz_total = cz_industry.groupby("cz", as_index=False)[employment_col].sum().rename(columns={employment_col: "cz_total_emp"})
    out = cz_industry.merge(cz_total, on="cz", how="left")
    out["industry_share"] = out[employment_col] / out["cz_total_emp"]
    return out


def build_trade_exposure(
    shares: pd.DataFrame,
    china_shocks: pd.DataFrame,
    instrument_shocks: pd.DataFrame,
) -> pd.DataFrame:
    work = shares.merge(china_shocks, on="naics", how="left").merge(instrument_shocks, on="naics", how="left")
    shock_col = next(col for col in china_shocks.columns if col.startswith("delta_"))
    inst_col = next(col for col in instrument_shocks.columns if col.startswith("delta_"))
    work[[shock_col, inst_col]] = work[[shock_col, inst_col]].fillna(0.0)
    work["import_exposure"] = work["industry_share"] * work[shock_col] / work["cz_total_emp"]
    work["instrument_exposure"] = work["industry_share"] * work[inst_col] / work["cz_total_emp"]
    exposure = work.groupby("cz", as_index=False)[["import_exposure", "instrument_exposure"]].sum()
    return exposure


def cz_outcome_changes(
    qcew_industry: pd.DataFrame,
    county_to_cz: pd.DataFrame,
    start_year: int,
    end_year: int,
    employment_col: str = "employment",
    wage_col: str = "wages",
) -> pd.DataFrame:
    cross = county_to_cz.copy()
    cross["county_fips"] = cross["county_fips"].astype(str).str.zfill(5)
    work = qcew_industry[qcew_industry["year"].isin([start_year, end_year])].copy()
    work["county_fips"] = work["county_fips"].astype(str).str.zfill(5)
    if "cz" not in work.columns:
        work = work.merge(cross[["county_fips", "cz"]], on="county_fips", how="inner")
    cz = work.groupby(["cz", "year"], as_index=False).agg(
        employment=(employment_col, "sum"),
        wages=(wage_col, "sum"),
    )
    pivot = cz.pivot(index="cz", columns="year", values=["employment", "wages"]).fillna(0.0)
    out = pd.DataFrame(index=pivot.index)
    out["delta_log_employment"] = np.log(pivot[("employment", end_year)].clip(lower=1)) - np.log(pivot[("employment", start_year)].clip(lower=1))
    out["delta_log_wages"] = np.log(pivot[("wages", end_year)].clip(lower=1)) - np.log(pivot[("wages", start_year)].clip(lower=1))
    out["start_employment"] = pivot[("employment", start_year)]
    return out.reset_index()


def run_shift_share_iv(
    data: pd.DataFrame,
    outcome: str = "delta_log_employment",
    endogenous: str = "import_exposure",
    instrument: str = "instrument_exposure",
) -> tuple[pd.DataFrame, str]:
    work = data.replace([np.inf, -np.inf], np.nan).dropna(subset=[outcome, endogenous, instrument])
    model = IV2SLS.from_formula(f"{outcome} ~ 1 + [{endogenous} ~ {instrument}]", data=work).fit(cov_type="robust")
    table = pd.DataFrame(
        [
            {
                "outcome": outcome,
                "endogenous": endogenous,
                "instrument": instrument,
                "estimate": model.params[endogenous],
                "std_error": model.std_errors[endogenous],
                "p_value": model.pvalues[endogenous],
                "nobs": int(model.nobs),
            }
        ]
    )
    return table, str(model.first_stage)


def rotemberg_weights(shares: pd.DataFrame, instrument_shocks: pd.DataFrame) -> pd.DataFrame:
    """Approximate industry influence weights for shift-share identification."""
    inst_col = next(col for col in instrument_shocks.columns if col.startswith("delta_"))
    work = shares.merge(instrument_shocks, on="naics", how="left").fillna({inst_col: 0.0})
    work["component"] = work["industry_share"] * work[inst_col]
    weights = work.groupby("naics", as_index=False)["component"].sum()
    denom = weights["component"].abs().sum()
    weights["rotemberg_weight_abs"] = weights["component"].abs() / denom if denom else 0.0
    return weights.sort_values("rotemberg_weight_abs", ascending=False)


def validate_exposure_against_reference(exposure: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    merged = exposure.merge(reference, on="cz", suffixes=("_built", "_reference"))
    corr = merged["import_exposure_built"].corr(merged["import_exposure_reference"]) if len(merged) > 1 else np.nan
    return pd.DataFrame([{"matched_cz": len(merged), "correlation": corr}])
