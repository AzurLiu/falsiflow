.PHONY: test build clean

PYTHON ?= python3

test:
	$(PYTHON) -m py_compile falsiflow/core.py falsiflow/bundle.py falsiflow/claim_check.py falsiflow/cli.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
	$(PYTHON) scripts/falsiflow_tests/regress_falsiflow_core.py

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist falsiflow.egg-info __pycache__
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
