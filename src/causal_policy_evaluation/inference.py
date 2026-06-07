"""Inference diagnostics for DiD designs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from causal_policy_evaluation.did import add_event_time_dummies


def cluster_count(df: pd.DataFrame, cluster: str = "state") -> pd.DataFrame:
    return pd.DataFrame(
        [{"cluster": cluster, "n_clusters": int(df[cluster].nunique()), "warning": df[cluster].nunique() < 30}]
    )


def joint_pretrend_test(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    cluster: str = "state",
    min_lag: int = -4,
    max_lead: int = 3,
) -> pd.DataFrame:
    work, terms = add_event_time_dummies(df, min_lag=min_lag, max_lead=max_lead)
    pre_terms = [term for term in terms if term.startswith("event_m")]
    formula = f"{outcome} ~ {' + '.join(terms)} + C(county_fips) + C(year) + C(pair_id)"
    model = smf.ols(formula, data=work).fit(cov_type="cluster", cov_kwds={"groups": work[cluster]})
    if not pre_terms:
        return pd.DataFrame([{"test": "joint_pretrend", "statistic": np.nan, "p_value": np.nan, "df_num": 0}])
    hypothesis = " = 0, ".join(pre_terms) + " = 0"
    try:
        test = model.f_test(hypothesis)
        return pd.DataFrame(
            [
                {
                    "test": "joint_pretrend",
                    "statistic": float(test.statistic),
                    "p_value": float(test.pvalue),
                    "df_num": int(test.df_num),
                    "warning": bool(df[cluster].nunique() < 30),
                }
            ]
        )
    except Exception as exc:
        return pd.DataFrame(
            [{"test": "joint_pretrend", "statistic": np.nan, "p_value": np.nan, "df_num": len(pre_terms), "warning": str(exc)}]
        )


def placebo_policy_years(
    df: pd.DataFrame,
    placebo_years: list[int],
    outcome: str = "log_employment",
    cluster: str = "state",
) -> pd.DataFrame:
    rows = []
    for year in placebo_years:
        work = df.copy()
        work["_placebo_post"] = (work["year"] >= year).astype(int)
        model = smf.ols(
            f"{outcome} ~ treated:_placebo_post + C(county_fips) + C(year) + C(pair_id)",
            data=work,
        ).fit(cov_type="cluster", cov_kwds={"groups": work[cluster]})
        term = "treated:_placebo_post"
        rows.append(
            {
                "placebo_year": year,
                "estimate": model.params.get(term, np.nan),
                "std_error": model.bse.get(term, np.nan),
                "p_value": model.pvalues.get(term, np.nan),
                "warning": bool(df[cluster].nunique() < 30),
            }
        )
    return pd.DataFrame(rows)


def wild_cluster_bootstrap_did(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    term: str = "treated:post",
    cluster: str = "state",
    reps: int = 499,
    seed: int = 11,
) -> pd.DataFrame:
    """Rademacher wild-cluster bootstrap for the validation DiD coefficient."""
    formula = f"{outcome} ~ treated:post + C(county_fips) + C(year) + C(pair_id)"
    base = smf.ols(formula, data=df).fit()
    observed = float(base.params.get(term, np.nan))
    fitted = base.fittedvalues.to_numpy()
    residuals = base.resid.to_numpy()
    clusters = df[cluster].to_numpy()
    rng = np.random.default_rng(seed)
    boot = []
    unique_clusters = np.unique(clusters)
    for _ in range(reps):
        weights = dict(zip(unique_clusters, rng.choice([-1, 1], size=len(unique_clusters))))
        y_star = fitted + residuals * np.array([weights[item] for item in clusters])
        work = df.copy()
        work["_boot_y"] = y_star
        boot_model = smf.ols(formula.replace(outcome, "_boot_y", 1), data=work).fit()
        boot.append(float(boot_model.params.get(term, np.nan)))
    boot = np.array(boot)
    p_value = float(np.mean(np.abs(boot - np.nanmean(boot)) >= abs(observed - np.nanmean(boot))))
    return pd.DataFrame(
        [
            {
                "term": term,
                "estimate": observed,
                "bootstrap_p_value": p_value,
                "reps": reps,
                "n_clusters": int(len(unique_clusters)),
                "warning": len(unique_clusters) < 30,
            }
        ]
    )
