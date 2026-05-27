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

## Verification

The release is not externally ready until all of these are true:

1. The `Falsiflow Publish` workflow has a successful `publish-pypi` job.
2. `https://pypi.org/pypi/falsiflow/json` returns JSON whose package name is
   `falsiflow` and whose version matches the release.
3. The `Falsiflow External Evidence` workflow uploads
   `falsiflow_pypi_project.json`.
4. `falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict`
   reports `external_ready`.
