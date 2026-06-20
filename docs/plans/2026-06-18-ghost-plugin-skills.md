# Ghost Plugin (Skills + Packaging) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Skill-authoring tasks use the `skill-creator` skill to write and `plugin-dev:skill-reviewer` (or `skill-reviewer`) to validate, instead of red/green unit tests.

**Goal:** Turn the tested `ghost-mcp` server (Plan 1) into an installable Claude Code plugin named `ghost` — seven skills implementing plan → draft → revise → push, a bundled MCP, marketplace registration, and project-level-only enablement — so it can be enabled and dogfooded in `ghost-site`.

**Architecture:** The plugin at `ghost/` bundles `.claude-plugin/plugin.json`, a bundled `.mcp.json` (runs `npx -y ghost-mcp@latest` with env passthrough), and `skills/`. Skills hold the writing method and judgment; the MCP holds deterministic Ghost I/O (Plan 1). Enablement is project-scoped (the bundled MCP inherits the plugin's scope), so the skills + MCP activate only in opted-in repos.

**Tech Stack:** Markdown `SKILL.md` files (YAML frontmatter), `plugin.json` / `marketplace.json` manifests, the Plan 1 TypeScript MCP (`ghost/mcp-server/`), and the repo's existing `release` skill.

## Global Constraints

- Plugin name `ghost`; lives at `ghost/` with `.claude-plugin/plugin.json`, `.mcp.json`, `skills/`, and the `mcp-server/` package (Plan 1).
- **Project-level-only enablement (hard requirement, spec §5.1):** the bundled `.mcp.json` and all skills must activate only where the plugin is enabled in a project's `.claude/settings.json`. Never instruct user-level (`~/.claude/settings.json`) enablement. `setup-ghost` enforces and verifies this.
- **Secrets** (`GHOST_API_URL`, `GHOST_ADMIN_API_KEY`) live in the consuming repo's `.claude/settings.local.json` `env` block (gitignored) or the shell, expanded into `.mcp.json` via `${...}`. Never committed, never logged.
- **Draft-only policy (spec §4.7):** `push-draft` always writes `status: draft`; final publish is a human action in the Ghost UI. The MCP exposes full `status` capability; the policy lives in the skill.
- **Author-agnostic:** no subaud-specific hardcoding. The paywall behavior (`early-access` tag + `visibility: paid`) is config-driven defaults in `ghost.local.md`, applied by `push-draft`.
- Skill names (best-practice, spec §4): `setup-ghost`, `define-voice`, `build-style-guide`, `draft-post`, `revise-post`, `push-draft`, `write-post`. Invoked as `ghost:<name>`.
- Skill descriptions describe ONLY triggering conditions (when to use), not the workflow steps (per Anthropic skill guidance).
- The seven MCP tools (Plan 1): `ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_post_create`, `ghost_post_update`, `ghost_tag_list`, `ghost_image_upload`.
- Skill → MCP map (spec §4.8): `setup-ghost`→`ghost_site_info`; `build-style-guide`→`ghost_site_info`/`ghost_post_list`/`ghost_post_get`; `push-draft`→`ghost_post_get`/`ghost_image_upload`/`ghost_post_create`/`update`/`ghost_tag_list`/`ghost_post_list`; `define-voice`/`draft-post`/`revise-post`→no MCP (local + WebFetch/Read); `write-post`→orchestrates.

---

### Task 1: MCP hardening (the two deferred one-liners)

**Files:**
- Modify: `ghost/mcp-server/src/server.ts` (add zod `.refine` to `ghost_post_get` and `ghost_post_update`)
- Modify: `ghost/mcp-server/test/server-read.test.ts` and `test/server-write.test.ts` (assert the refine)
- Modify: `ghost/mcp-server/package.json` (`prepublishOnly`)

**Interfaces:**
- Consumes: the Plan 1 server (`buildServer`).
- Produces: `ghost_post_get`/`ghost_post_update` reject calls with neither `id` nor `slug` at the tool-validation layer; `prepublishOnly` runs typecheck.

- [ ] **Step 1: Write the failing tests**

Add to `test/server-read.test.ts`:

```ts
it("ghost_post_get rejects when neither id nor slug is given", async () => {
  const mcp = await connect(fakeClient());
  const res: any = await mcp.callTool({ name: "ghost_post_get", arguments: {} });
  expect(res.isError).toBe(true);
});
```

Add to `test/server-write.test.ts`:

```ts
it("ghost_post_update rejects when neither id nor slug is given", async () => {
  const mcp = await connect(fakeClient());
  const res: any = await mcp.callTool({ name: "ghost_post_update", arguments: { markdown: "x" } });
  expect(res.isError).toBe(true);
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ghost/mcp-server && npx vitest run test/server-read.test.ts test/server-write.test.ts`
Expected: the two new cases FAIL (the tool currently accepts empty args and calls the client).

- [ ] **Step 3: Add the refine guards in `src/server.ts`**

The MCP SDK accepts a raw zod shape for `inputSchema`; to add a cross-field refine, wrap the shape's object and validate inside the handler (the SDK's `inputSchema` is a shape, so enforce the rule at the top of each handler):

