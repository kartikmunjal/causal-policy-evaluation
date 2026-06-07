"""Shift-share instrument construction and 2SLS estimation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.iv import IV2SLS


def add_bartik_instrument(
    df: pd.DataFrame,
    outcome_col: str = "log_wages",
    unit: str = "county_fips",
    time: str = "year",
) -> pd.DataFrame:
    """Construct a compact Bartik-style instrument from baseline shares and aggregate shocks.

    In the full data build, replace sector shares with ACS/QCEW industry shares and shocks
    with national CES industry growth excluding the local area.
    """
    work = df.copy()
    baseline_year = int(work[time].min())
    baseline = (
        work[work[time] == baseline_year]
        .groupby(unit, as_index=False)
        .agg(baseline_emp=("employment", "mean"))
    )
    total_by_year = work.groupby(time)["employment"].sum().rename("national_emp")
    shock = np.log(total_by_year).diff().fillna(0).rename("aggregate_labor_demand_shock").reset_index()
    work = work.merge(baseline, on=unit, how="left").merge(shock, on=time, how="left")
    work["baseline_share"] = work["baseline_emp"] / work.groupby(time)["baseline_emp"].transform("sum")
    work["bartik"] = work["baseline_share"] * work["aggregate_labor_demand_shock"]
    work["endogenous_labor_demand"] = work.groupby(unit)[outcome_col].diff().fillna(0)
    return work


def run_2sls(
    df: pd.DataFrame,
    dependent: str = "log_employment",
    endogenous: str = "endogenous_labor_demand",
    instrument: str = "bartik",
) -> tuple[pd.DataFrame, str]:
    work = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[dependent, endogenous, instrument, "state"])
    model = IV2SLS.from_formula(
        f"{dependent} ~ 1 + C(year) + [ {endogenous} ~ {instrument} ]",
        data=work,
    ).fit(cov_type="clustered", clusters=work["state"])
    table = pd.DataFrame(
        [
            {
                "term": endogenous,
                "estimate": model.params[endogenous],
                "std_error": model.std_errors[endogenous],
                "p_value": model.pvalues[endogenous],
                "nobs": int(model.nobs),
            }
        ]
    )
    return table, str(model.first_stage)


def save_iv_outputs(table: pd.DataFrame, first_stage: str, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(report_dir / "iv_2sls.csv", index=False)
    (report_dir / "iv_first_stage.txt").write_text(first_stage + "\n", encoding="utf-8")
