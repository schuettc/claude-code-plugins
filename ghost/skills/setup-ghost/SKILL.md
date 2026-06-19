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

Keep these values ready; you'll save them to a gitignored credentials file in Step 3. Do **not** paste them into `ghost.local.md`, `settings.json`, or any other tracked file.

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

## Step 3: Capture your Ghost credentials (gitignored file)

The MCP server reads your Ghost API URL and Admin API Key from a gitignored JSON
file at `.claude/ghost.creds.json` in this project. The server loads it directly
at startup — reliable, and the secret stays out of version control. (No shell
`export`, no `settings.json` env block, no enable-time dialog.)

**First, look for a key you already have.** Many projects keep one in a local
`.env`. Check `infrastructure/.env.ghost-pro`, `.env`, and `.env.local` for a
`GHOST_ADMIN_API_KEY` and a Ghost URL. If you find one, offer to reuse it — read
the value straight from that file so the secret is never typed or printed.

Write `.claude/ghost.creds.json` (with the Write tool, or by reading the values
from the existing `.env`):

```json
{
  "GHOST_API_URL": "https://yourblog.ghost.io",
  "GHOST_ADMIN_API_KEY": "<id>:<secret>"
}
```

- **GHOST_API_URL** — the Ghost site base URL (no trailing slash).
- **GHOST_ADMIN_API_KEY** — the Admin API Key in `id:secret` form (24 hex chars,
  a colon, then 64 hex chars), from a Ghost custom integration.

**Gitignore it** so the secret can never be committed:

```bash
grep -q 'ghost.creds.json' .gitignore || echo '.claude/ghost.creds.json' >> .gitignore
```

The server reads this file at spawn — no dependency on Claude passing env. If the
MCP ever runs from a different working directory, set `GHOST_CREDENTIALS_FILE` to
the file's absolute path.

## Step 4: Write the non-secret project config

Create `.claude/ghost.local.md` using the Write tool with the following content:

```
Write(".claude/ghost.local.md", """
---
# Ghost plugin per-project config (non-secret). Copy to .claude/ghost.local.md.
# Secrets (Ghost API URL + Admin API Key) live in .claude/ghost.creds.json (Step 3), NOT here.
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

**Call `ghost_site_info`** to confirm the key and URL are wired correctly. The tool returns your site's title, URL, and version. A successful response means the MCP server can reach Ghost and the credentials are valid. Report the result inline to the user: on success, `✓ Connected to <title> (<url>, Ghost <version>)`; on failure, `✗ <the error>` followed by the matching fix below.

If `ghost_site_info` returns an authentication or connection error:
- Open `.claude/ghost.creds.json` and check `GHOST_ADMIN_API_KEY` is the full `id:secret` pair (24 hex chars, a colon, then 64 hex chars), not just the key ID.
- Confirm `GHOST_API_URL` has no trailing slash and matches your Ghost Admin URL exactly.
- If the MCP runs from a different working directory than the project root, the server won't find `.claude/ghost.creds.json` — the bundled `.mcp.json` passes `GHOST_CREDENTIALS_FILE=${CLAUDE_PROJECT_DIR}/.claude/ghost.creds.json`, so verify that file actually exists at that path.
- Restart Claude Code (a genuinely fresh session, not `--resume`) so the MCP server respawns and re-reads the creds file.

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