For `ghost_post_get`, change the handler to guard first:

```ts
    async ({ type, id, slug }) => {
      if (!id && !slug) {
        return { isError: true, content: [{ type: "text" as const, text: "Provide id or slug." }] };
      }
      return json(await client.getPost({ type: type as PostType, id, slug }));
    },
```

For `ghost_post_update`, guard the same way at the top of its handler (it has `id` + `slug` in `writeFields`+`id`):

```ts
    async (args) => {
      if (!args.id && !args.slug) {
        return { isError: true, content: [{ type: "text" as const, text: "Provide id or slug to identify the post." }] };
      }
      return json(await client.updatePost({ ...args, type: args.type as PostType }));
    },
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ghost/mcp-server && npx vitest run test/server-read.test.ts test/server-write.test.ts`
Expected: PASS, including the two new cases.

- [ ] **Step 5: Add typecheck to `prepublishOnly`**

In `ghost/mcp-server/package.json`, change:

```json
    "prepublishOnly": "npm run build && npm test"
```
to:
```json
    "prepublishOnly": "npm run build && npm run typecheck && npm test"
```

- [ ] **Step 6: Full suite + typecheck**

Run: `cd ghost/mcp-server && npm test && npm run typecheck`
Expected: all green (34 tests), typecheck clean.

- [ ] **Step 7: Commit**

```bash
git add ghost/mcp-server/src/server.ts ghost/mcp-server/test ghost/mcp-server/package.json
git commit -m "feat(ghost-mcp): refine id||slug on get/update; typecheck in prepublishOnly"
```

---

### Task 2: Plugin manifest + bundled MCP + marketplace registration

**Files:**
- Create: `ghost/.claude-plugin/plugin.json`
- Create: `ghost/.mcp.json`
- Modify: `.claude-plugin/marketplace.json` (register the `ghost` plugin)
- Reference: model `feature-workflow/.claude-plugin/plugin.json` and `website-deployment/.mcp.json` for shape.

**Interfaces:**
- Produces: an installable, structurally valid `ghost` plugin entry whose bundled MCP runs `npx -y ghost-mcp@latest`.

- [ ] **Step 1: Read the existing conventions**

Read `feature-workflow/.claude-plugin/plugin.json` and the root `.claude-plugin/marketplace.json` to match field shape, version style, and the marketplace entry format exactly.

- [ ] **Step 2: Create `ghost/.claude-plugin/plugin.json`**

```json
{
  "name": "ghost",
  "version": "0.1.0",
  "description": "Write, revise, and push blog posts to a Ghost site from Claude Code — a Ghost Admin API MCP plus a plan→draft→revise→push skill set.",
  "author": { "name": "Court Schuett" },
  "license": "MIT"
}
```

(Match any additional required fields observed in `feature-workflow/.claude-plugin/plugin.json` — e.g. `keywords` — to keep the manifest consistent with the repo.)

- [ ] **Step 3: Create the bundled `ghost/.mcp.json`**

```json
{
  "mcpServers": {
    "ghost": {
      "command": "npx",
      "args": ["-y", "ghost-mcp@latest"],
      "env": {
        "GHOST_API_URL": "${GHOST_API_URL}",
        "GHOST_ADMIN_API_KEY": "${GHOST_ADMIN_API_KEY}"
      }
    }
  }
}
```

- [ ] **Step 4: Register in `.claude-plugin/marketplace.json`**

