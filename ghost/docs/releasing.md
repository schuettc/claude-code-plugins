# Releasing the ghost plugin

This document covers the exact steps to release a new version of the ghost plugin — including the `ghost-mcp` npm package and the plugin manifest/marketplace version.

The repo's `/release` skill is currently scoped to `feature-workflow`. Extending it cleanly to support multiple plugins would require parameterising the plugin name and adding npm-publish logic; that is a worthwhile future improvement but out of scope for this initial release. Follow the manual steps below for now.

---

## Release checklist

### 1. Bump the npm package version

```bash
cd ghost/mcp-server
# Decide patch / minor / major
npm version patch   # or minor / major
```

`npm version` updates `package.json`, runs `preversion`/`postversion` hooks if any, and creates a git tag.

### 2. Build, typecheck, and test (prepublishOnly runs automatically)

```bash
cd ghost/mcp-server
npm run build
npm test
```

`prepublishOnly` in `package.json` already chains these. If anything fails, fix before continuing.

### 3. Publish the npm package

```bash
cd ghost/mcp-server
npm publish --access public
```

Confirm the new version appears at `https://www.npmjs.com/package/ghost-mcp`.

### 4. Bump the plugin manifest and marketplace entry

Update the version in **both** files to match the npm release:

- `ghost/.claude-plugin/plugin.json` — `"version": "X.X.X"`
- `.claude-plugin/marketplace.json` — `"version": "X.X.X"` in the `ghost` entry

**Both must stay in sync** — the marketplace listing is what the Discover tab shows; the manifest is what gets installed.

### 5. Commit and push

```bash
git add ghost/.claude-plugin/plugin.json .claude-plugin/marketplace.json ghost/mcp-server/package.json
git commit -m "chore(ghost): release vX.X.X"
git push
```

### 6. Update local installation (optional)

```bash
cd ~/.claude/plugins/marketplaces/schuettc-claude-code-plugins && git pull
```

Then edit `~/.claude/plugins/installed_plugins.json` to point `ghost` at the new version/cache path, and restart Claude Code.

---

## Future: generalise the /release skill

The `/release` skill at `.claude/skills/release/SKILL.md` handles version synchronisation for `feature-workflow`. To support `ghost` (and any future plugin), it should be extended to:

1. Accept a `plugin` parameter (`feature-workflow` | `ghost` | …).
2. Resolve the correct `<plugin>/.claude-plugin/plugin.json` path dynamically.
3. For plugins with an npm package, add an `npm publish` step with confirmation.

Until that generalisation is done, use this document.
