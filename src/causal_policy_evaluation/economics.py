"""Economics-focused margins, mechanisms, and heterogeneity tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


HOURS_PER_YEAR = 2080


def _drop_model_missing(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.replace([np.inf, -np.inf], np.nan).dropna(subset=cols)


def add_economic_margins(df: pd.DataFrame, treated_min_wage: float = 10.0, control_min_wage: float = 7.25) -> pd.DataFrame:
    """Add interpretable economic margins and a policy-bite measure.

    The validation panel only has NJ/PA. For the national panel, pass in data
    with a `minimum_wage` column and this function will use it directly.
    """
    out = df.copy()
    if "minimum_wage" not in out.columns:
        out["minimum_wage"] = np.where(out["treated"].eq(1), treated_min_wage, control_min_wage)
    out["avg_annual_pay"] = out["wages"] / out["employment"].replace(0, np.nan)
    out["avg_hourly_pay"] = out["avg_annual_pay"] / HOURS_PER_YEAR
    out["emp_per_establishment"] = out["employment"] / out["establishments"].replace(0, np.nan)
    out["minimum_wage_bite"] = out["minimum_wage"] / out["avg_hourly_pay"]
    out["policy_dose"] = out["minimum_wage_bite"].where(out["treated"].eq(1), 0.0)
    for col in ["establishments", "emp_per_establishment", "avg_annual_pay", "avg_hourly_pay"]:
        out[f"log_{col}"] = np.log(out[col].clip(lower=1e-9))
    return out


def add_preperiod_heterogeneity(df: pd.DataFrame, pre_end_year: int = 2018) -> pd.DataFrame:
    """Classify counties by pre-period size and growth proxies."""
    out = add_economic_margins(df)
    pre = out[out["year"] <= pre_end_year].copy()
    base_year = int(pre["year"].min())
    base = (
        pre[pre["year"] == base_year]
        .groupby("county_fips", as_index=False)
        .agg(baseline_emp_per_estab=("emp_per_establishment", "mean"), baseline_employment=("employment", "mean"))
    )
    growth = (
        pre.sort_values(["county_fips", "year"])
        .groupby("county_fips")
        .agg(pre_first=("employment", "first"), pre_last=("employment", "last"))
        .reset_index()
    )
    growth["pre_emp_growth"] = np.log(growth["pre_last"].clip(lower=1)) - np.log(growth["pre_first"].clip(lower=1))
    out = out.merge(base, on="county_fips", how="left").merge(growth[["county_fips", "pre_emp_growth"]], on="county_fips", how="left")
    out["large_establishment_county"] = (
        out["baseline_emp_per_estab"] >= out["baseline_emp_per_estab"].median()
    ).astype(int)
    out["high_pregrowth_county"] = (out["pre_emp_growth"] >= out["pre_emp_growth"].median()).astype(int)
    return out


def estimate_margin_decomposition(df: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Estimate the validation DiD across economically meaningful margins."""
    work = add_economic_margins(df)
    outcomes = {
        "log_employment": "Employment",
        "log_establishments": "Establishments",
        "log_emp_per_establishment": "Employment per establishment",
        "log_avg_annual_pay": "Average annual pay",
    }
    rows = []
    for outcome, label in outcomes.items():
        model_data = _drop_model_missing(work, [outcome, "treated", "post", "county_fips", "year", "pair_id", cluster])
        model = smf.ols(
            f"{outcome} ~ treated:post + C(county_fips) + C(year) + C(pair_id)",
            data=model_data,
        ).fit(cov_type="cluster", cov_kwds={"groups": model_data[cluster]})
        term = "treated:post"
        rows.append(
            {
                "outcome": outcome,
                "label": label,
                "estimate": model.params.get(term, np.nan),
                "std_error": model.bse.get(term, np.nan),
                "p_value": model.pvalues.get(term, np.nan),
                "nobs": int(model.nobs),
                "interpretation": "log-point DiD effect",
            }
        )
    return pd.DataFrame(rows)


