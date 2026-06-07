from pathlib import Path

import pandas as pd

from causal_policy_evaluation.data import build_nj_pa_border_panel, make_smoke_panel
from causal_policy_evaluation.did import pretrend_summary, run_border_pair_did, run_event_study
from causal_policy_evaluation.diagnostics import balance_table, raw_trends
from causal_policy_evaluation.economics import (
    add_economic_margins,
    assess_border_spillover_identification,
    estimate_bite_dose_response,
    estimate_heterogeneity,
    estimate_margin_decomposition,
    specification_curve,
)
from causal_policy_evaluation.geography import build_state_border_pairs
from causal_policy_evaluation.inference import cluster_count, joint_pretrend_test, placebo_policy_years
from causal_policy_evaluation.plots import plot_event_study
from causal_policy_evaluation.policy import policy_seed, validate_policy_table
from causal_policy_evaluation.synthetic_control import fit_simple_synth, placebo_permutation_gaps


def test_smoke_panel_has_expected_design_columns():
    df = make_smoke_panel()
    assert {"county_fips", "year", "treated", "post", "relative_year", "log_employment"}.issubset(df.columns)
    assert df["treated"].sum() > 0
    assert df["post"].sum() > 0


def test_event_study_and_pretrend_table(tmp_path: Path):
    df = make_smoke_panel()
    result = run_event_study(df, min_lag=-3, max_lead=2)
    assert not result.empty
    assert (result["relative_year"] == -1).sum() == 0
    pre = pretrend_summary(result)
    assert (pre["relative_year"] < 0).all()
    out = plot_event_study(result, tmp_path / "event_study.png")
    assert out.exists()


def test_single_cohort_did_smoke():
    result = run_border_pair_did(make_smoke_panel())
    assert result.loc[0, "term"] == "treated:post"
    assert result.loc[0, "nobs"] > 0


def test_synthetic_control_smoke():
    df = make_smoke_panel()
    paths, weights = fit_simple_synth(df, treated_unit="34005")
    placebo = placebo_permutation_gaps(df)
    assert {"treated", "synthetic"}.issubset(paths.columns)
    assert abs(weights["weight"].sum() - 1) < 1e-9
    assert not placebo.empty


def test_policy_seed_validates():
    checks = validate_policy_table(policy_seed())
    assert checks["valid"].all()


def test_border_pair_builder_keeps_cross_state_pairs_only():
    adjacency = pd.DataFrame(
        [
            {"county_fips": "34005", "neighbor_fips": "42017", "county_name": "Burlington", "neighbor_name": "Bucks"},
            {"county_fips": "34005", "neighbor_fips": "34007", "county_name": "Burlington", "neighbor_name": "Camden"},
        ]
    )
    pairs = build_state_border_pairs(adjacency)
    assert len(pairs) == 1
    assert pairs.iloc[0]["state"] == "NJ"
    assert pairs.iloc[0]["neighbor_state"] == "PA"


def test_diagnostics_smoke():
    df = make_smoke_panel()
    assert not raw_trends(df).empty
    assert not balance_table(df).empty
    assert cluster_count(df).loc[0, "n_clusters"] == 2
    assert not joint_pretrend_test(df, min_lag=-3, max_lead=2).empty
    assert not placebo_policy_years(df, [2016]).empty


def test_phase2_economic_extensions_smoke():
    df = make_smoke_panel()
    enriched = add_economic_margins(df)
    assert {"minimum_wage_bite", "emp_per_establishment", "log_avg_annual_pay"}.issubset(enriched.columns)
    assert not estimate_margin_decomposition(df).empty
    assert not estimate_bite_dose_response(df).empty
    assert not estimate_heterogeneity(df).empty
    spillover = assess_border_spillover_identification(df)
    assert spillover.loc[0, "identified"] is False or spillover.loc[0, "identified"] == False
    assert not specification_curve(df).empty
