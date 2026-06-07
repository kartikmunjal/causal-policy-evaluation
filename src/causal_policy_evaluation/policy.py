"""Minimum-wage policy table schema, validation, and cohort construction."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


POLICY_COLUMNS = [
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


def policy_seed() -> pd.DataFrame:
    """Return audited seed rows for the validation design.

    National-scale research should extend this table row-by-row from DOL/state
    sources. The validator below deliberately fails if rows are missing source
    URLs or are not marked verified.
    """
    rows = [
        {
            "state": "NJ",
            "effective_date": "2019-07-01",
            "old_minimum_wage": 8.85,
            "new_minimum_wage": 10.00,
            "nominal_change": 1.15,
            "pct_change": 1.15 / 8.85,
            "policy_year": 2019,
            "source_url": "https://www.nj.gov/labor/wageandhour/tools-resources/laws/minimum-wage.shtml",
            "source_name": "New Jersey Department of Labor minimum wage schedule",
            "verified": True,
            "notes": "Validation treatment. Later scheduled increases should be modeled as separate dose changes.",
        },
        {
            "state": "PA",
            "effective_date": "",
            "old_minimum_wage": 7.25,
            "new_minimum_wage": 7.25,
            "nominal_change": 0.00,
            "pct_change": 0.00,
            "policy_year": 0,
            "source_url": "https://www.dol.gov/agencies/whd/state/minimum-wage/history",
            "source_name": "US Department of Labor state minimum wage history",
            "verified": True,
            "notes": "Validation comparison state retained the federal minimum in the 2019 window.",
        },
    ]
    return pd.DataFrame(rows, columns=POLICY_COLUMNS)


def write_policy_seed(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    policy_seed().to_csv(path, index=False)
    return path


def load_policy_table(path: Path) -> pd.DataFrame:
    policy = pd.read_csv(path, dtype={"state": str, "source_url": str, "source_name": str, "notes": str})
    missing = [col for col in POLICY_COLUMNS if col not in policy.columns]
    if missing:
        raise ValueError(f"Policy table is missing required columns: {missing}")
    policy["state"] = policy["state"].str.upper()
    policy["verified"] = policy["verified"].astype(bool)
    policy["policy_year"] = policy["policy_year"].fillna(0).astype(int)
    return policy[POLICY_COLUMNS]


def validate_policy_table(policy: pd.DataFrame, require_verified: bool = True) -> pd.DataFrame:
    checks = []
    for idx, row in policy.iterrows():
        errors = []
        if not row["state"] or len(str(row["state"])) != 2:
            errors.append("state must be a two-letter USPS abbreviation")
        if row["policy_year"] and not str(row["effective_date"]):
            errors.append("treated rows require an effective_date")
        if row["policy_year"] and pd.isna(row["new_minimum_wage"]):
            errors.append("treated rows require new_minimum_wage")
        if not str(row["source_url"]).startswith("http"):
            errors.append("source_url must be an http(s) URL")
        if require_verified and not bool(row["verified"]):
            errors.append("row is not marked verified")
        checks.append({"row": idx, "state": row["state"], "valid": not errors, "errors": "; ".join(errors)})
    return pd.DataFrame(checks)


def first_treatment_cohorts(policy: pd.DataFrame, min_change: float = 0.0) -> pd.DataFrame:
    treated = policy[(policy["policy_year"] > 0) & (policy["nominal_change"] > min_change)].copy()
    treated = treated.sort_values(["state", "effective_date"])
    cohorts = treated.groupby("state", as_index=False).first()[["state", "policy_year", "effective_date", "nominal_change"]]
    return cohorts.rename(columns={"policy_year": "first_treat_year"})


def attach_policy_cohorts(panel: pd.DataFrame, policy: pd.DataFrame, state_col: str = "state") -> pd.DataFrame:
    cohorts = first_treatment_cohorts(policy)
    out = panel.merge(cohorts, left_on=state_col, right_on="state", how="left", suffixes=("", "_policy"))
    out["policy_year"] = out["first_treat_year"]
    out["relative_year"] = out["year"] - out["policy_year"]
    out.loc[out["policy_year"].isna(), "relative_year"] = pd.NA
    out["post"] = ((out["policy_year"].notna()) & (out["year"] >= out["policy_year"])).astype(int)
    out["treated"] = out["policy_year"].notna().astype(int)
    return out.drop(columns=[col for col in ["state_policy"] if col in out.columns])
