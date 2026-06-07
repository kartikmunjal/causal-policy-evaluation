"""Synthetic-control robustness and placebo inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def fit_simple_synth(
    df: pd.DataFrame,
    treated_unit: str,
    outcome: str = "log_employment",
    unit: str = "county_fips",
    time: str = "year",
    treatment_year: int = 2019,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Non-negative least-squares synthetic control fallback.

    pysyncon is used by the CLI when installed; this compact fallback keeps smoke
    tests deterministic and documents the exact donor-weight target.
    """
    panel = df.groupby([unit, time], as_index=False)[outcome].mean()
    pre = panel[panel[time] < treatment_year]
    pivot = pre.pivot(index=time, columns=unit, values=outcome).dropna(axis=1)
    donors = [col for col in pivot.columns if col != treated_unit]
    if treated_unit not in pivot or not donors:
        raise ValueError("Need one treated unit and at least one donor with complete pre-period data.")
    y = pivot[treated_unit].to_numpy()
    x = pivot[donors].to_numpy()
    weights, *_ = np.linalg.lstsq(x, y, rcond=None)
    weights = np.clip(weights, 0, None)
    weights = weights / weights.sum() if weights.sum() > 0 else np.repeat(1 / len(donors), len(donors))
    full = panel[panel[unit].isin([treated_unit, *donors])].pivot(index=time, columns=unit, values=outcome)
    synth = full[donors].to_numpy() @ weights
    paths = pd.DataFrame({"year": full.index, "treated": full[treated_unit].to_numpy(), "synthetic": synth})
    paths.attrs["treatment_year"] = treatment_year
    weights_df = pd.DataFrame({"donor_unit": donors, "weight": weights})
    return paths, weights_df


def placebo_permutation_gaps(
    df: pd.DataFrame,
    outcome: str = "log_employment",
    unit: str = "county_fips",
    time: str = "year",
    treatment_year: int = 2019,
) -> pd.DataFrame:
    rows = []
    for candidate in sorted(df[unit].unique()):
        try:
            paths, _ = fit_simple_synth(df, candidate, outcome=outcome, unit=unit, time=time, treatment_year=treatment_year)
        except ValueError:
            continue
        post = paths[paths["year"] >= treatment_year]
        pre = paths[paths["year"] < treatment_year]
        rows.append(
            {
                "placebo_unit": candidate,
                "post_mean_gap": float((post["treated"] - post["synthetic"]).mean()),
                "pre_rmspe": float(np.sqrt(np.mean((pre["treated"] - pre["synthetic"]) ** 2))),
                "post_rmspe": float(np.sqrt(np.mean((post["treated"] - post["synthetic"]) ** 2))),
            }
        )
    out = pd.DataFrame(rows)
    if not out.empty:
        treated_abs = out["post_mean_gap"].abs().iloc[0]
        out["permutation_p_value"] = (out["post_mean_gap"].abs() >= treated_abs).mean()
    return out


def save_synth_outputs(paths: pd.DataFrame, weights: pd.DataFrame, placebo: pd.DataFrame, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    paths.to_csv(report_dir / "synthetic_paths.csv", index=False)
    weights.to_csv(report_dir / "synthetic_weights.csv", index=False)
    placebo.to_csv(report_dir / "synthetic_placebos.csv", index=False)
