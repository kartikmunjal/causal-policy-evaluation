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
from causal_policy_evaluation.minimum_wage import detect_minimum_wage_changes, fred_series_id
from causal_policy_evaluation.plots import plot_event_study
from causal_policy_evaluation.policy import policy_seed, validate_policy_table
from causal_policy_evaluation.rdd import density_balance_diagnostics, run_local_linear_rdd
from causal_policy_evaluation.shift_share import (
    aggregate_trade_to_naics,
    build_cz_industry_shares,
    build_trade_exposure,
    cz_outcome_changes,
    industry_trade_shocks,
    rotemberg_weights,
    run_shift_share_iv,
)
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


def test_fred_minimum_wage_change_detection():
    series = pd.DataFrame(
        {
            "state": ["NJ", "NJ", "NJ", "PA"],
            "date": pd.to_datetime(["2018-01-01", "2019-01-01", "2020-01-01", "2019-01-01"]),
            "minimum_wage": [8.85, 10.0, 11.0, 7.25],
            "series_id": ["STTMINWGNJ", "STTMINWGNJ", "STTMINWGNJ", "STTMINWGPA"],
            "source_url": ["https://fred.stlouisfed.org/graph/fredgraph.csv?id=STTMINWGNJ"] * 4,
        }
    )
    changes = detect_minimum_wage_changes(series, start_year=2019, end_year=2020)
    assert fred_series_id("NJ") == "STTMINWGNJ"
    assert len(changes) == 2
    assert set(changes["policy_year"]) == {2019, 2020}


def test_shift_share_trade_iv_components_smoke():
    crosswalk = pd.DataFrame(
        {
            "hs6": ["000001", "000002"],
            "naics": ["311", "722"],
            "share": [1.0, 1.0],
        }
    )
    us_trade = pd.DataFrame(
        {
            "year": [1991, 1991, 2007, 2007],
            "hs6": ["1", "2", "1", "2"],
            "trade_value": [100.0, 50.0, 180.0, 90.0],
        }
    )
    inst_trade = pd.DataFrame(
        {
            "year": [1991, 1991, 2007, 2007],
            "hs6": ["1", "2", "1", "2"],
            "trade_value": [80.0, 60.0, 160.0, 120.0],
        }
    )
    qcew_rows = []
    county_rows = []
    for cz in range(1, 7):
        county = f"0100{cz}"
        county_rows.append({"county_fips": county, "cz": cz})
        for year in [1991, 2007]:
            for naics, base in [("311", 100 + 10 * cz), ("722", 60 + 4 * cz)]:
                qcew_rows.append(
                    {
                        "county_fips": county,
                        "cz": cz,
                        "year": year,
                        "naics": naics,
                        "employment": base + (year == 2007) * (5 * cz),
                        "wages": 1000 * base + (year == 2007) * (50 * cz),
                    }
                )
    qcew = pd.DataFrame(qcew_rows)
    county_to_cz = pd.DataFrame(county_rows)
    us_naics, dropped = aggregate_trade_to_naics(us_trade, crosswalk)
    inst_naics, _ = aggregate_trade_to_naics(inst_trade, crosswalk)
    china_shocks = industry_trade_shocks(us_naics, 1991, 2007, prefix="china_import")
    inst_shocks = industry_trade_shocks(inst_naics, 1991, 2007, prefix="adh_import")
    shares = build_cz_industry_shares(qcew, county_to_cz, 1991)
    exposure = build_trade_exposure(shares, china_shocks, inst_shocks)
    outcomes = cz_outcome_changes(qcew, county_to_cz, 1991, 2007)
    analysis = outcomes.merge(exposure, on="cz")
    iv_table, first_stage = run_shift_share_iv(analysis)
    weights = rotemberg_weights(shares, inst_shocks)
    assert dropped.empty
    assert len(exposure) == 6
    assert not iv_table.empty
    assert "Partial F-statistic" in first_stage
    assert abs(weights["rotemberg_weight_abs"].sum() - 1.0) < 1e-9


def test_spatial_rdd_requires_real_signed_distance_and_estimates():
    df = pd.DataFrame(
        {
            "signed_distance_km": [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6],
            "log_employment": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.9, 11.0, 11.1, 11.2, 11.3, 11.4],
            "state": ["A"] * 6 + ["B"] * 6,
        }
    )
    estimate = run_local_linear_rdd(df, outcome="log_employment", bandwidth=6.1)
    diagnostics = density_balance_diagnostics(df, bandwidth=6.1)
    assert estimate.nobs == 12
    assert estimate.estimate > 0
    assert diagnostics.loc[0, "left_n"] == 6
