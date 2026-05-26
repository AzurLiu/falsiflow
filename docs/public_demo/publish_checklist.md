# Falsiflow Demo Publish Checklist

- Package status: `demo_package_ready`
- Publishable static files: `true`
- External URL required: `true`

## Before Sharing Publicly

- Publish the directory with GitHub Pages, Netlify, or another static host.
- Record the repository URL in `FALSIFLOW_REPO_URL`.
- Record the hosted demo URL in `FALSIFLOW_PUBLIC_DEMO_URL`.
- Re-run `falsiflow external-check --out-dir falsiflow_external_check --force --strict`.
