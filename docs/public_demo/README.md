# Falsiflow Public Demo Package

This directory is a static, zero-install Falsiflow demo package.

## Preview

- Open `index.html` locally, or publish this directory with GitHub Pages, Netlify, or any static file server.
- The launchpad starts with the live downstream PR story set: AI eval, RAG eval, and product-metric PRs block placeholder evidence in CI, then pass after source-backed evidence is added.
- PR #1 in the downstream AI eval demo remains the smallest single-PR version of that story.
- Workbench shell: `docs/public_demo/workbench.html`
- Try report: `docs/public_demo/try_report.html`
- Wizard: `docs/public_demo/falsiflow_wizard.html`

## Publish Checklist

- Keep `.nojekyll` so GitHub Pages serves files exactly as written.
- Netlify can deploy the directory directly; `netlify.toml` sets the publish root to this folder.
- Set `FALSIFLOW_REPO_URL` and `FALSIFLOW_PUBLIC_DEMO_URL`, then run `falsiflow external-check --out-dir falsiflow_external_check --force --strict` before calling a release externally ready.

## Boundary

The demo shows evidence gates and audit outputs. It does not upload data, run cloud AI, or make unverified research claims ready.
