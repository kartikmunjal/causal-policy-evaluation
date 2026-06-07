.PHONY: install smoke validation diagnostics research report manifest test

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

install:
	$(PIP) install -r requirements.txt

smoke:
	PYTHONPATH=src $(PYTHON) scripts/run_all.py --python $(PYTHON) --smoke

validation:
	PYTHONPATH=src $(PYTHON) scripts/run_all.py --python $(PYTHON)

diagnostics:
	PYTHONPATH=src $(PYTHON) scripts/run_diagnostics.py

research:
	PYTHONPATH=src $(PYTHON) scripts/run_research_extensions.py

report:
	PYTHONPATH=src $(PYTHON) scripts/render_report.py

manifest:
	PYTHONPATH=src $(PYTHON) scripts/write_manifest.py

test:
	$(PYTHON) -m pytest -q
