---
name: setup-ghost
description: Use when first connecting a project to a Ghost site for the ghost plugin, or whenever Ghost credentials are missing/unverified — onboards the Ghost Admin API key, enables the plugin at project level, and verifies the connection. Triggers on "set up ghost", "connect my ghost site", "ghost credentials", "the ghost mcp isn't working".
---

# Set up the Ghost plugin for this project

You are onboarding this project to a Ghost site. Work through each step in order; don't skip ahead — later steps depend on earlier ones being complete.

## Step 1: Acquire the Admin API key

In your Ghost Admin panel:

1. Go to **Settings → Advanced → Integrations**.
2. Click **Add custom integration**, give it a name (e.g. "Claude Code").
3. Copy two values — you'll need both:
   - **Admin API Key** — looks like `id:secret` (a colon-separated pair).
   - **API URL** — the base URL of your Ghost site, e.g. `https://yourblog.ghost.io`.

Keep these values ready; you'll store them in the next step. Do **not** paste them into `ghost.local.md` or any tracked file — they are secrets.

## Step 2: Enable the plugin at project level

The `ghost` plugin must be enabled **per project**, not globally. Here is why this matters:

- `/plugin marketplace add schuettc/claude-code-plugins` (user-level) makes the plugin available in your Claude Code installation but does **not** activate its skills or MCP server anywhere. It is a one-time prerequisite, not the enablement step.
- **Enablement happens in the project's `.claude/settings.json`** — the committed, project-scoped settings file. Only projects that opt in get the Ghost skills and MCP server.

> **WARNING: do NOT enable the ghost plugin in `~/.claude/settings.json`.** Doing so activates the Ghost MCP server and skills in every Claude Code session on your machine, regardless of project. The MCP server reads project-specific config that won't exist in other projects, so it will error or misbehave globally.

Add `ghost` to `enabledPlugins` in the **project's** `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "ghost@schuettc-claude-code-plugins": true
  }
}
```

If `enabledPlugins` already exists, add `"ghost@schuettc-claude-code-plugins": true` to it. This file is committed to the repo — it's how the whole team (or just you, on this project) gets the plugin.

## Step 3: Store secrets in settings.local.json

The Ghost API URL and Admin API Key are secrets. Store them in `.claude/settings.local.json` (the gitignored, local-only counterpart to `settings.json`):

```json
{
  "env": {
    "GHOST_API_URL": "https://yourblog.ghost.io",
    "GHOST_ADMIN_API_KEY": "your-id:your-secret"
  }
}
```

Replace the placeholder values with the ones you copied in Step 1.

Then confirm `.claude/settings.local.json` is gitignored. Check or update `.gitignore`:

```bash
grep -q 'settings.local.json' .gitignore || echo '.claude/settings.local.json' >> .gitignore
```

> **Never put `GHOST_API_URL` or `GHOST_ADMIN_API_KEY` in `ghost.local.md`, `settings.json`, or any other tracked file.** Secrets go only in `settings.local.json` (gitignored) or in your shell environment. The MCP server reads them from the `env` block at startup.

## Step 4: Write the non-secret project config

Create `.claude/ghost.local.md` using the Write tool with the following content:

```
Write(".claude/ghost.local.md", """
---
# Ghost plugin per-project config (non-secret). Copy to .claude/ghost.local.md.
# Secrets (GHOST_API_URL, GHOST_ADMIN_API_KEY) go in .claude/settings.local.json, NOT here.
corpus_filter: "status:published"   # NQL filter for the voice-learning corpus
corpus_limit: 25                     # how many recent posts to learn from
style_guide_path: ".claude/ghost-style-guide.md"
drafts_dir: "blog-posts/drafts"      # where local draft .md files live
default_tags: []                     # tags every post gets, e.g. ["early-access"]
default_visibility: "public"         # public | members | paid
early_access:                        # optional paywall pattern; omit to disable
  enabled: false
  tag: "early-access"
  visibility: "paid"
---

# Ghost project config

Human-readable notes about this site's writing setup. The frontmatter above is
what the skills read; this body is for your own reference.
""")
```

Then open `.claude/ghost.local.md` and fill in the frontmatter fields for your project:

- **`drafts_dir`** — path (relative to repo root) where local draft `.md` files should live, e.g. `blog-posts/drafts`.
- **`default_tags`** — tags every post gets automatically, e.g. `["engineering"]`. Leave `[]` if none.
- **`default_visibility`** — `public`, `members`, or `paid`.
- **`corpus_filter`** — NQL filter for the voice-learning corpus (default `status:published` is fine for most sites).
- **`corpus_limit`** — how many recent posts to learn from (default 25).
- **`style_guide_path`** — where `build-style-guide` will write the style guide (default `.claude/ghost-style-guide.md`).
- **`early_access`** — optional paywall pattern; leave `enabled: false` unless you use a paid-tier teaser flow.

The body section below the frontmatter is free-form notes for your own reference — write anything useful about this site's tone, structure, or publishing conventions.

Commit `ghost.local.md`:

```bash
git add .claude/ghost.local.md
git commit -m "chore(ghost): add project ghost config"
```

## Step 5: Verify the connection

**Reload the MCP server** if it was already running (or just restart Claude Code):

```
/reload-plugins
```

**Call `ghost_site_info`** to confirm the key and URL are wired correctly. The tool returns your site's title, URL, and version. A successful response means the MCP server can reach Ghost and the credentials are valid.

If `ghost_site_info` returns an authentication error:
- Double-check `GHOST_ADMIN_API_KEY` in `settings.local.json` — it must be `id:secret` format, not just the key ID.
- Confirm `GHOST_API_URL` has no trailing slash and matches your Ghost Admin URL exactly.
- Make sure `settings.local.json` was saved and Claude Code was reloaded.

**Check the MCP connection** by running:

```
/mcp
```

You should see the `ghost` server listed as **connected** here. If you open another project that does not have `ghost` in its `enabledPlugins`, the `ghost` server should be absent there — confirming the project-scoped enablement is working correctly.

## Step 6: Next step

Setup is complete. Choose your next skill based on your starting point:

- **Cold start (new site, no existing posts):** Run `/ghost:define-voice` to establish a writing voice from scratch.
- **Existing corpus (published posts you want to learn from):** Run `/ghost:build-style-guide` to extract voice and style from your existing posts.

If you're unsure, `build-style-guide` is the better default whenever your Ghost site has published content — it grounds the style guide in your real writing rather than a blank slate.
