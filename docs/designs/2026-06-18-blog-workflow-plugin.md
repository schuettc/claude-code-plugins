# Blog Workflow Plugin — Design Spec

**Date:** 2026-06-18
**Repo:** `claude-code-plugins`
**Status:** Approved design, ready for implementation planning.
**Supersedes the open questions in:** `docs/superpowers/HANDOFF-blog-workflow-plugin.md`

---

## 1. Goal

Package the blog-writing *method* we developed by hand (in `ghost-site`) into a
distributable Claude Code plugin: a **general-purpose Ghost MCP server** that
makes working with a Ghost site easy from Claude Code, plus a set of **skills**
that encode the writing process that made the output good. Author-agnostic and
config-driven — the `subaud.io` setup is just one configuration.

The plugin is the seventh in this marketplace and the **first to ship a custom
MCP server**.

---

## 2. Architecture at a glance

Three layers, each with one job:

- **MCP server** — deterministic Ghost Admin API capabilities, exposed as
  discrete tools. Stateless, scriptable, unit-testable. The *only* path to Ghost.
- **Skills** — the conversational workflows (the writing method) that call the
  MCP tools and hold the judgment.
- **Hooks** — none in v1. We add a hook only if a gate genuinely must be
  unskippable; nothing in the current design qualifies.

### Topology decisions (locked)

| Decision | Choice | Why |
|---|---|---|
| Hosting | **Local stdio** — no remote server | Single-tenant dev tool; the workflow is filesystem-/repo-local; per-author Ghost key should stay on the author's machine. Hosting would centralize every author's admin key (worse security) and add a Lambda/OAuth rig for zero benefit. |
| Client→server auth | **None** | Trusted local subprocess in the author's own session. Same as the `learning-with-court` CCA-reviewer pattern. |
| Server→Ghost auth | **Ghost Admin API key via env** | `@tryghost/admin-api` mints short-lived JWTs from the `id:secret` key. Key read from `GHOST_ADMIN_API_KEY` / `GHOST_API_URL`, never committed. |
| Dependency delivery | **npx-published npm package** | Matches the repo's existing `.mcp.json` convention (`uvx`/`npx` @latest). No native deps; pure-JS tree. Esbuild-bundle-in-plugin was considered and rejected by preference. |
| Language/stack | **TypeScript + `@modelcontextprotocol/sdk` + `@tryghost/admin-api`** | Reuses the existing Node tooling (official Ghost SDK + the hand-rolled lexical builder) verbatim; matches the TS-MCP house style (`mixcraft-app`, `learning-with-court`). A Python/uvx server would force a rewrite against an unofficial Ghost client. |

### Why not the patterns from the other repos

`bettor-help` and `mixcraft-app` are hosted, multi-tenant, OAuth-gated SaaS
products — that's what forced Clerk, API Gateway, KMS-encrypted per-user token
storage. The blog plugin has **none of those properties** (one author, one
config, local files), so it follows the *embedded local stdio* pattern instead.

---

## 3. MCP server

### 3.1 Package & wiring

- Published as e.g. `@schuettc/blog-workflow-mcp` (name TBD at implementation).
- `<plugin>/.mcp.json` wires it:

```json
{
  "mcpServers": {
    "blog-workflow": {
      "command": "npx",
      "args": ["-y", "@schuettc/blog-workflow-mcp@latest"],
      "env": {
        "GHOST_API_URL": "${GHOST_API_URL}",
        "GHOST_ADMIN_API_KEY": "${GHOST_ADMIN_API_KEY}"
      }
    }
  }
}
```

- Transport: **stdio** (local subprocess).
- The npm package carries its own semver, kept in lockstep with the plugin
  version. The repo's `release` skill gains an `npm publish` step.

### 3.2 Tool surface (v1)

Posts and pages are unified by a `type: post | page` parameter (default
`post`). Ergonomic "smarts" are baked **into the write tools**, not exposed as
separate transform tools.

| Tool | Purpose | Notes |
|---|---|---|
| `ghost_site_info` | Read title/url/version | Cheap connectivity + auth check; good first call |
| `ghost_post_list` | Browse with NQL `filter`/`order`/`limit`/`fields` | Find by slug, list drafts; supports `type` |
| `ghost_post_get` | Read by id **or** slug | `formats=html,lexical`; supports `type` |
| `ghost_post_create` | Create from Markdown (card-split lexical) or HTML | `title`, `slug`, `tags`, `authors`, `status`, `visibility`, `published_at` (scheduling), `feature_image`, `custom_excerpt`, meta/SEO; returns public + editor URLs; supports `type` |
| `ghost_post_update` | Update in place | Resolves slug→id; **read-then-edit** (`updated_at`); **full metadata sync** (title/tags/excerpt/feature_image/meta, not just body); returns URLs; supports `type` |
| `ghost_post_delete` | Delete by slug/id | supports `type` |
| `ghost_tag_list` | Browse tags | |
| `ghost_tag_upsert` | Create-or-edit a tag by slug | |
| `ghost_image_upload` | Upload an image | multipart; returns CDN `url` |

