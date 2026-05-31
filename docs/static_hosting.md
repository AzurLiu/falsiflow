# Static Hosting

The public demo is a static site in `docs/public_demo`. It does not need GitHub
Pages specifically.

Current public demo:

- GitHub Pages: <https://azurliu.github.io/falsiflow/>

Treat a hosted demo as launch-ready only after `Falsiflow External Evidence`
fetches it successfully and `external-check --strict` reports `external_ready`.

## Recommended Hosted URL

Use GitHub Pages through the included `Falsiflow Pages Demo` workflow. The
workflow builds a fresh static demo package and deploys it to
`https://azurliu.github.io/falsiflow/`.

Verify it after each deployment:

```bash
curl -fsS https://azurliu.github.io/falsiflow/ | grep -E "Falsiflow|Launchpad|Try"
```

## Netlify

Use Netlify:

- Connect `https://github.com/AzurLiu/falsiflow`.
- Use the repository root.
- The included `netlify.toml` publishes `docs`.
- Leave the build command empty.
- The deployed site is `https://falsiflow-demo.netlify.app`.
- If Netlify returns `usage_exceeded` or another hosted-demo error, keep using
  the GitHub Pages URL as `FALSIFLOW_PUBLIC_DEMO_URL`.

## Other Static Hosts

Cloudflare Pages:

- Build command: empty
- Output directory: `docs`

Vercel:

- Framework preset: Other
- Build command: empty
- Output directory: `docs`

## GitHub Pages

The `Falsiflow Pages Demo` workflow builds the static demo package and deploys
it through GitHub Actions. Its `actions/configure-pages` step uses
`enablement: true` so a repository without an existing Pages site can be enabled
by the workflow before deployment when repository permissions allow it.

If the Pages workflow succeeds, verify:

```bash
curl -fsS https://azurliu.github.io/falsiflow/ | grep -E "Falsiflow|Launchpad|Try"
```

If the workflow fails with `Resource not accessible by integration`, enable
GitHub Pages for GitHub Actions in repository settings or with:

```bash
gh api --method POST repos/AzurLiu/falsiflow/pages -f build_type=workflow
```
