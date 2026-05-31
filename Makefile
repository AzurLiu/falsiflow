.PHONY: install-local pipx-install pipx-start start start-check onboard-check static-demo demo-package publish-kit launch-kit external-evidence external-check release-proof cli-reference casebook-check test release-check clean

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

launch-kit: install-local
	falsiflow launch-kit --out-dir falsiflow_launch_kit --force

external-evidence: install-local
	falsiflow external-evidence --out falsiflow_external_evidence.json --force

external-check: install-local
	falsiflow external-check --out-dir falsiflow_external_check --force

release-proof: install-local
	falsiflow release-proof --evidence falsiflow_external_evidence.json --readiness falsiflow_external_check/external_readiness.json --out release_proof.md

cli-reference: install-local
	falsiflow cli-reference --out docs/falsiflow_cli_reference.md

casebook-check: install-local
	falsiflow casebook-check --out-dir data/falsiflow/casebook_check --force

test:
	$(PYTHON) -m py_compile falsiflow/core.py falsiflow/cli.py falsiflow/adapters.py falsiflow/api.py falsiflow/mcp_server.py falsiflow/release.py falsiflow/adoption.py falsiflow/casebook_check.py falsiflow/bundle.py falsiflow/browser_demo.py falsiflow/demo.py falsiflow/discovery.py falsiflow/local_server.py falsiflow/public_release.py falsiflow/claim_check.py falsiflow/doctor.py falsiflow/quickstart.py falsiflow/scaffold.py falsiflow/template_discovery.py falsiflow/template_gallery.py falsiflow/template_check.py falsiflow/template_pack.py falsiflow/template_registry.py falsiflow/template_provenance.py falsiflow/template_release.py falsiflow/template_install.py scripts/falsiflow.py scripts/falsiflow_tests/regress_falsiflow_core.py
	$(PYTHON) scripts/falsiflow_tests/regress_falsiflow_core.py

release-check:
	$(PYTHON) scripts/falsiflow.py release-check --out-dir data/falsiflow/release_check --force

clean:
	rm -rf build dist falsiflow.egg-info __pycache__
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