### 3.3 Baked-in ergonomics (the differentiators vs the old scripts)

These solve the frictions observed across the real `ghost-site` sessions:

1. **Card-split lexical** — write tools accept Markdown and build lexical
   internally, splitting on top-level `<table>` blocks and `<!-- card -->`
   markers, so each prose chunk is independently editable in the Ghost UI.
   (Fixes the "4,000-word post becomes one giant uneditable card" problem.)
   `source: 'html'` is the fallback path for pure-HTML input.
2. **Read-then-edit on update** — fetch the current `updated_at`, then edit,
   resolving Ghost's optimistic-lock "someone else is editing" rejection.
3. **Metadata sync on update** — `update` pushes title/tags/excerpt/feature_image/
   meta, not just the lexical body. (Fixes the #1 repeated friction: locally
   edited title/tags silently not propagating.)
4. **slug→id resolution** — update/delete by slug resolve to id transparently.
5. **Returned URLs** — create/update return the public URL and the Ghost editor
   URL, so they're no longer reconstructed by hand.

H1 stripping (Ghost owns the title) stays in the write path, as today.

### 3.4 Core module layout

Pure, unit-tested core modules wrapped thinly by the MCP tools:

```
core/
  ghost-client     # wraps @tryghost/admin-api; used by all ghost_* tools
  lexical-builder  # markdown → card-split lexical (ported from build-lexical.js)
```

Tools are thin registrations over the core. `node-fetch` and `dotenv` from the
original scripts are dropped (global `fetch`; env via `.mcp.json` passthrough),
leaving `@tryghost/admin-api` + `@modelcontextprotocol/sdk` as the only runtime
deps — both pure JS.

### 3.5 Deliberately deferred to v2

Real Ghost surface with **zero** usage in the historical sessions; additive
later (same `@tryghost/admin-api` shape), not a rewrite:

- Members / labels, newsletters, tiers / offers (audience + monetization)
- Media / file upload, staff / users, webhooks, post-copy

**Probably skip entirely:** themes, settings edit, redirects, snippets.

---

## 4. Skills

Six skills. The two style skills sit outside the linear flow (setup +
continuous refinement); the rest implement the baseline process.

### 4.1 Baseline process

**plan → draft → revise → post**

| Step | Skill | What happens | Ghost state |
|---|---|---|---|
| plan | *(folded into `draft-post`)* | settle angle + outline (opening beat) | — |
| draft | `draft-post` | write the whole draft to a local `.md`, self-audit against anti-patterns | local only |
| revise | `revise-section-by-section` | section-by-section three-axis refinement, author in the loop | local only |
| post | `push-to-ghost` | pull-guard → upload feature image → create/update Ghost **draft** → verify cards + links → return editor URL | **draft, never published** |

The middle (draft, revise) is deliberately **local-only — no Ghost round-trips.**
That is the core process lesson encoded as architecture: iterate on one local
file, don't repeatedly post.

### 4.2 The style-guide subsystem

The style guide is a **living document** with multiple input sources, not a
one-shot corpus scan. Two skills build and maintain it:

- **`style-interview`** *(elicitation)* — a conversational pass where the author
  explains, in their own words, audience/tone/voice and what they admire or
  reject. Also **gathers reference material**: links to docs/pages they've
  written or admire (external URLs via WebFetch, local files via Read). Makes the
  **cold-start** case (no published posts) work, and captures stated intent +
  admired exemplars.
- **`build-style-guide`** *(synthesis + continuous merge)* — synthesizes
  `style-guide.md` from **whatever inputs exist**: interview answers, reference
  docs, and the Ghost corpus (`ghost_post_list`/`get`, `filter: status:published`).
  Runs at setup and continuously thereafter.

`style-guide.md` is structured by provenance so continuous updates don't thrash:

- **Stated voice** (from interview) — *authoritative*; never silently overwritten.
- **Observed patterns** (from corpus + references) — *refreshable* derived
  rhythm/structure/opening-closing/code+table conventions.
- **Anti-patterns** — the forbidden list (forbidden headings, editorial
  restatements, hedge words, AI transitions, cleft/focus-frames, cute closers,
  code-fence width), from both sources.