Add a `ghost` entry to the `plugins` array, matching the exact shape of the existing entries (source/path, name, description). Copy the structure of a sibling entry verbatim and adjust the values.

- [ ] **Step 5: Validate the plugin structure**

Use the `plugin-dev:plugin-validator` agent (or `plugin-validator`) on `ghost/`. Expected: manifest valid, `.mcp.json` valid, marketplace entry resolves. Fix any structural errors it reports.

- [ ] **Step 6: Commit**

```bash
git add ghost/.claude-plugin ghost/.mcp.json .claude-plugin/marketplace.json
git commit -m "feat(ghost): plugin manifest, bundled MCP wiring, marketplace registration"
```

---

### Task 3: Config schema + `ghost.local.md` template

**Files:**
- Create: `ghost/skills/setup-ghost/ghost.local.example.md` (the committed example/template the skill copies)
- Reference: spec §5 for the fields.

**Interfaces:**
- Produces: the canonical non-secret config shape (`.claude/ghost.local.md`) used by `setup-ghost`, `build-style-guide`, `draft-post`, `push-draft`.

- [ ] **Step 1: Create the example config template**

`ghost/skills/setup-ghost/ghost.local.example.md`:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add ghost/skills/setup-ghost/ghost.local.example.md
git commit -m "feat(ghost): per-project config template (ghost.local.md)"
```

---

### Task 4: `setup-ghost` skill

**Files:**
- Create: `ghost/skills/setup-ghost/SKILL.md`

**Authoring:** Use `skill-creator` to write, `plugin-dev:skill-reviewer` to validate. No unit tests; acceptance = skill-reviewer pass + the structural checklist below.

**Frontmatter (exact):**
```yaml
---
name: setup-ghost
description: Use when first connecting a project to a Ghost site for the ghost plugin, or whenever Ghost credentials are missing/unverified — onboards the Ghost Admin API key, enables the plugin at project level, and verifies the connection. Triggers on "set up ghost", "connect my ghost site", "ghost credentials", "the ghost mcp isn't working".
---
```

**Required body sections (author the prose per spec §4.6 + §5.1):**
1. **Acquire the Admin API key** — Ghost Admin → Settings → Advanced → Integrations → *Add custom integration* → copy the **Admin API Key** (`id:secret`) and **API URL**.
2. **Enable the plugin at PROJECT level** — write `enabledPlugins: { "ghost@<marketplace>": true }` into the project's `.claude/settings.json` (committed). Explicit warning: do NOT enable in `~/.claude/settings.json` (would activate skills + MCP globally). Note `/plugin marketplace add` is user-level and only makes the plugin available.
3. **Store secrets** — put `GHOST_API_URL` and `GHOST_ADMIN_API_KEY` in `.claude/settings.local.json` `env` block (gitignored), expanded into the bundled `.mcp.json`. Add `.claude/settings.local.json` to `.gitignore` if absent.
4. **Write non-secret config** — copy `ghost.local.example.md` → `.claude/ghost.local.md`, fill in `drafts_dir`, `default_tags`, etc.
5. **Verify** — run `/reload-plugins` if needed, then call `ghost_site_info` to confirm the key works; have the user run `/mcp` to confirm the `ghost` server is connected here, and (gotcha) absent in other projects.
6. **Next step** — point to `define-voice` (cold start) or `build-style-guide` (existing corpus).

**Acceptance checklist:**
- [ ] Frontmatter `name`/`description` exact; description is triggers-only.
- [ ] Enforces project-level enablement; warns against user-level.
- [ ] Secrets routed to `settings.local.json`/shell, never committed.
- [ ] Uses `ghost_site_info` to verify.
- [ ] `plugin-dev:skill-reviewer` returns approved.

- [ ] **Step 1: Author the skill** (skill-creator), following the sections above.
- [ ] **Step 2: Validate** with `plugin-dev:skill-reviewer`; fix findings.
- [ ] **Step 3: Commit**

```bash
git add ghost/skills/setup-ghost/SKILL.md
git commit -m "feat(ghost): setup-ghost onboarding skill"
```

---

### Task 5: `define-voice` skill

**Files:**
- Create: `ghost/skills/define-voice/SKILL.md`

**Frontmatter (exact):**
```yaml
---
name: define-voice
description: Use when establishing or refining how an author wants to sound before writing Ghost posts, especially with no published corpus yet (cold start) — interviews the author about audience, tone, and admired references, and gathers reference material to seed the style guide. Triggers on "define my voice", "set up my writing style", "I'm starting a new blog", "here are posts I like".
---
```

**Required body sections (per spec §4.2):**
1. **Interview** — audience, purpose, tone, what the author admires and rejects, in their own words. One question at a time.
2. **Gather references** — collect links to docs/pages the author wrote or admires (fetch external URLs via WebFetch, local files via Read).
3. **Hand off** — write the raw interview answers + reference notes to a location `build-style-guide` reads (e.g. `.claude/ghost-voice-inputs.md`), then invoke / point to `build-style-guide` to synthesize.

**Acceptance:** frontmatter exact (triggers-only description); cold-start path works without a corpus; `skill-reviewer` approved.

- [ ] **Step 1: Author** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/define-voice/SKILL.md
git commit -m "feat(ghost): define-voice elicitation skill"
```

