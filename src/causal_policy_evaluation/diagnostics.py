"""Design diagnostics and robustness summaries."""

from __future__ import annotations

import pandas as pd


def raw_trends(df: pd.DataFrame, outcome: str = "log_employment") -> pd.DataFrame:
    return (
        df.groupby(["treated", "year"], as_index=False)
        .agg(mean_outcome=(outcome, "mean"), n_county_pairs=("pair_id", "nunique"), n_counties=("county_fips", "nunique"))
        .sort_values(["treated", "year"])
    )


def balance_table(df: pd.DataFrame) -> pd.DataFrame:
    base_year = int(df["year"].min())
    base = df[df["year"] == base_year].copy()
    rows = []
    for col in ["employment", "wages", "establishments"]:
        treated = base.loc[base["treated"] == 1, col].mean()
        control = base.loc[base["treated"] == 0, col].mean()
        rows.append(
            {
                "baseline_year": base_year,
                "variable": col,
                "treated_mean": treated,
                "control_mean": control,
                "difference": treated - control,
                "ratio": treated / control if control else pd.NA,
            }
        )
    return pd.DataFrame(rows)


def leave_one_state_out(df: pd.DataFrame, estimate_fn) -> pd.DataFrame:
    rows = []
    for state in sorted(df["state"].dropna().unique()):
        work = df[df["state"] != state]
        if work["state"].nunique() < 2:
            rows.append({"left_out_state": state, "estimate": pd.NA, "note": "fewer than two states remain"})
            continue
        try:
            result = estimate_fn(work).iloc[0].to_dict()
            result["left_out_state"] = state
            rows.append(result)
        except Exception as exc:
            rows.append({"left_out_state": state, "estimate": pd.NA, "note": str(exc)})
    return pd.DataFrame(rows)
