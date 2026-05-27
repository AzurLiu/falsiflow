# Falsiflow PyPI Trusted Publishing

This runbook records the account-bound PyPI setup needed before Falsiflow can be
called externally ready.

## Current Blocker

The `Falsiflow Publish` workflow builds and checks the distributions, but PyPI
rejected the trusted-publishing token exchange with `invalid-publisher` because
no PyPI trusted publisher matches the GitHub OIDC claims.

Observed claim from the failed `v0.1.1` release run:

- `sub`: `repo:AzurLiu/falsiflow:environment:pypi`
- `repository`: `AzurLiu/falsiflow`
- `workflow_ref`: `AzurLiu/falsiflow/.github/workflows/falsiflow-publish.yml@refs/tags/v0.1.1`
- `ref`: `refs/tags/v0.1.1`
- `environment`: `pypi`

## Required PyPI Project Setup

In the PyPI project or pending publisher setup for `falsiflow`, configure a
GitHub trusted publisher with:

- Owner: `AzurLiu`
- Repository name: `falsiflow`
- Workflow name: `falsiflow-publish.yml`
- Environment name: `pypi`

After saving the publisher, rerun the failed `Falsiflow Publish` workflow or
publish a new release tag whose package version matches `pyproject.toml`.

Current main is prepared for `0.1.2`. Prefer publishing a new `v0.1.2` GitHub
release after the trusted publisher is configured, rather than rerunning the old
`v0.1.1` release, so the PyPI package includes the product-metric template,
README 30-second demo, demo PR playbook, named neighboring-tool boundaries, and
sharpened launch kit.

Do not publish the `v0.1.2` release tag until the PyPI project or pending
publisher has the exact trusted-publisher settings above; otherwise the release
workflow will build successfully and fail again at the PyPI token exchange.

## Verification

The release is not externally ready until all of these are true:

1. The `Falsiflow Publish` workflow has a successful `publish-pypi` job.
2. `https://pypi.org/pypi/falsiflow/json` returns JSON whose package name is
   `falsiflow` and whose version matches the release. For current main, that
   expected version is `0.1.2`.
3. The `Falsiflow External Evidence` workflow uploads
   `falsiflow_pypi_project.json`, `falsiflow_expected_version.txt`, and
   `falsiflow_pypi_version.txt`; pass `expected_version` when checking a
   release other than the version in `pyproject.toml`.
4. `falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict`
   reports `external_ready`.