---

### Task 6: `build-style-guide` skill + style-guide format

**Files:**
- Create: `ghost/skills/build-style-guide/SKILL.md`
- Create: `ghost/skills/build-style-guide/style-guide-template.md` (the living-doc structure)

**Frontmatter (exact):**
```yaml
---
name: build-style-guide
description: Use to create or update the per-author Ghost style guide from all available signals — interview answers, reference docs, and the published corpus — and to fold a newly approved post into it. Triggers on "build my style guide", "update the style guide", "learn my voice from my posts", and is invoked by push-draft after a successful push.
---
```

**Required body sections (per spec §4.2–4.3):**
1. **Inputs** — read interview/reference notes (from `define-voice`), and pull the corpus via `ghost_post_list`/`ghost_post_get` using `corpus_filter`/`corpus_limit` from `ghost.local.md` (`ghost_site_info` first to confirm connection). Cold start works with no corpus.
2. **Synthesize the living `style-guide.md`** with provenance-structured sections (see template): **Stated voice** (authoritative, from interview — never silently overwritten), **Observed patterns** (refreshable, derived from corpus + references), **Anti-patterns** (forbidden headings, editorial restatements, hedge words, AI transitions, cleft/focus-frames, cute closers, code-fence width), **Provenance log** (which posts/sources folded in — idempotent).
3. **Continuous merge** — when invoked after a push with a newly approved post, append it to the provenance log, re-derive the Observed section, and surface any guidance change for a quick confirm. Never override Stated voice.

`style-guide-template.md` contains the four-section skeleton with headers and a one-line description under each.

**Acceptance:** frontmatter exact; produces the four-section guide; continuous-merge path documented; corpus pull respects config; `skill-reviewer` approved.

- [ ] **Step 1: Author skill + template** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/build-style-guide
git commit -m "feat(ghost): build-style-guide synthesis + living-doc template"
```

---

### Task 7: `draft-post` skill (+ anti-pattern lint checklist)

**Files:**
- Create: `ghost/skills/draft-post/SKILL.md`
- Create: `ghost/skills/draft-post/anti-patterns.md` (the self-audit grep checklist)

**Frontmatter (exact):**
```yaml
---
name: draft-post
description: Use to write the first full draft of a Ghost blog post locally, matching the author's style guide, then self-audit it against the anti-pattern checklist. Triggers on "draft a post about X", "write the first draft", "start a new blog post".
---
```

**Required body sections (per spec §4.1, §4.4):**
1. **Plan (opening beat)** — settle angle + outline; optionally `ghost_post_list` to avoid re-treading a published topic.
2. **Draft to the local `.md`** in `drafts_dir` (the single source of truth) — no Ghost round-trips. Read the style guide; match Stated voice + Observed patterns.
3. **Self-audit** against `anti-patterns.md` (greps for forbidden headings, editorial restatements, hedge words, AI transitions, cleft/focus-frames, cute closers, code-fence width ≤~70 for Ghost). Fix, don't just report.
4. **Hand off** — point to `revise-post`.

`anti-patterns.md` lists each anti-pattern with a concrete grep/regex and a one-line "why".

**Acceptance:** local-file-only (no MCP calls); self-audit checklist concrete; `skill-reviewer` approved.

- [ ] **Step 1: Author skill + checklist** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/draft-post
git commit -m "feat(ghost): draft-post skill + anti-pattern self-audit checklist"
```

