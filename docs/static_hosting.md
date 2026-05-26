# Static Hosting

The public demo is a static site in `docs/public_demo`. It does not need GitHub
Pages specifically.

Current public demo: <https://falsiflow-demo.netlify.app>

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

GitHub Pages is optional. If it fails before project code runs while downloading
GitHub's own Pages actions, keep it disabled or manual and use another static
host until the account or Pages service issue is resolved.
