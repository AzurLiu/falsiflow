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

Because `https://pypi.org/pypi/falsiflow/json` currently returns 404, use the
PyPI account-level pending publisher path unless the project has appeared since
this runbook was last checked.

For a new PyPI project:

1. Sign in to PyPI as the account that will own `falsiflow`.
2. Open the account sidebar's **Publishing** page.
3. Add a new **pending publisher** for GitHub Actions.
4. Fill in the exact fields below.
5. Save the pending publisher, then publish the `v0.1.2` GitHub release soon
   after saving it. A pending publisher does not reserve the project name; it is
   converted into a normal trusted publisher only when the first publish
   succeeds.

If the PyPI project already exists, open the project management page, choose
**Publishing**, and add the same GitHub trusted publisher there instead of using
the account-level pending publisher path.

Use these exact trusted-publisher settings:

- PyPI project name: `falsiflow`
- Owner: `AzurLiu`
- Repository name: `falsiflow`
- Workflow name: `falsiflow-publish.yml`
- Environment name: `pypi`

References:

- PyPI pending publisher setup:
  <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
- PyPI existing-project trusted publisher setup:
  <https://docs.pypi.org/trusted-publishers/adding-a-publisher/>
- PyPI trusted publishing workflow requirements:
  <https://docs.pypi.org/trusted-publishers/using-a-publisher/>

After saving the publisher, publish a new release tag whose package version
matches `pyproject.toml`.

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

1. The `v0.1.2` draft GitHub release is published after the pending publisher
   or existing-project publisher is saved.
2. The release-triggered `Falsiflow Publish` workflow has a successful
   `publish-pypi` job. A workflow_dispatch rehearsal is not enough because that
   path intentionally skips `publish-pypi`.
3. `https://pypi.org/pypi/falsiflow/json` returns JSON whose package name is
   `falsiflow` and whose version matches the release. For current main, that
   expected version is `0.1.2`.
4. The `Falsiflow External Evidence` workflow uploads
   `falsiflow_pypi_project.json`, `falsiflow_expected_version.txt`, and
   `falsiflow_pypi_version.txt`; pass `expected_version` when checking a
   release other than the version in `pyproject.toml`.
5. `falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict`
   reports `external_ready`.

Useful post-publish commands:

```bash
curl -fsS https://pypi.org/pypi/falsiflow/json | python -m json.tool | head -40
gh run list --workflow falsiflow-publish.yml --event release --limit 5
gh workflow run "Falsiflow External Evidence" \
  --field public_demo_url="$FALSIFLOW_PUBLIC_DEMO_URL" \
  --field pypi_package_url="https://pypi.org/project/falsiflow/" \
  --field expected_version="0.1.2"
```

If the release-triggered publish fails again with `invalid-publisher`, compare
the failed job's OIDC claims against the five fields above. The most likely
mismatches are the workflow filename, repository owner casing, or the GitHub
Actions environment name.
