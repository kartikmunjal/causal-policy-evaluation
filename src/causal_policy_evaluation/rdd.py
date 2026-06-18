"""Spatial regression-discontinuity helpers for border designs.

The module is deliberately conservative. It does not create a running variable
from treatment status. A caller must supply a signed distance to the relevant
state border, with negative values on the low-minimum-wage side and positive
values on the high-minimum-wage side.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class RDDResult:
    outcome: str
    running_variable: str
    bandwidth: float
    estimate: float
    std_error: float
    p_value: float
    nobs: int
    left_n: int
    right_n: int
    method: str

    def as_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.__dict__])


def require_signed_running_variable(data: pd.DataFrame, running_col: str = "signed_distance_km") -> pd.DataFrame:
    """Validate the spatial RDD running variable and return a clean copy."""
    if running_col not in data.columns:
        raise ValueError(
            f"Spatial RDD requires `{running_col}`. Supply signed distance to the policy border; "
            "negative values should be the lower-minimum-wage side and positive values the higher-wage side."
        )
    out = data.copy()
    out[running_col] = pd.to_numeric(out[running_col], errors="coerce")
    out = out.dropna(subset=[running_col])
    if not ((out[running_col] < 0).any() and (out[running_col] >= 0).any()):
        raise ValueError("Spatial RDD requires observations on both sides of the border cutoff.")
    return out


def select_bandwidth(data: pd.DataFrame, running_col: str = "signed_distance_km", quantile: float = 0.5) -> float:
    """Pick a transparent default bandwidth when no publication bandwidth is supplied."""
    distances = pd.to_numeric(data[running_col], errors="coerce").abs()
    distances = distances[(distances > 0) & np.isfinite(distances)]
    if distances.empty:
        raise ValueError("Cannot select bandwidth from empty or zero running-variable distances.")
    bandwidth = float(distances.quantile(quantile))
    if bandwidth <= 0:
        bandwidth = float(distances.max())
    return bandwidth


def triangular_kernel_weights(running: pd.Series, bandwidth: float) -> pd.Series:
    scaled = running.abs() / bandwidth
    return (1.0 - scaled).clip(lower=0.0)


def run_local_linear_rdd(
    data: pd.DataFrame,
    outcome: str,
    running_col: str = "signed_distance_km",
    bandwidth: float | None = None,
    cluster_col: str | None = None,
) -> RDDResult:
    """Estimate a local-linear spatial RDD with side-specific slopes."""
    clean = require_signed_running_variable(data, running_col)
    if outcome not in clean.columns:
        raise ValueError(f"Outcome `{outcome}` is missing.")
    clean[outcome] = pd.to_numeric(clean[outcome], errors="coerce")
    clean = clean.dropna(subset=[outcome])
    if bandwidth is None:
        bandwidth = select_bandwidth(clean, running_col)
    work = clean[clean[running_col].abs() <= bandwidth].copy()
    work["right_side"] = (work[running_col] >= 0).astype(float)
    work["running_right"] = work[running_col] * work["right_side"]
    work["kernel_weight"] = triangular_kernel_weights(work[running_col], bandwidth)
    work = work[work["kernel_weight"] > 0].copy()
    left_n = int((work[running_col] < 0).sum())
    right_n = int((work[running_col] >= 0).sum())
    if left_n < 3 or right_n < 3:
        raise ValueError("Local-linear RDD requires at least three observations on each side inside the bandwidth.")
    x = sm.add_constant(work[["right_side", running_col, "running_right"]], has_constant="add")
    model = sm.WLS(work[outcome], x, weights=work["kernel_weight"])
    if cluster_col and cluster_col in work.columns and work[cluster_col].nunique() > 1:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": work[cluster_col]})
        method = "local_linear_triangular_clustered"
    else:
        fit = model.fit(cov_type="HC1")
        method = "local_linear_triangular_hc1"
    return RDDResult(
        outcome=outcome,
        running_variable=running_col,
        bandwidth=float(bandwidth),
        estimate=float(fit.params["right_side"]),
        std_error=float(fit.bse["right_side"]),
        p_value=float(fit.pvalues["right_side"]),
        nobs=int(fit.nobs),
        left_n=left_n,
        right_n=right_n,
        method=method,
    )


def density_balance_diagnostics(
    data: pd.DataFrame,
    running_col: str = "signed_distance_km",
    bandwidth: float | None = None,
) -> pd.DataFrame:
    """Return manipulation-risk diagnostics around the border cutoff.

    If the optional `rddensity` package is available, callers can add it later.
    The built-in diagnostic is a transparent count imbalance and should be read
    as a screen, not a formal McCrary density test.
    """
    clean = require_signed_running_variable(data, running_col)
    if bandwidth is None:
        bandwidth = select_bandwidth(clean, running_col)
    work = clean[clean[running_col].abs() <= bandwidth]
    left_n = int((work[running_col] < 0).sum())
    right_n = int((work[running_col] >= 0).sum())
    total = left_n + right_n
    imbalance = (right_n - left_n) / total if total else np.nan
    has_rddensity = importlib.util.find_spec("rddensity") is not None
    return pd.DataFrame(
        [
            {
                "running_variable": running_col,
                "bandwidth": float(bandwidth),
                "left_n": left_n,
                "right_n": right_n,
                "count_imbalance": imbalance,
                "formal_density_test_available": bool(has_rddensity),
                "interpretation": "screen_only_not_formal_density_test",
            }
        ]
    )


def spatial_rdd_identification_notes() -> pd.DataFrame:
    """Document why the spatial RDD is a complement, not the main design."""
    return pd.DataFrame(
        [
            {
                "assumption": "Continuity at state border",
                "threat": "State borders bundle taxes, labor laws, demographics, and pandemic policies.",
                "design_response": "Use narrow bandwidths, border-segment controls where available, and report as robustness.",
            },
            {
                "assumption": "No sorting exactly around cutoff",
                "threat": "Firms and workers may locate based on state policy bundles.",
                "design_response": "Report density/count diagnostics and pre-policy covariate balance.",
            },
            {
                "assumption": "Sharp treatment discontinuity",
                "threat": "Local minimum wages, exemptions, and enforcement can weaken the jump.",
                "design_response": "Use verified policy rates and skip RDD if the treatment jump is not sharp.",
            },
        ]
    )