---

### Task 8: `revise-post` skill

**Files:**
- Create: `ghost/skills/revise-post/SKILL.md`

**Frontmatter (exact):**
```yaml
---
name: revise-post
description: Use to revise an existing local Ghost draft section by section with the author, improving formatting, voice, and accuracy. Triggers on "revise this post", "let's go through it section by section", "tighten this draft".
---
```

**Required body sections (per spec §4.4):**
1. **Operate on the local `.md`** — no Ghost round-trips.
2. **Section-by-section, author in the loop** — for each section apply the **three axes**: **formatting** (code wrapping ≤~70 chars for Ghost, dense paragraphs → lists, table/card rendering), **voice** (the anti-patterns), **content/accuracy** (verify every command/flag/claim against real source — never fabricate). Iterate per section until approved.
3. **Hand off** — point to `push-draft` when all sections pass.

**Acceptance:** interactive, per-section; three axes explicit; accuracy axis forbids fabrication; `skill-reviewer` approved.

- [ ] **Step 1: Author** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/revise-post/SKILL.md
git commit -m "feat(ghost): revise-post section-by-section skill"
```

---

### Task 9: `push-draft` skill

**Files:**
- Create: `ghost/skills/push-draft/SKILL.md`

**Frontmatter (exact):**
```yaml
---
name: push-draft
description: Use to push a finished local Ghost draft to the Ghost site as a draft (never published) — pull-guards against in-editor edits, uploads the feature image, creates or updates the post, verifies links, and feeds the approved post back into the style guide. Triggers on "push this to ghost", "send the draft to ghost", "publish to ghost as a draft".
---
```

**Required body sections (per spec §4.1, §4.3, §4.6, §4.7):**
1. **Pull-guard** — if updating, `ghost_post_get` the live lexical, reconstruct to text, diff against the local `.md`; fold any in-editor changes into the local file FIRST.
2. **Feature image** — if set, `ghost_image_upload` and use the returned URL.
3. **Push as a DRAFT** — `ghost_post_create` (new) or `ghost_post_update` (existing, by slug). **Always `status: draft`** (draft-only policy). Apply `ghost.local.md` defaults (tags incl. optional `early_access`, visibility). Resolve real slug; use `ghost_tag_list` to attach the canonical tag slug. Return the editor URL with "review and publish in Ghost when you're ready."
4. **Verify** — confirm card structure (from the create/update result) and that outbound links resolve; do NOT link internal design/journey docs (ask before linking any internal doc).
5. **Feed the style guide** — on success the author is happy → invoke `build-style-guide` to fold this approved post in.

**Acceptance:** never sets a non-draft status; pull-guard precedes update; uses the documented MCP tools; link-verification + no-internal-docs rule present; `skill-reviewer` approved.

- [ ] **Step 1: Author** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/push-draft/SKILL.md
git commit -m "feat(ghost): push-draft skill (draft-only, pull-guard, feeds style guide)"
```

---

### Task 10: `write-post` orchestrator skill

**Files:**
- Create: `ghost/skills/write-post/SKILL.md`

**Frontmatter (exact):**
```yaml
---
name: write-post
description: Use to write a Ghost blog post end to end, walking the full plan→draft→revise→push flow in one guided pass. Triggers on "write a post about X end to end", "take this from idea to a ghost draft", "guide me through writing a post".
---
```

**Required body sections (per spec §4.5):**
1. **Preflight** — ensure setup is done (route to `setup-ghost` if credentials unverified) and a style guide exists (route to `define-voice`/`build-style-guide` if not).
2. **Walk the happy path** — `draft-post` → `revise-post` → `push-draft`, stopping at draft-in-Ghost. Note the discrete skills remain usable à la carte (jump straight to revise or push on an existing draft).

**Acceptance:** thin orchestrator; stops at draft (no live publish); `skill-reviewer` approved.

- [ ] **Step 1: Author** (skill-creator). **Step 2: Validate** (skill-reviewer). **Step 3: Commit**

```bash
git add ghost/skills/write-post/SKILL.md
git commit -m "feat(ghost): write-post orchestrator skill"
```

---

