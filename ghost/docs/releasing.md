# Releasing the ghost plugin

The plugin has two versioned artifacts that move together:

- the **`ghost-blog-mcp`** npm package (`ghost/mcp-server/`), which the bundled
  `.mcp.json` runs via `npx`, and
- the **plugin** itself (`ghost/.claude-plugin/plugin.json` + the `ghost` entry
  in `.claude-plugin/marketplace.json`).

Releases are **CI-published on a pushed tag**, via OIDC trusted publishing — no
`NPM_TOKEN`, no local `npm publish`, no `npm dist-tag`, no OTP. The dist-tag is
chosen by **version shape**, mirroring `@learning-with-court/cli`:

- a **prerelease** version (contains `-`, e.g. `0.1.5-dev.0`) publishes to
  **`@dev`** — the test channel;
- a **clean** version (e.g. `0.1.5`) publishes to **`@latest`** — prod.

Each version is published exactly once, to the right tag. There is no
"promote": shipping to prod is just tagging a clean version. `@latest` is
whatever clean release is current; `@dev` is the last prerelease.

```
tag ghost-mcp-v0.1.5-dev.0 ─► CI ─► ghost-blog-mcp@dev ──(test in ghost-site)
tag ghost-mcp-v0.1.5       ─► CI ─► ghost-blog-mcp@latest  (prod)
```

The bundled `ghost/.mcp.json` always references `@latest`. Dev testing opts into
`@dev` (or an exact version) via a **project-level `.mcp.json` override** in the
consuming repo, so the shipped file never has to change. See `enable-in-a-project.md`.

---

## Dev build (publish to `@dev`)

```bash
cd ghost/mcp-server
npm version prerelease --preid dev --no-git-tag-version   # e.g. 0.1.5-dev.0
V=$(node -p "require('./package.json').version")
git commit -am "chore(ghost): ghost-blog-mcp $V"
git push
git tag "ghost-mcp-v$V" && git push origin "ghost-mcp-v$V"   # triggers CI → @dev
```

Test it: in `ghost-site`, point the project `.mcp.json` at `ghost-blog-mcp@$V`
(pinning the exact version beats `@dev`, which npx may cache), restart so the MCP
respawns, and exercise the flow against a real Ghost site.

## Prod release (publish to `@latest`)

Once the dev build passes, cut a **clean** version and take it through
`feat → dev → main`, then tag it from `main`:

```bash
cd ghost/mcp-server
npm version patch --no-git-tag-version        # or minor / major — clean version
```

Bump the plugin in lockstep in **both**:

- `ghost/.claude-plugin/plugin.json` → `"version": "X.Y.Z"`
- `.claude-plugin/marketplace.json` → `"version": "X.Y.Z"` in the `ghost` entry

Commit, promote `dev → main`, then tag the release commit on `main`:

```bash
git commit -am "chore(ghost): release X.Y.Z"
# open PR to dev, merge, promote dev → main
git tag "ghost-mcp-vX.Y.Z" && git push origin "ghost-mcp-vX.Y.Z"   # CI → @latest
```

CI verifies the tag matches `package.json`, builds/typechecks/tests, and
publishes to `@latest`. Prod consumers pick it up via `npx -y ghost-blog-mcp@latest`.

---

## Automation

Publishing is handled by `.github/workflows/publish-ghost-mcp.yml`
(filename on disk: `publish-ghost-mcp-dev.yml` — kept to preserve the trusted-publisher
config). It triggers on `ghost-mcp-v*` tags, verifies the tag matches
`package.json`, builds/tests, and runs `npm publish --tag <dev|latest>` with the
dist-tag chosen by version shape. Tokenless via OIDC.

**One-time setup (npmjs.com):** a *trusted publisher* for `ghost-blog-mcp` →
repository `schuettc/claude-code-plugins`, workflow
`.github/workflows/publish-ghost-mcp-dev.yml`. Until that's set the publish step
fails with an auth error. (npm CLI ≥ 11.5 is required for tokenless OIDC; the
workflow upgrades npm first.)
</content>
