# Static Hosting

The public demo is a static site in `docs/public_demo`. It does not need GitHub
Pages specifically.

Current public demo candidates:

- Netlify: <https://falsiflow-demo.netlify.app>
- GitHub Pages after the Pages workflow succeeds:
  <https://azurliu.github.io/falsiflow/>

Treat a hosted demo as launch-ready only after `Falsiflow External Evidence`
fetches it successfully and `external-check --strict` reports `external_ready`.

## Recommended Replacement

Use Netlify:

- Connect `https://github.com/AzurLiu/falsiflow`.
- Use the repository root.
- The included `netlify.toml` publishes `docs`.
- Leave the build command empty.
- The deployed site is `https://falsiflow-demo.netlify.app`.

## Other Static Hosts

Cloudflare Pages:

- Build command: empty
- Output directory: `docs`

Vercel:

- Framework preset: Other
- Build command: empty
- Output directory: `docs`

## GitHub Pages

GitHub Pages is optional but useful as a Netlify fallback. The
`Falsiflow Pages Demo` workflow builds the static demo package and deploys it
through GitHub Actions. Its `actions/configure-pages` step uses
`enablement: true` so a repository without an existing Pages site can be enabled
by the workflow before deployment.

If the Pages workflow succeeds, verify:

```bash
curl -fsS https://azurliu.github.io/falsiflow/ | grep -E "Falsiflow|Launchpad|Try"
```

If Netlify returns `usage_exceeded` or another hosted-demo error, use the GitHub
Pages URL as the candidate `FALSIFLOW_PUBLIC_DEMO_URL` for the external evidence
workflow.
