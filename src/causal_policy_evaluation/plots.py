"""Plotting utilities for reports."""

from __future__ import annotations

from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/causal_policy_evaluation_mpl")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_event_study(results: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(-0.5, color="gray", linestyle="--", linewidth=1)
    ax.errorbar(
        results["relative_year"],
        results["estimate"],
        yerr=1.96 * results["std_error"],
        fmt="o-",
        color="#1f77b4",
        ecolor="#555555",
        capsize=3,
    )
    ax.set_xlabel("Years relative to minimum-wage increase")
    ax.set_ylabel("Effect on log food-service employment")
    ax.set_title("Border-County-Pair Event Study")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_treated_vs_synthetic(paths: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(paths["year"], paths["treated"], label="Treated", linewidth=2)
    ax.plot(paths["year"], paths["synthetic"], label="Synthetic control", linewidth=2)
    ax.axvline(paths.attrs.get("treatment_year", 2019), color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Year")
    ax.set_ylabel(paths.attrs.get("outcome_label", "Outcome"))
    ax.legend(frameon=False)
    ax.set_title("Treated vs Synthetic Path")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_specification_curve(results: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    work = results.sort_values(["outcome", "window", "weighted"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = {
        "log_employment": "#1f77b4",
        "log_establishments": "#2ca02c",
        "log_emp_per_establishment": "#d62728",
        "log_avg_annual_pay": "#9467bd",
    }
    for outcome, group in work.groupby("outcome"):
        ax.scatter(group.index, group["estimate"], label=outcome.replace("log_", ""), color=colors.get(outcome, "#555555"), s=30)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Specification")
    ax.set_ylabel("Treated x post estimate")
    ax.set_title("Phase 2 Specification Curve")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path
