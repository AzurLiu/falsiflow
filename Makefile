.PHONY: install-local pipx-install pipx-start start start-check onboard-check static-demo demo-package publish-kit external-check test release-check clean

PYTHON ?= python3
FALSIFLOW_OUT ?= falsiflow_start

install-local:
	$(PYTHON) -m pip install -e .

pipx-install:
	pipx install --force .

pipx-start:
	falsiflow start --out-dir $(FALSIFLOW_OUT)

start: install-local
	falsiflow start --out-dir $(FALSIFLOW_OUT)

start-check: install-local
	falsiflow start --out-dir $(FALSIFLOW_OUT) --check --json

onboard-check: install-local
	falsiflow onboard --check --json

static-demo: install-local
	falsiflow static-demo --out-dir falsiflow_static_demo --force

demo-package: install-local
	falsiflow demo-package --out-dir falsiflow_public_demo --force

publish-kit: install-local
	falsiflow publish-kit --out-dir falsiflow_publish_kit --force

external-check: install-local
	falsiflow external-check --out-dir falsiflow_external_check --force

test:
	$(PYTHON) -m py_compile falsiflow/core.py falsiflow/cli.py falsiflow/adapters.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
	$(PYTHON) scripts/falsiflow_tests/regress_falsiflow_core.py

release-check:
	$(PYTHON) scripts/falsiflow.py release-check --out-dir data/falsiflow/release_check --force

clean:
	rm -rf build dist falsiflow.egg-info __pycache__
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
