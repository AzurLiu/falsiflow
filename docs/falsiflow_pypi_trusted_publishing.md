# Falsiflow PyPI Trusted Publishing

This runbook records the account-bound PyPI setup, current publish evidence,
and the original successful v0.1.2 trusted-publishing recovery for Falsiflow.

## Current Status

Current release evidence:

- PyPI project: <https://pypi.org/project/falsiflow/>
- PyPI JSON API: <https://pypi.org/pypi/falsiflow/json>
- Latest release: <https://github.com/AzurLiu/falsiflow/releases/latest>
- Release publish workflow:
  <https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-publish.yml>
- `Falsiflow External Evidence` workflow:
  <https://github.com/AzurLiu/falsiflow/actions/workflows/falsiflow-external-evidence.yml>
- Required status after each release: PyPI JSON reports the release version and
  `external-check --strict` reports `external_ready`.

The original v0.1.2 failure was resolved by adding a PyPI account-level
pending publisher for project `falsiflow`. On first successful publish, PyPI
converted that pending publisher into the project's trusted publisher.

## v0.1.16 README Rendering Check

The v0.1.16 launch-hardening release moved README image embeds to absolute
HTTPS URLs so PyPI long descriptions and other external renderers can show the
downstream PR proof strip without relying on repository-relative Markdown image targets.

Public evidence:

- PyPI project page: <https://pypi.org/project/falsiflow/>
- PyPI JSON API: <https://pypi.org/pypi/falsiflow/json>
- Expected proof image URL:
  <https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png>
- Expected downstream PR link:
  <https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1>
- Release workflow:
  <https://github.com/AzurLiu/falsiflow/actions/runs/26716164341>
- External evidence workflow:
  <https://github.com/AzurLiu/falsiflow/actions/runs/26716210700>

Use this public check when reviewing a PyPI rendering regression:

```bash
python3 - <<'PY'
import json, re, urllib.request

url = "https://pypi.org/pypi/falsiflow/json"
data = json.load(urllib.request.urlopen(url, timeout=30))
desc = data["info"].get("description") or ""

assert data["info"]["version"] >= "0.1.16"
assert "https://raw.githubusercontent.com/AzurLiu/falsiflow/main/docs/assets/falsiflow_downstream_pr_proof_strip.png" in desc
assert "https://github.com/AzurLiu/falsiflow-downstream-ai-eval-demo/pull/1" in desc
assert not re.search(r"!\[[^\]]*\]\(docs/assets/", desc)
print("pypi_description_rendering_inputs_ready")
PY
```

## Historical Blocker

Before the publisher was registered, the `Falsiflow Publish` workflow built and
checked the distributions, but PyPI rejected the trusted-publishing token
exchange with `invalid-publisher` because no PyPI trusted publisher matched the
GitHub OIDC claims.

Observed claim from the failed `v0.1.2` release run:

- `sub`: `repo:AzurLiu/falsiflow:environment:pypi`
- `repository`: `AzurLiu/falsiflow`
- `workflow_ref`: `AzurLiu/falsiflow/.github/workflows/falsiflow-publish.yml@refs/tags/v0.1.2`
- `ref`: `refs/tags/v0.1.2`
- `environment`: `pypi`

Failure evidence:

- Release: <https://github.com/AzurLiu/falsiflow/releases/tag/v0.1.2>
- Original failed release-triggered publish run:
  <https://github.com/AzurLiu/falsiflow/actions/runs/26704442265>
- Successful build job in that run: distribution build, `twine check`, and
  `release-check`.
- Failed job: `publish-pypi`, step `Publish to PyPI`, with
  `invalid-publisher`.
- The same run later succeeded after rerunning the failed job with the PyPI
  pending publisher configured.

## Required PyPI Project Setup For Future Releases

For new projects, use the PyPI account-level pending publisher path until the
project exists. For the existing `falsiflow` project, open the project
management page, choose **Publishing**, and verify or repair the existing
trusted publisher instead.

For a new PyPI project:

1. Sign in to PyPI as the account that will own `falsiflow`.
2. Open the account sidebar's **Publishing** page.
3. Add a new **pending publisher** for GitHub Actions.
4. Fill in the exact fields below.
5. Save the pending publisher, then publish or rerun the release workflow soon
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

The original `v0.1.2` GitHub release is already published and points at commit
`c7efa3301e32e04df86e1828bcbec7158e2b65ba`. The recovery used this rerun path:

```bash
gh run rerun 26704442265 --repo AzurLiu/falsiflow --failed
gh run watch 26704442265 --repo AzurLiu/falsiflow --exit-status
```

If a new code change is needed after PyPI publication, publish a new version
instead of replacing the already-published `v0.1.2` artifacts.

## Verification

The original v0.1.2 verification is complete. For current and future releases,
do not call the release externally ready until all of these are true:

1. The PyPI pending publisher or existing-project publisher exists with the
   exact fields above.
2. The release-triggered `Falsiflow Publish` workflow for the release tag has a successful
   `publish-pypi` job. A workflow_dispatch rehearsal is not enough because that
   path intentionally skips `publish-pypi`.
3. `https://pypi.org/pypi/falsiflow/json` returns JSON whose package name is
   `falsiflow` and whose version matches the release.
4. The `Falsiflow External Evidence` workflow uploads
   `falsiflow_pypi_project.json`, `falsiflow_expected_version.txt`, and
   `falsiflow_pypi_version.txt`; pass `expected_version` when checking a
   release other than the version in `pyproject.toml`.
5. `falsiflow external-check --out-dir falsiflow_external_check --evidence falsiflow_external_evidence.json --force --strict`
   reports `external_ready`.

Useful post-publish commands:

```bash
expected_version="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")"
curl -fsS https://pypi.org/pypi/falsiflow/json | python -m json.tool | head -40
gh run list --workflow falsiflow-publish.yml --event release --limit 5
gh workflow run "Falsiflow External Evidence" \
  --field public_demo_url="$FALSIFLOW_PUBLIC_DEMO_URL" \
  --field pypi_package_url="https://pypi.org/project/falsiflow/" \
  --field expected_version="$expected_version"
```

If a release-triggered publish fails again with `invalid-publisher`, compare the
failed job's OIDC claims against the five fields above. The most likely
mismatches are the workflow filename, repository owner casing, or the GitHub
Actions environment name.