def estimate_bite_dose_response(df: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Estimate whether higher minimum-wage bite predicts larger employment responses."""
    work = add_economic_margins(df)
    work["post_x_bite"] = work["post"] * work["policy_dose"]
    rows = []
    for outcome in ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]:
        model_data = _drop_model_missing(work, [outcome, "post_x_bite", "county_fips", "year", "pair_id", cluster])
        model = smf.ols(
            f"{outcome} ~ post_x_bite + C(county_fips) + C(year) + C(pair_id)",
            data=model_data,
        ).fit(cov_type="cluster", cov_kwds={"groups": model_data[cluster]})
        rows.append(
            {
                "outcome": outcome,
                "term": "post_x_bite",
                "estimate": model.params.get("post_x_bite", np.nan),
                "std_error": model.bse.get("post_x_bite", np.nan),
                "p_value": model.pvalues.get("post_x_bite", np.nan),
                "mean_treated_bite": model_data.loc[model_data["treated"].eq(1), "minimum_wage_bite"].mean(),
                "nobs": int(model.nobs),
            }
        )
    return pd.DataFrame(rows)


def estimate_heterogeneity(df: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Test whether responses differ by baseline establishment scale and pre-growth."""
    work = add_preperiod_heterogeneity(df)
    rows = []
    for hetero in ["large_establishment_county", "high_pregrowth_county"]:
        work[f"treated_post_x_{hetero}"] = work["treated"] * work["post"] * work[hetero]
        for outcome in ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]:
            term = f"treated_post_x_{hetero}"
            model_data = _drop_model_missing(
                work,
                [outcome, "treated", "post", term, "county_fips", "year", "pair_id", cluster],
            )
            model = smf.ols(
                f"{outcome} ~ treated:post + {term} + C(county_fips) + C(year) + C(pair_id)",
                data=model_data,
            ).fit(cov_type="cluster", cov_kwds={"groups": model_data[cluster]})
            rows.append(
                {
                    "outcome": outcome,
                    "heterogeneity_dimension": hetero,
                    "base_treated_post": model.params.get("treated:post", np.nan),
                    "interaction_estimate": model.params.get(term, np.nan),
                    "interaction_std_error": model.bse.get(term, np.nan),
                    "interaction_p_value": model.pvalues.get(term, np.nan),
                    "nobs": int(model.nobs),
                }
            )
    return pd.DataFrame(rows)


def assess_border_spillover_identification(df: pd.DataFrame) -> pd.DataFrame:
    """Report whether a border-spillover test is identified in the available panel."""
    has_unexposed_controls = "spillover_exposed" in df.columns and df.loc[df["treated"].eq(0), "spillover_exposed"].nunique() > 1
    if not has_unexposed_controls:
        return pd.DataFrame(
            [
                {
                    "test": "control_side_border_spillover",
                    "identified": False,
                    "reason": "Validation panel contains only border controls exposed to the neighboring treated state; add interior or unexposed border controls for this test.",
                }
            ]
        )
    work = df.copy()
    work["control_spillover_post"] = (work["treated"].eq(0) & work["spillover_exposed"].eq(1) & work["post"].eq(1)).astype(int)
    model = smf.ols("log_employment ~ control_spillover_post + C(county_fips) + C(year)", data=work).fit()
    return pd.DataFrame(
        [
            {
                "test": "control_side_border_spillover",
                "identified": True,
                "estimate": model.params.get("control_spillover_post", np.nan),
                "std_error": model.bse.get("control_spillover_post", np.nan),
                "p_value": model.pvalues.get("control_spillover_post", np.nan),
            }
        ]
    )


def specification_curve(df: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    """Run a compact specification curve across outcomes, windows, and weights."""
    work = add_economic_margins(df)
    rows = []
    outcomes = ["log_employment", "log_establishments", "log_emp_per_establishment", "log_avg_annual_pay"]
    windows = {
        "full": work,
        "drop_2020": work[work["year"] != 2020],
        "balanced_2016_2022": work[work["year"].between(2016, 2022)],
    }
    for outcome in outcomes:
        for window_name, frame in windows.items():
            for weighted in [False, True]:
                required = [outcome, "treated", "post", "county_fips", "year", "pair_id", cluster]
                if weighted:
                    required.append("baseline_employment" if "baseline_employment" in frame.columns else "employment")
                model_data = _drop_model_missing(frame, required)
                kwargs = {}
                if weighted:
                    kwargs["weights"] = model_data["baseline_employment"] if "baseline_employment" in model_data.columns else model_data["employment"]
                    fit = smf.wls
                else:
                    fit = smf.ols
                try:
                    model = fit(
                        f"{outcome} ~ treated:post + C(county_fips) + C(year) + C(pair_id)",
                        data=model_data,
                        **kwargs,
                    ).fit(cov_type="cluster", cov_kwds={"groups": model_data[cluster]})
                    rows.append(
                        {
                            "outcome": outcome,
                            "window": window_name,
                            "weighted": weighted,
                            "estimate": model.params.get("treated:post", np.nan),
                            "std_error": model.bse.get("treated:post", np.nan),
                            "p_value": model.pvalues.get("treated:post", np.nan),
                            "nobs": int(model.nobs),
                            "status": "ok",
                        }
                    )
                except Exception as exc:
                    rows.append(
                        {
                            "outcome": outcome,
                            "window": window_name,
                            "weighted": weighted,
                            "estimate": np.nan,
                            "std_error": np.nan,
                            "p_value": np.nan,
                            "nobs": len(model_data),
                            "status": f"failed: {exc}",
                        }
                    )
    return pd.DataFrame(rows)


def save_research_outputs(outputs: dict[str, pd.DataFrame], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(report_dir / f"{name}.csv", index=False)
