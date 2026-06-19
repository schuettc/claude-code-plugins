# Enabling the ghost plugin in a project

This guide explains how to activate the ghost plugin in a specific repository (e.g. your Ghost site's content repo). All configuration is **project-level only** — the plugin is never enabled globally.

---

## 1. Add the marketplace (once per machine)

Run this once to make the `schuettc/claude-code-plugins` marketplace available on your machine:

```bash
claude plugin marketplace add schuettc/claude-code-plugins
```

This writes to your user-level Claude config and makes the marketplace discoverable. It does **not** enable any plugin in any project.

---

## 2. Enable the plugin for this repo

In `<repo>/.claude/settings.json`, add:

```json
{
  "enabledPlugins": {
    "ghost@schuettc-claude-code-plugins": true
  }
}
```

**IMPORTANT — PROJECT-LEVEL ONLY.**
This file lives at `<repo>/.claude/settings.json` and should be committed to the repo. Never add `ghost@schuettc-claude-code-plugins` to `~/.claude/settings.json` — that would enable the plugin (and its MCP server) in every project on your machine.

---

## 3. Add credentials (gitignored, never committed)

Create `<repo>/.claude/settings.local.json`:

```json
{
  "env": {
    "GHOST_API_URL": "https://your-ghost-site.com",
    "GHOST_ADMIN_API_KEY": "your-admin-api-key-here"
  }
}
```

Obtain the Admin API key from your Ghost admin panel: **Settings → Integrations → Add custom integration**.

Then ensure this file is gitignored. Add to `<repo>/.gitignore`:

```
.claude/settings.local.json
```

---

## 4. Run setup and verify

Open Claude Code at the repo root and run:

```
/ghost:setup-ghost
```

This will:
- Prompt for site context (URL, audience, tone)
- Write `.claude/ghost.local.md` with that context (commit this file)
- Verify the MCP connection is live

Then reload plugins and confirm the MCP appears:

```
/reload-plugins
/mcp
```

You should see `ghost` listed as **connected** in this project and absent in other projects.

---

## Quick-start summary

```bash
# 1. Marketplace (once per machine)
claude plugin marketplace add schuettc/claude-code-plugins

# 2. Enable plugin (committed)
# <repo>/.claude/settings.json
{
  "enabledPlugins": { "ghost@schuettc-claude-code-plugins": true }
}

# 3. Credentials (gitignored)
# <repo>/.claude/settings.local.json
{
  "env": {
    "GHOST_API_URL": "https://your-ghost-site.com",
    "GHOST_ADMIN_API_KEY": "your-key"
  }
}

# Add to .gitignore
echo ".claude/settings.local.json" >> .gitignore

# 4. Setup
/ghost:setup-ghost
/reload-plugins
/mcp
```