### Task 11: Release/publish wiring + plugin README + ghost-site setup doc

**Files:**
- Create: `ghost/README.md`
- Modify: the repo `release` skill (find it under `*/skills/release*` or the documented release path) to (a) `npm publish` `ghost-mcp` and (b) bump `ghost/.claude-plugin/plugin.json` + the `ghost` entry in `marketplace.json` in lockstep with the npm version.
- Create: `ghost/docs/enable-in-a-project.md` (the project-scoped setup recipe for consuming repos like `ghost-site`).

**Interfaces:**
- Produces: a documented, releasable plugin; a copy-paste setup recipe enforcing project-level-only enablement.

- [ ] **Step 1: Locate the existing release flow**

Find the repo's release skill/process (e.g. a `release` skill that bumps `plugin.json` + `marketplace.json`). Read it to match its mechanics before extending.

- [ ] **Step 2: Extend release to publish the MCP + lockstep versions**

Add steps so a `ghost` release: runs `cd ghost/mcp-server && npm publish` (the `prepublishOnly` guard builds + typechecks + tests), then bumps `ghost/.claude-plugin/plugin.json` `version` and the `ghost` `marketplace.json` entry to match, commits, and pushes — confirming before publish. Keep the existing feature-workflow release path untouched.

- [ ] **Step 3: Write `ghost/README.md`**

Document: what the plugin is, the seven skills (plan→draft→revise→push + setup/voice/style-guide), the bundled MCP, and that it requires the `ghost-mcp` npm package (auto-fetched via npx). Link to the enable-in-a-project recipe.

- [ ] **Step 4: Write `ghost/docs/enable-in-a-project.md`**

The exact, copy-paste recipe for a consuming repo (spec §5.1):
- `claude plugin marketplace add <marketplace>` (user-level; makes it available).
- `<repo>/.claude/settings.json` → `{ "enabledPlugins": { "ghost@<marketplace>": true } }` (committed; **project-level only — never `~/.claude/settings.json`**).
- `<repo>/.claude/settings.local.json` → `{ "env": { "GHOST_API_URL": "...", "GHOST_ADMIN_API_KEY": "..." } }` (gitignored).
- Add `.claude/settings.local.json` to `.gitignore`.
- Copy `ghost.local.example.md` → `.claude/ghost.local.md`.
- Verify: `/reload-plugins`, `/mcp` shows `ghost` connected here and absent elsewhere.

- [ ] **Step 5: Validate the whole plugin**

Run `plugin-dev:plugin-validator` on `ghost/`. Expected: all components (manifest, `.mcp.json`, 7 skills) valid and discovered.

- [ ] **Step 6: Commit**

```bash
git add ghost/README.md ghost/docs/enable-in-a-project.md <release skill path>
git commit -m "feat(ghost): release/publish wiring, README, project-scoped setup doc"
```

---

## Notes for the implementer

- **Do not run `npm publish` or push** during execution — Task 11 wires the release *process*; the actual publish/merge is a separate, human-gated step (the plugin can't be dogfooded from npm until `ghost-mcp` is published, which the user will trigger).
- **Skill bodies** are authored with `skill-creator` and judged by `plugin-dev:skill-reviewer`; the plan gives exact frontmatter, required sections, and acceptance — the prose is the authoring subagent's job, guided by spec §4 and the anti-pattern list.
- **Descriptions are triggers-only** (no workflow summaries) per Anthropic guidance — the skill-reviewer enforces this.

## Self-review

- **Spec coverage:** 7 skills (Tasks 4–10) ✓; bundled MCP + manifest + marketplace (Task 2) ✓; project-level-only enablement enforced in `setup-ghost` + the setup doc (Tasks 4, 11) ✓; config template (Task 3) ✓; style-guide living-doc + continuous merge (Task 6) ✓; draft-only policy in `push-draft` (Task 9) ✓; the two deferred MCP one-liners (Task 1) ✓; release/publish wiring (Task 11) ✓.
- **Placeholder scan:** code/manifest tasks carry exact content; skill tasks carry exact frontmatter + required sections + acceptance (the correct granularity for prose skills, not a vague "write the skill").
- **Type/name consistency:** skill names, MCP tool names, config field names, and the `ghost@<marketplace>` enablement key are used identically across tasks and match the spec.
