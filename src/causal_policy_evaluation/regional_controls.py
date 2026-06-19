"""Merge regional nowcast controls into causal-policy panels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .economics import add_economic_margins


REGIONAL_CONTROL_COLUMNS = [
    "avg_activity_index",
    "avg_activity_momentum",
    "avg_activity_percentile",
    "avg_negative_indicator_breadth",
    "gdp_qoq_ann",
    "avg_activity_surprise",
    "avg_abs_error_improvement_vs_benchmark",
    "avg_available_indicator_share",
]


def load_regional_policy_controls(path: str | Path) -> pd.DataFrame:
    controls = pd.read_csv(path)
    required = {"state", "year"}
    missing = required - set(controls.columns)
    if missing:
        raise ValueError(f"Regional controls missing required columns: {sorted(missing)}")
    controls["state"] = controls["state"].astype(str)
    controls["year"] = controls["year"].astype(int)
    keep = ["state", "year"] + [c for c in REGIONAL_CONTROL_COLUMNS if c in controls.columns]
    return controls[keep].replace([np.inf, -np.inf], np.nan)


def merge_regional_controls(panel: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    """Merge state-year controls and add one-year lags."""
    work = panel.copy()
    work["state"] = work["state"].astype(str)
    work["year"] = work["year"].astype(int)
    out = work.merge(controls, on=["state", "year"], how="left", indicator="regional_control_match")
    out["has_regional_controls"] = out["regional_control_match"].eq("both")
    out = out.drop(columns=["regional_control_match"])
    lagged = controls.copy()
    lagged["year"] = lagged["year"] + 1
    lagged = lagged.rename(columns={col: f"lag_{col}" for col in controls.columns if col not in {"state", "year"}})
    out = out.merge(lagged, on=["state", "year"], how="left")
    return out


def regional_control_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "sample": "all_rows",
            "rows": len(panel),
            "matched_rows": int(panel["has_regional_controls"].sum()) if "has_regional_controls" in panel else 0,
            "matched_share": float(panel["has_regional_controls"].mean()) if "has_regional_controls" in panel else 0.0,
            "states": int(panel["state"].nunique()),
            "matched_states": int(panel.loc[panel.get("has_regional_controls", False), "state"].nunique()) if "has_regional_controls" in panel else 0,
        }
    ]
    if "treated" in panel:
        for value, label in [(1, "treated_rows"), (0, "control_rows")]:
            group = panel[panel["treated"].eq(value)]
            rows.append(
                {
                    "sample": label,
                    "rows": len(group),
                    "matched_rows": int(group["has_regional_controls"].sum()) if "has_regional_controls" in group else 0,
                    "matched_share": float(group["has_regional_controls"].mean()) if len(group) and "has_regional_controls" in group else 0.0,
                    "states": int(group["state"].nunique()),
                    "matched_states": int(group.loc[group.get("has_regional_controls", False), "state"].nunique()) if "has_regional_controls" in group else 0,
                }
            )
    return pd.DataFrame(rows)


def _fit_formula(data: pd.DataFrame, formula: str, term: str, cluster: str = "state") -> dict:
    try:
        model = smf.ols(formula, data=data)
        if cluster in data.columns and data[cluster].nunique() > 1:
            fit = model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster]})
            covariance = f"clustered_{cluster}"
        else:
            fit = model.fit(cov_type="HC1")
            covariance = "hc1"
        return {
            "estimate": fit.params.get(term, np.nan),
            "std_error": fit.bse.get(term, np.nan),
            "p_value": fit.pvalues.get(term, np.nan),
            "nobs": int(fit.nobs),
            "covariance": covariance,
            "status": "ok",
        }
    except Exception as exc:
        return {"estimate": np.nan, "std_error": np.nan, "p_value": np.nan, "nobs": len(data), "covariance": "", "status": f"failed: {exc}"}


def estimate_regional_cycle_adjusted_did(panel: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Estimate DiD robustness specs with lagged regional-cycle controls."""
    work = add_economic_margins(panel)
    controls = ["lag_avg_activity_index", "lag_avg_activity_momentum", "lag_avg_negative_indicator_breadth", "lag_gdp_qoq_ann"]
    outcomes = ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]
    rows = []
    for outcome in outcomes:
        required = [outcome, "treated", "post", "county_fips", "year", "pair_id", cluster, *controls]
        model_data = work.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
        formula = f"{outcome} ~ treated:post + {' + '.join(controls)} + C(county_fips) + C(year) + C(pair_id)"
        result = _fit_formula(model_data, formula, "treated:post", cluster)
        rows.append({"outcome": outcome, "term": "treated:post", "specification": "lagged_regional_cycle_controls", **result})
    return pd.DataFrame(rows)


def estimate_activity_surprise_heterogeneity(panel: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Test whether effects differ in high-surprise regional years."""
    work = add_economic_margins(panel)
    work["treated_post_x_lag_surprise"] = work["treated"] * work["post"] * work["lag_avg_activity_surprise"]
    outcomes = ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]
    rows = []
    controls = ["lag_avg_activity_index", "lag_avg_activity_momentum", "lag_avg_negative_indicator_breadth"]
    for outcome in outcomes:
        term = "treated_post_x_lag_surprise"
        required = [outcome, "treated", "post", term, "county_fips", "year", "pair_id", cluster, *controls]
        model_data = work.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
        formula = f"{outcome} ~ treated:post + {term} + {' + '.join(controls)} + C(county_fips) + C(year) + C(pair_id)"
        result = _fit_formula(model_data, formula, term, cluster)
        rows.append({"outcome": outcome, "term": term, "specification": "lagged_activity_surprise_interaction", **result})
    return pd.DataFrame(rows)


def estimate_excluding_high_surprise_years(panel: pd.DataFrame, cluster: str = "state", quantile: float = 0.75) -> pd.DataFrame:
    """Re-estimate after dropping state-years with large lagged nowcast surprises."""
    work = add_economic_margins(panel).replace([np.inf, -np.inf], np.nan)
    threshold = work["lag_avg_activity_surprise"].abs().quantile(quantile)
    filtered = work[work["lag_avg_activity_surprise"].abs().le(threshold)].copy()
    outcomes = ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]
    rows = []
    for outcome in outcomes:
        required = [outcome, "treated", "post", "county_fips", "year", "pair_id", cluster]
        model_data = filtered.dropna(subset=required)
        formula = f"{outcome} ~ treated:post + C(county_fips) + C(year) + C(pair_id)"
        result = _fit_formula(model_data, formula, "treated:post", cluster)
        rows.append(
            {
                "outcome": outcome,
                "term": "treated:post",
                "specification": f"exclude_abs_lag_surprise_above_p{int(quantile * 100)}",
                "excluded_threshold": threshold,
                **result,
            }
        )
    return pd.DataFrame(rows)
