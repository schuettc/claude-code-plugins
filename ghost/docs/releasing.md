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

## Automation

**Dev publish is automated** via `.github/workflows/publish-ghost-mcp-dev.yml`
(OIDC Trusted Publishing — no `NPM_TOKEN`). On every push to `dev` that touches
`ghost/mcp-server/**`, it builds/typechecks/tests and, **if the version in
`package.json` is new**, runs `npm publish --tag dev --provenance`. So the dev
release becomes: bump the version on a `feat/*` branch, merge to `dev`, and CI
publishes `@dev`. (The manual `npm publish --tag dev` above is the local
fallback; `--provenance` only works from CI.)

**One-time setup (npmjs.com):** configure a *trusted publisher* for the
`ghost-blog-mcp` package → repository `schuettc/claude-code-plugins`, workflow
`.github/workflows/publish-ghost-mcp-dev.yml`. Until that's done the publish
step fails with an auth error. (npm CLI ≥ 11.5 is required for tokenless OIDC;
the workflow upgrades npm before publishing.)

**Prod promotion stays manual — on purpose.** Moving `@latest` is the "ship to
prod" gate and should be a deliberate human action, so it is *not* automated:
run `npm dist-tag add ghost-blog-mcp@<version> latest` yourself (see "Promote to
prod" above). It also sidesteps a limitation: OIDC trusted publishing authorises
`npm publish`, not `dist-tag` operations, so automating promotion would require a
classic token — which we avoid.

The repo's `/release` skill is currently scoped to `feature-workflow`; until it's
generalised to take a plugin parameter + npm-publish step, use this document.
