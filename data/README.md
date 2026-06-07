# Data Directory

`data/raw/` stores cached public source files and provenance metadata. Large BLS QCEW zip files and processed parquet panels are ignored by git. Small audit files such as `minimum_wage_policy_dates.csv` and `provenance.json` are committed.

`data/processed/` stores derived analysis panels. These are reproducible from the scripts and are ignored by git except for `.gitkeep`.

National-scale runs require:

- Census county adjacency from `scripts/build_border_pairs.py`
- audited minimum-wage policy rows in `data/raw/minimum_wage_policy_dates.csv`
- BLS QCEW annual county files downloaded by `scripts/build_national_panel.py` or `scripts/fetch_data.py`

The national builder validates policy rows and fails if required provenance or verification flags are missing.
