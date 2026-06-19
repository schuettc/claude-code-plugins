# Releasing the ghost plugin

The plugin has two versioned artifacts that move together:

- the **`ghost-blog-mcp`** npm package (`ghost/mcp-server/`), which the bundled
  `.mcp.json` runs via `npx`, and
- the **plugin** itself (`ghost/.claude-plugin/plugin.json` + the `ghost` entry
  in `.claude-plugin/marketplace.json`).

Releases follow a **dev → prod** flow using npm **dist-tags**, mirroring the
repo's `feat → dev → main` promotion model: you publish to the `dev` tag,
test against it, then *promote the exact same artifact* to `latest`.

```
publish ──► ghost-blog-mcp@dev ──(test in ghost-site)──► promote ──► ghost-blog-mcp@latest
```

- **`@dev`** — what `ghost-site` (and any dev consumer) points at to test a build.
- **`@latest`** — what the shipped plugin's `.mcp.json` points at; what prod gets.

The bundled `ghost/.mcp.json` always references `@latest`. Dev testing opts into
`@dev` via a **project-level `.mcp.json` override** in the consuming repo, so the
shipped file never has to flip between branches. See `enable-in-a-project.md`.

---

## Dev release (publish to `@dev`)

```bash
cd ghost/mcp-server
npm version patch          # or minor / major — updates package.json + git tag
npm publish --tag dev      # prepublishOnly runs build + typecheck + test first
```

This publishes `ghost-blog-mcp@<version>` under the `dev` dist-tag only —
`@latest` is untouched, so nothing prod-facing changes.

Verify:

```bash
npm view ghost-blog-mcp dist-tags     # dev: <version>
```

(A brand-new version can take a couple of minutes to be readable; the publish
itself is confirmed by the `+ ghost-blog-mcp@<version>` line and by
`npm access list packages`.)

Test it: in `ghost-site`, the project `.mcp.json` points at `ghost-blog-mcp@dev`
(see `enable-in-a-project.md`), then run `/ghost:setup-ghost` and exercise the
flow against a real Ghost site.

## Promote to prod (move `@latest`)

Once the `@dev` build passes testing, promote the **exact same version** — no
rebuild, no republish:

```bash
npm dist-tag add ghost-blog-mcp@<version> latest
```

Now `@latest` and `@dev` point at the same version. Prod consumers (the shipped
plugin's `.mcp.json`) pick it up via `npx -y ghost-blog-mcp@latest`.

## Bump the plugin to match

Keep the plugin version in lockstep with the npm release, in **both** files:

- `ghost/.claude-plugin/plugin.json` → `"version": "X.X.X"`
- `.claude-plugin/marketplace.json` → `"version": "X.X.X"` in the `ghost` entry

Commit and push (feat → dev → main per the repo's promotion model):

```bash
git add ghost/.claude-plugin/plugin.json .claude-plugin/marketplace.json ghost/mcp-server/package.json
git commit -m "chore(ghost): release vX.X.X"
git push
```

---

## Future: automate with OIDC (no tokens)

Mirror `mixcraft-app`'s GitHub Actions **Trusted Publishing** (OIDC) so CI
publishes without an `NPM_TOKEN`:

- **`publish-dev`** — on push to `dev` touching `ghost/mcp-server/**`:
  build/typecheck/test, then `npm publish --tag dev --provenance`.
- **`publish-prod`** — on a GitHub Release: `npm dist-tag add ghost-blog-mcp@<v> latest`.

Both need `permissions: { id-token: write, contents: read }` and a trusted
publisher configured for `ghost-blog-mcp` on npmjs.com (repo
`schuettc/claude-code-plugins` + the workflow filename). `--provenance` only
works from CI, not a local `npm publish`.

The repo's `/release` skill is currently scoped to `feature-workflow`; until it's
generalised to take a plugin parameter + npm-publish step, use the manual flow
above.
