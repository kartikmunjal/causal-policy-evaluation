.PHONY: install smoke validation diagnostics research fred-policy national-findings regional-controls shift-share spatial-rdd report manifest test

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
US_IMPORTS ?= data/raw/us_china_imports_hs6.csv
INSTRUMENT_TRADE ?= data/raw/adh_country_china_imports_hs6.csv
HS_NAICS_CROSSWALK ?= data/raw/hs6_naics_crosswalk.csv
QCEW_INDUSTRY ?= data/processed/qcew_county_industry_panel.parquet
COUNTY_TO_CZ ?= data/raw/county_to_commuting_zone.csv
SPATIAL_RDD_PANEL ?= data/processed/spatial_border_distance_panel.parquet
REGIONAL_CONTROLS ?= ../regional-activity-nowcast/report/state_year_policy_controls.csv

install:
	$(PIP) install -r requirements.txt

smoke:
	PYTHONPATH=src $(PYTHON) scripts/run_all.py --python $(PYTHON) --smoke

validation:
	PYTHONPATH=src $(PYTHON) scripts/run_all.py --python $(PYTHON)

diagnostics:
	PYTHONPATH=src $(PYTHON) scripts/run_diagnostics.py

fred-policy:
	PYTHONPATH=src $(PYTHON) scripts/fetch_policy_fred.py

national-findings:
	PYTHONPATH=src $(PYTHON) scripts/run_national_findings.py

regional-controls:
	PYTHONPATH=src $(PYTHON) scripts/run_regional_control_specs.py --regional-controls $(REGIONAL_CONTROLS)

shift-share:
	PYTHONPATH=src $(PYTHON) scripts/run_shift_share.py --us-imports $(US_IMPORTS) --instrument-trade $(INSTRUMENT_TRADE) --crosswalk $(HS_NAICS_CROSSWALK) --qcew-industry $(QCEW_INDUSTRY) --county-to-cz $(COUNTY_TO_CZ)

spatial-rdd:
	PYTHONPATH=src $(PYTHON) scripts/run_spatial_rdd.py --panel $(SPATIAL_RDD_PANEL)

research:
	PYTHONPATH=src $(PYTHON) scripts/run_research_extensions.py

report:
	PYTHONPATH=src $(PYTHON) scripts/render_report.py

manifest:
	PYTHONPATH=src $(PYTHON) scripts/write_manifest.py

test:
	$(PYTHON) -m pytest -q
