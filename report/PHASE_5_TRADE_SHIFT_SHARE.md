# Phase 5: Trade-Shock Shift-Share IV

This phase adds a research extension that is connected to the minimum-wage project but has its own economic question: whether exposure to import competition changes local labor-market outcomes in ways that matter for interpreting policy effects.

## Economic Idea

The minimum-wage design estimates policy effects in border labor markets. A natural next question is whether those effects differ in places already under demand pressure from trade exposure. The China-shock design constructs commuting-zone exposure from baseline industry employment shares and national industry import growth.

The instrument follows the Autor-Dorn-Hanson logic: use import growth from China to other high-income countries to isolate industry-level supply shocks from China rather than demand shocks specific to the United States.

## Estimating Equation

The prepared analysis panel estimates:

`Delta log(Y_cz) = alpha + beta ImportExposure_cz + u_cz`

with first stage:

`ImportExposure_cz = pi0 + pi1 InstrumentExposure_cz + v_cz`

where exposure is the baseline CZ industry-share weighted change in imports by NAICS industry. The command reports the 2SLS coefficient and the first-stage diagnostics from `linearmodels`.

## Required Public Inputs

The CLI is source-agnostic and expects prepared public files:

- US imports from China by HS6 and year.
- Imports from China by the Autor-Dorn-Hanson instrument countries by HS6 and year.
- HS6-to-NAICS concordance, such as Pierce-Schott style mappings.
- QCEW county-industry employment panel.
- County-to-commuting-zone crosswalk, such as the Dorn CZ crosswalk.

The script writes dropped HS6 codes so concordance loss is visible rather than hidden.

## Research-Grade Diagnostics

The phase adds:

- First-stage strength reporting.
- HS6 concordance dropped-code audit.
- Rotemberg-style industry influence weights to show which industries identify the shift-share design.
- Optional validation against a reference ADH exposure file when available.

## Interpretation

This does not replace the primary minimum-wage DiD estimand. It is a connected labor-demand design that can help explain heterogeneity in policy effects and demonstrate credible data-science construction of an economically meaningful instrument.