- **Provenance log** — which posts/sources have been folded in (idempotent,
  auditable).

### 4.3 Continuous learning trigger

**`push-to-ghost` is the happiness signal.** Final publish happens manually in
the Ghost UI (outside our flow), so we learn two ways:

1. **Immediate** — on a successful push the author is happy with, `push-to-ghost`
   folds that post into the style guide right then.
2. **Eventual reconciliation** — `build-style-guide` pulls `status:published`
   posts, so anything published by hand in Ghost gets incorporated next run.

This keeps the guide continuously updating despite the manual final publish. The
distillation needs the model's judgment, so it lives as a **skill step, not a
hook.**

### 4.4 draft vs revise (distinct modes, not stages)

- **`draft-post`** — *create*: generate prose from the outline, whole-post in one
  sweep, mostly autonomous, then self-audit. Produces a complete first draft.
- **`revise-section-by-section`** — *refine*: improve existing prose, one section
  at a time, deeply interactive, iterating until each section passes. The
  three axes: **formatting** (code wrapping ≤~70 chars for Ghost, dense
  paragraphs → lists, table/card rendering), **voice** (the anti-patterns),
  **content/accuracy** (every command/flag/claim verified against real source).

### 4.5 The orchestrator

- **`write-post`** *(thin)* — walks the happy path draft → revise → push, stopping
  at draft-in-Ghost. The six discrete skills remain invocable à la carte (jump
  straight to revise or push on an existing draft).

### 4.6 Draft-only policy

`ghost_post_create`/`update` keep full `status` capability (draft/published/
scheduled) — it's a general Ghost MCP. The **`push-to-ghost` skill enforces the
v1 policy: always `status: draft`**, and ends by handing the author the editor
URL with "review and publish in Ghost when you're ready." Capability in the
tool, policy in the skill.

### 4.7 Skill → MCP tool map

| Skill | MCP tools |
|---|---|
| `style-interview` | *(none — WebFetch/Read)* |
| `build-style-guide` | `ghost_site_info`, `ghost_post_list`, `ghost_post_get` |
| `draft-post` | *(none — local file; lint is skill logic)* |
| `revise-section-by-section` | *(none — local file)* |
| `push-to-ghost` | `ghost_post_get` (pull-guard), `ghost_image_upload`, `ghost_post_create`/`update`, `ghost_tag_upsert`, `ghost_post_list` (slug verify) |
| `write-post` | *(orchestrates the above)* |

Ghost calls cluster at the **two ends** (learn-from-corpus, push); the middle is
local. Pull-guard and lint are **skill behaviors** (transforms/judgment), not
MCP tools.

---

## 5. Configuration (author-agnostic)

- **Non-secret config** lives in `.claude/blog-workflow.local.md` (the
  plugin-settings pattern — YAML frontmatter + markdown): corpus source,
  style-guide path, default tags, default visibility / "early-access" behavior,
  local drafts directory.
- **Secret** (Ghost Admin key) stays in env (`GHOST_ADMIN_API_KEY`,
  `GHOST_API_URL`), passed through `.mcp.json`. Never in config, never committed.
- The old subaud paywall logic (auto `early-access` tag + `visibility: paid`)
  becomes **config-driven defaults the `push-to-ghost` skill applies** — not
  hardcoded anywhere in the MCP.

---

## 6. Repo conventions

- Plugin at `claude-code-plugins/blog-workflow/` (name TBD; lean `blog-workflow`)
  with `.claude-plugin/plugin.json`, `skills/`, `.mcp.json`, and the MCP package.
- Register in `.claude-plugin/marketplace.json`.
- Own semver in `plugin.json`, kept in lockstep with the npm package version.
- `release` skill extended with `npm publish`.

---

## 7. Testing

- **MCP core** — unit tests on `lexical-builder` (card-split boundaries, H1
  strip, cardSummary/cardCount) and `ghost-client` wrappers (mocked
  `@tryghost/admin-api`), in the style of `mixcraft-app/packages/mcp-server/
  src/mcp-server.test.ts`. Tool registration smoke tests.
- **Skills** — validated via the plugin-dev tooling and a dogfood run.

---

## 8. Non-goals (v1)

- No hosting / remote server / OAuth.
- No actual publishing or scheduling from skills (draft-only policy).
- No members/tiers/offers/newsletters/webhooks tools (deferred to v2).
- No NASA APOD or any subaud-specific feature-image sourcing.
- No hooks.

---

## 9. Follow-on (not part of this spec)

The **meta blog post** — written later in `ghost-site` by running the plugin's
own process on itself — announcing the method. Out of scope here.
