"""Report assembly helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def render_research_grade_writeup(report_dir: Path, output: Path | None = None) -> Path:
    output = output or report_dir / "WRITEUP.md"
    event = _read_csv(report_dir / "event_study_coefficients.csv")
    pretest = _read_csv(report_dir / "joint_pretrend_test.csv")
    did = _read_csv(report_dir / "border_pair_did.csv")
    pyfixest = _read_csv(report_dir / "pyfixest_lpdid.csv")
    iv = _read_csv(report_dir / "iv_2sls.csv")
    placebo = _read_csv(report_dir / "synthetic_placebos.csv")
    margins = _read_csv(report_dir / "phase2_margin_decomposition.csv")
    bite = _read_csv(report_dir / "phase2_bite_dose_response.csv")
    heterogeneity = _read_csv(report_dir / "phase2_heterogeneity.csv")
    spillovers = _read_csv(report_dir / "phase2_spillover_identification.csv")
    spec_curve = _read_csv(report_dir / "phase2_specification_curve.csv")

    lead_text = "not available"
    if not event.empty:
        leads = event[event["relative_year"] < 0]
        lead_text = leads[["relative_year", "estimate", "p_value"]].to_string(index=False)
    pretest_text = pretest.to_string(index=False) if not pretest.empty else "not available"
    did_text = did.to_string(index=False) if not did.empty else "not available"
    pyfixest_text = pyfixest.to_string(index=False) if not pyfixest.empty else "not available"
    iv_text = iv.to_string(index=False) if not iv.empty else "not available"
    placebo_text = placebo.head(12).to_string(index=False) if not placebo.empty else "not available"
    margins_text = margins.to_string(index=False) if not margins.empty else "not available"
    bite_text = bite.to_string(index=False) if not bite.empty else "not available"
    heterogeneity_text = heterogeneity.head(16).to_string(index=False) if not heterogeneity.empty else "not available"
    spillover_text = spillovers.to_string(index=False) if not spillovers.empty else "not available"
    spec_text = spec_curve.head(24).to_string(index=False) if not spec_curve.empty else "not available"

    text = f"""# Minimum-Wage Effects on Food-Service Employment

## Question

Estimate the causal effect of state minimum-wage increases on county-level food-service employment using public data and quasi-experimental designs.

## Primary Design

The pre-specified primary design is a border-county-pair event study with county, year, and border-pair fixed effects. The omitted event year is -1. The scaled design should use all audited state minimum-wage changes and all Census cross-state adjacent county pairs.

## Identification

The identifying assumption is parallel counterfactual employment trends between treated and comparison border counties. The design is threatened by cross-border spillovers, contemporaneous state policies, pandemic-era disruptions, composition changes, and too few clusters in validation-only runs.

## Parallel Trends Evidence

Event-study leads:

```text
{lead_text}
```

Joint pre-trend diagnostic:

```text
{pretest_text}
```

## Main Estimates

Single-cohort validation DiD:

```text
{did_text}
```

Modern staggered-DiD validation output:

```text
{pyfixest_text}
```

## Robustness

Synthetic-control placebo summary:

```text
{placebo_text}
```

## Phase 3: Economic Mechanisms and Heterogeneity

Phase 3 preserves the original causal design and asks whether adjustment appears through economically meaningful channels rather than only total employment.

Margin decomposition:

```text
{margins_text}
```

Minimum-wage bite dose response:

```text
{bite_text}
```

Heterogeneity by baseline establishment scale and pre-period growth:

```text
{heterogeneity_text}
```

Border-spillover identification status:

```text
{spillover_text}
```

Specification curve:

```text
{spec_text}
```

## Secondary IV

```text
{iv_text}
```

The IV result should be interpreted only with the first-stage diagnostics in `iv_first_stage.txt`. A weak first stage is a failed robustness check, not supportive evidence.

## Limitations

The NJ/PA validation design is not a publishable full-sample estimate. It is useful for validating data cleaning and estimators, but credible inference requires the national border-county-pair panel, audited policy timing, and enough state clusters for cluster-robust or wild-bootstrap inference.

## RDD

RDD remains omitted because no genuine sharp public-data eligibility threshold has been identified.
"""
    output.write_text(text, encoding="utf-8")
    return output
