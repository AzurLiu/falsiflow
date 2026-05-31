# Falsiflow PyPI Trusted Publishing

This runbook records the account-bound PyPI setup needed before Falsiflow can be
called externally ready.

## Current Blocker

The `Falsiflow Publish` workflow builds and checks the distributions, but PyPI
rejected the trusted-publishing token exchange with `invalid-publisher` because
no PyPI trusted publisher matches the GitHub OIDC claims.

Observed claim from the failed `v0.1.2` release run:

- `sub`: `repo:AzurLiu/falsiflow:environment:pypi`
- `repository`: `AzurLiu/falsiflow`
- `workflow_ref`: `AzurLiu/falsiflow/.github/workflows/falsiflow-publish.yml@refs/tags/v0.1.2`
- `ref`: `refs/tags/v0.1.2`
- `environment`: `pypi`

Evidence:

- Release: <https://github.com/AzurLiu/falsiflow/releases/tag/v0.1.2>
- Failed release-triggered publish run:
  <https://github.com/AzurLiu/falsiflow/actions/runs/26704442265>
- Successful build job in that run: distribution build, `twine check`, and
  `release-check`.
- Failed job: `publish-pypi`, step `Publish to PyPI`, with
  `invalid-publisher`.

## Required PyPI Project Setup

Because `https://pypi.org/pypi/falsiflow/json` currently returns 404, use the
PyPI account-level pending publisher path unless the project has appeared since
this runbook was last checked.

For a new PyPI project:

1. Sign in to PyPI as the account that will own `falsiflow`.
2. Open the account sidebar's **Publishing** page.
3. Add a new **pending publisher** for GitHub Actions.
4. Fill in the exact fields below.
5. Save the pending publisher, then rerun the failed `publish-pypi` job from
   the `v0.1.2` release workflow soon after saving it. A pending publisher does
   not reserve the project name; it is converted into a normal trusted publisher
   only when the first publish succeeds.

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

The `v0.1.2` GitHub release is already published and points at commit
`c7efa3301e32e04df86e1828bcbec7158e2b65ba`. After saving the publisher, rerun
the failed release workflow instead of creating a new release tag:

```bash
gh run rerun 26704442265 --repo AzurLiu/falsiflow --failed
gh run watch 26704442265 --repo AzurLiu/falsiflow --exit-status
```

If a new code change is needed before PyPI publication, publish a new version
instead of replacing the already-published `v0.1.2` artifacts.

## Verification

The release is not externally ready until all of these are true:

1. The PyPI pending publisher or existing-project publisher is saved with the
   exact fields above.
2. The release-triggered `Falsiflow Publish` workflow for `v0.1.2` has a successful
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
