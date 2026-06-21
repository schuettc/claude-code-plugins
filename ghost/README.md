# ghost plugin

Write, revise, and push blog posts to a Ghost site — directly from Claude Code.

The plugin bundles a Ghost Admin API MCP server (auto-fetched via `npx ghost-blog-mcp`) and a set of skills that guide you from planning an article all the way to pushing a draft into Ghost. **Publishing is always a deliberate human action inside Ghost** — the plugin creates and updates drafts only.

---

## Skills

### Setup

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| setup-ghost | `/ghost:setup-ghost` | Write `.claude/ghost.local.md` with site context (URL, tone, audience) and verify the MCP connection. Run this once per repo. |

### Voice and style

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| define-voice | `/ghost:define-voice` | Interview you about tone, audience, and writing personality; produces a `voice.md` artifact used by all drafting skills. |
| build-style-guide | `/ghost:build-style-guide` | Analyse existing posts via the MCP and draft a `style-guide.md` that captures structural patterns, vocabulary, and formatting conventions. |

### Plan → draft → revise → push

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| draft-post | `/ghost:draft-post` | Turn a topic or brief into a structured post outline, then write a full draft in Markdown. |
| revise-post | `/ghost:revise-post` | Apply a round of editorial feedback (yours or from a review) to an existing draft. |
| push-draft | `/ghost:push-draft` | Push the current draft to Ghost as a draft post via the Admin API. Does **not** publish. |

### Orchestrator

| Skill | Invocation | Purpose |
|-------|-----------|---------|
| write-post | `/ghost:write-post` | End-to-end orchestrator: draft-post → revise-post → push-draft, with human review gates between phases. A preflight checks the Ghost connection and style guide first, routing you to setup-ghost / build-style-guide (or define-voice) if either is missing. |

---

## Bundled MCP

The plugin ships a `.mcp.json` that points at `ghost-blog-mcp@latest` (fetched automatically via `npx -y`). No separate install step is needed. The server exposes 7 tools covering post CRUD, tag management, and site metadata.

Credentials live in a gitignored file, not environment variables. The `setup-ghost` skill writes `.claude/ghost.creds.json` holding the two values below, and the bundled `.mcp.json` passes that path to the server via `GHOST_CREDENTIALS_FILE`. Run `/ghost:setup-ghost` once per repo to create the file and verify the connection.

| Key | Description |
|----------|-------------|
| `GHOST_API_URL` | Your Ghost site URL, e.g. `https://myblog.com` |
| `GHOST_ADMIN_API_KEY` | Admin API key from Ghost → Settings → Advanced → Integrations |

The server also reads these two as environment variables as a fallback when `GHOST_CREDENTIALS_FILE` is unset.

---

## Draft-only policy

The plugin never publishes posts. All Ghost writes go to `status: draft`. Scheduling and publishing are your actions inside the Ghost Admin UI. This keeps Claude in the role of writer/editor and you in the role of publisher.

---

## Enabling the plugin in a project

See [docs/enable-in-a-project.md](docs/enable-in-a-project.md) for the exact copy-paste recipe.
