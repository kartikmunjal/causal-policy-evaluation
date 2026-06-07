"""Difference-in-differences estimators and event-study helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def add_event_time_dummies(
    df: pd.DataFrame,
    rel_col: str = "relative_year",
    treated_col: str = "treated",
    min_lag: int = -4,
    max_lead: int = 3,
    omitted: int = -1,
) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy()
    terms: list[str] = []
    for rel in range(min_lag, max_lead + 1):
        if rel == omitted:
            continue
        name = f"event_m{abs(rel)}" if rel < 0 else f"event_p{rel}"
        out[name] = ((out[rel_col] == rel) & (out[treated_col] == 1)).astype(int)
        terms.append(name)
    return out, terms


def run_event_study(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    cluster: str = "state",
    min_lag: int = -4,
    max_lead: int = 3,
) -> pd.DataFrame:
    work, terms = add_event_time_dummies(df, min_lag=min_lag, max_lead=max_lead)
    formula = f"{outcome} ~ {' + '.join(terms)} + C(county_fips) + C(year) + C(pair_id)"
    model = smf.ols(formula, data=work).fit(cov_type="cluster", cov_kwds={"groups": work[cluster]})
    rows = []
    for term in terms:
        rel = -int(term.split("m")[1]) if term.startswith("event_m") else int(term.split("p")[1])
        rows.append(
            {
                "term": term,
                "relative_year": rel,
                "estimate": model.params.get(term, np.nan),
                "std_error": model.bse.get(term, np.nan),
                "p_value": model.pvalues.get(term, np.nan),
            }
        )
    result = pd.DataFrame(rows).sort_values("relative_year")
    result["ci_low"] = result["estimate"] - 1.96 * result["std_error"]
    result["ci_high"] = result["estimate"] + 1.96 * result["std_error"]
    return result


def pretrend_summary(event_study: pd.DataFrame) -> pd.DataFrame:
    pre = event_study[event_study["relative_year"] < 0].copy()
    pre["passes_10pct_screen"] = pre["p_value"] > 0.10
    return pre


def run_callaway_santanna(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    unit: str = "county_fips",
    time: str = "year",
    cohort: str = "policy_year",
) -> pd.DataFrame:
    """Run Callaway-Sant'Anna ATT(g,t) with the differences package.

    The dependency is optional at import time so tests can exercise the rest of the
    project even when compiled econometrics dependencies are not installed.
    """
    try:
        from differences import ATTgt
    except Exception as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install requirements.txt to run Callaway-Sant'Anna estimation.") from exc

    work = df.copy()
    work[cohort] = work[cohort].fillna(0).astype(int)
    att = ATTgt(data=work, cohort_name=cohort, strata_name=unit)
    att.fit(formula=f"{outcome} ~ 1", est_method="dr", base_period="universal", time_name=time)
    dynamic = att.aggregate("event")
    if hasattr(dynamic, "reset_index"):
        return dynamic.reset_index()
    return pd.DataFrame(dynamic)


def run_pyfixest_lpdid(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    unit: str = "county_fips",
    time: str = "year",
    cohort: str = "policy_year",
    cluster: str = "state",
    pre_window: int = 4,
    post_window: int = 3,
) -> pd.DataFrame:
    """Run pyfixest's local-projections DiD estimator for staggered timing."""
    try:
        import pyfixest as pf
    except Exception as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install requirements.txt to run pyfixest staggered DiD.") from exc

    work = df.copy()
    work["_cohort"] = work[cohort].fillna(0).astype(int)
    result = pf.lpdid(
        work,
        yname=outcome,
        idname=unit,
        tname=time,
        gname="_cohort",
        vcov={"CRV1": cluster},
        pre_window=pre_window,
        post_window=post_window,
        never_treated=0,
    )
    tidy = result.tidy().reset_index(names="term")
    tidy = tidy.rename(
        columns={
            "Estimate": "estimate",
            "Std. Error": "std_error",
            "Pr(>|t|)": "p_value",
            "2.5%": "ci_low",
            "97.5%": "ci_high",
        }
    )
    tidy.insert(0, "estimator", "pyfixest_lpdid")
    return tidy


def run_border_pair_did(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    cluster: str = "state",
) -> pd.DataFrame:
    """Simple validation DiD for one treated cohort, not the final staggered estimator."""
    model = smf.ols(
        f"{outcome} ~ treated:post + C(county_fips) + C(year) + C(pair_id)",
        data=df,
    ).fit(cov_type="cluster", cov_kwds={"groups": df[cluster]})
    return pd.DataFrame(
        [
            {
                "estimator": "single_cohort_border_pair_did",
                "term": "treated:post",
                "estimate": model.params["treated:post"],
                "std_error": model.bse["treated:post"],
                "p_value": model.pvalues["treated:post"],
                "nobs": int(model.nobs),
            }
        ]
    )


def save_table(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
