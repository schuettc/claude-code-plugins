# Feature Workflow Plugin

**Version:** 9.11.0

A Claude Code plugin for feature lifecycle management using a directory-based architecture with event-driven hooks. Capture feature ideas, plan implementations, and ship features through a review-gated pipeline — optionally with automated PR reviews from an external AI (Gemini or Codex) via GitHub Actions. Scales to **multi-repo workspaces** — coordinate several interconnected repos in one org as if they were one (see [Multi-repo workspaces](#multi-repo-workspaces)).

## What's New

### 9.11.0 — Multi-repo workspaces: cross-repo epics, contracts, coordinated deploy
- **Aggregated workspace dashboard** — in a workspace (a root with `.feature-workspace.yml`), the dashboard hook auto-detects the manifest and writes a cross-repo roll-up: per-repo counts plus combined In Progress / Backlog / Epics across the workspace and every member. Editing a member feature also refreshes the workspace aggregate (walk-up in the hook).
- **Cross-repo epics** — an epic's `children:` use namespaced `repo:id` refs (e.g. `engine:engine-api`), and `dependsOn:` uses the same form for cross-repo prerequisites. `build_workspace_by_id()` feeds the existing `compute_dispatch_waves`, so producer-first wave ordering works unchanged — each child autopilots inside its own member repo.
- **Contract-edit warning** — declare standing `contracts:` (producer → consumers) in the manifest; editing a producer member surfaces a one-time warning (marker-deduped per member) steering contract reshapes into a producer-first epic.
- **`/feature-deploy [<epic-id>]`** — coordinated deploy that walks the manifest's `deploy:` groups in producer-first order, preflighting and gating each member before the next.
- **`shared/workspace.md`** documents the day-to-day model; linked from capture / autopilot / ship.

### 9.10.0 — Workspace scaffolder
- **`/feature-init --workspace --org <org> --member <dir>=<owner/repo> …`** scaffolds a multi-repo workspace: a `.feature-workspace.yml` manifest, a `.gitignore` that nests member repos as independent clones (while keeping the shared `.claude/settings.json` tracked), `.claude/settings.json` allowlisting `git -C *` / `gh -R *`, a `CLAUDE.md` topology skeleton, the workspace's own `.feature-workflow.yml`, and `scripts/clone-members.sh`. A member is a full clone in the working tree, so `cd <member>` and the normal feature flow just works — no permission prompts.

### 9.9.0 — OCI GenAI reviewer
- **New `oci` reviewer** — `/feature-init --reviewer oci` wires PR review to OCI Generative AI's OpenAI-compatible `chat/completions` endpoint (no agentic CLI). Same label-gated plan/impl lifecycle, prompts, and `post-review.sh` as gemini/codex. Because a single chat call can't explore the repo, `oci-review.sh` gathers the PR diff plus the feature's `idea.md`/`plan.md` and sends them inline. Secret `OCI_GENAI_API_KEY`; optional vars `OCI_GENAI_BASE_URL` / `OCI_GENAI_MODEL` (default `us-ashburn-1` + `openai.gpt-4.1`).

### 9.8.1 — Suppression discipline
- **Drive-by static-analysis suppressions now FAIL impl-review** — the reviewer prompt scans diffs for newly-added `// fallow-ignore-*`, `# skylos: ignore`, `# noqa`, `# type: ignore`, `// @ts-ignore`, etc. Without an adjacent `# Why:` justification, they're Blocking findings (FAIL verdict → autopilot enters the respond loop). Legitimate suppressions (false positives, parameterized SQL, deliberately-coalesced state) with written justifications pass.
- **`pre-commit-compat.md`** documents the rule: suppressions are a last resort. Try-to-fix-first, justify if you can't, cap at 2 new suppressions per PR.

### 9.8.0 — Epic Dispatch (Plan 3)
- **`/feature-autopilot <epic-id>` walks the children to completion.** Sequential by default; `--parallel` for concurrent waves with a cap of 3 simultaneous subagents.
- **Bidirectional `epic:` ↔ `children:` sync** via `sync_epics.py` in the post-write hook. Same pattern as `replaces:` from v9.7.2 — set one direction and the other follows on the next save.
- **`compute_dispatch_waves(epic_id, features)`** topo-sorts children into parallel-safe waves. Skips shipped / tombstoned / paused children automatically. Order within a wave matches the epic's `children:` array.
- **Validation warning** for `type: Epic` features with empty `children:` (the dispatcher refuses, the dashboard surfaces it).

### 9.7.3 — Autopilot hardening
- **Pre-flight check** — `check-base-sync.sh` refuses to start a feature branch if local `<base>` is ahead/behind/diverged from `origin/<base>`. Catches the "parallel Claude Code session left unpushed commits" failure mode.
- **Mandatory worktree isolation on every dispatch** — every subagent the autopilot spawns for git work runs with `isolation: "worktree"`. No opt-out. Removes the entire class of clobber bugs where two agents in one tree overwrite each other on branch switches.
- **Workflow YAML `concurrency: cancel-in-progress`** per PR — prevents the duplicate-review-comment pattern where one plan got six review runs (including two AFTER a clean PASS).
- **Label-removal timing** — autopilot removes the active review label immediately after a PASS, before any subsequent push. Label swap from `plan-review` → `impl-review` is now two separate `gh pr edit` calls with `sleep 3` between.
- **`pre-commit-compat.md`** — guidance for projects using skylos/fallow/ruff/prettier/husky; reinforces the `--no-verify` ban.

### 9.7.2 — Replaced/replacedBy rename + auto-sync
- **`superseded` → `replaced` rename** — `state: replaced`, `replacedBy:` (singular reverse), and a new `replaces: [a, b]` forward field on the new feature.
- **`sync_replaces.py` hook** auto-sets `state: replaced` and `replacedBy: <new>` on each target when a new feature declares `replaces:`.
- **Unknown-key validation** — dashboard warns on unrecognized frontmatter keys (catches typos like the original `supersedes:` confusion).
- **Verdict-language tightening** — `CONDITIONAL PASS` cannot contain Blocking findings; Blocking → FAIL.

### 9.7.1 — Internal review path
- **Per-feature `review:` override** — `review: external | internal | skip` in `idea.md` frontmatter overrides the project default.
- **Internal review** dispatches a same-session subagent loaded with the same `templates/review-prompt-{plan,impl}.md` the CI reviewers use, captures the verdict, and posts it as a PR comment. From `wait-for-review.sh`'s perspective, indistinguishable from a CI comment.

### 9.7.0 — Foundations (state, assignee, search, dependencies)
- **State overlay** — `state: active | paused | replaced | abandoned` in `idea.md`, orthogonal to lifecycle. New `/feature-state` skill manages transitions with required companion fields.
- **Assignee** — `assignee: court` or `assignee: [court, alex]` in frontmatter; surfaced in dashboard columns and searchable.
- **`/feature-search`** with filters: `--state`, `--assignee`, `--epic`, `--depends-on`, `--archive`.
- **Stronger dependency markers** — `relatedTo: [c, d]` (soft link), `parallelSafe: true | false`. Stored `blockedBy:` is deprecated; the dashboard computes it dynamically from the graph.
- **Dashboard sections** — Paused, Archive (collapsed), Epics rollup, Validation Warnings (cycles, unknown refs, unknown frontmatter keys).

### 9.2.3 — Comment-only CI reviews
- **Simplified CI posting** — `post-review.sh` now posts reviewer output as a plain `gh pr comment` instead of parsing a VERDICT prefix to map to `--approve`/`--request-changes`. The VERDICT/inline-comments JSON protocol was too fragile — Gemini intermittently truncated before the VERDICT line, and inline comments frequently failed with HTTP 422 when the reviewer cited lines outside the diff. Reviews are advisory anyway.
- **Human-readable verdict** — review prompts still include a `### Verdict: PASS / CONDITIONAL PASS / FAIL` heading in the markdown body for humans to scan. No machine parsing required.

### 9.2 — Inline thread replies + tighter prompt filters
- **Inline responses on resolved findings** — `/feature-review-plan <id> --respond` and `/feature-review-impl <id> --respond` now fetch review threads via GraphQL, reply inline on each finding with `Resolved in <sha>: <one-line>`, and resolve the thread via the `resolveReviewThread` mutation. Disagreed findings get an inline reply explaining the reasoning but stay open.
- **No-op finding filter** — prompts explicitly reject "no change required, just confirming" commentary, hedged hypotheticals ("if a user somehow…"), and defensive additions for impossible conditions. Observed noise in early Gemini rounds drops significantly.

### 9.1 — Workflow-side review posting
- **Reviewer no longer runs `gh` commands** — Gemini/Codex output is captured by the workflow and posted via `post-review.sh`.
- **New `templates/post-review.sh`** installed into `.github/scripts/` by `/feature-init` and `/feature-init --update`.

### 9.0 — Automated PR reviews
- **Gemini + Codex in GitHub Actions** — draft PRs auto-reviewed by an external AI. See [Automated PR Reviews](#automated-pr-reviews) below.
- **`/feature-init --update`** — refresh the generated CI workflow + review prompts + `post-review.sh` in an existing project without re-running full init or re-uploading your API key.
- **Label-driven review lifecycle** — submit skills add `plan-review` / `impl-review` labels that trigger the workflow; ship removes them.

## Requirements

- **jq** - Required for JSON parsing in hooks
  ```bash
  # macOS
  brew install jq

  # Ubuntu/Debian
  sudo apt-get install jq

  # Check installation
  jq --version
  ```

## Installation

### From GitHub (recommended)
```bash
# Add the marketplace
/plugin marketplace add schuettc/claude-code-plugins

# Install the plugin
/plugin install feature-workflow@schuettc-claude-code-plugins
```

### Development Mode
```bash
git clone https://github.com/schuettc/claude-code-plugins.git
claude --plugin-dir ./claude-code-plugins/feature-workflow
```

## Feature Directory Architecture

Features are stored in directories with status determined by file presence:

```
docs/features/
├── DASHBOARD.md              # Auto-generated, read-only for Claude
├── my-feature/
│   ├── idea.md               # Problem statement + metadata (backlog)
│   ├── plan.md               # Implementation plan (in-progress)
│   └── shipped.md            # Completion notes (completed)
└── another-feature/
    └── idea.md
```

### Status Detection by File Presence

| Files Present | Status |
|---------------|--------|
| `idea.md` only | backlog |
| `idea.md` + `plan.md` | in-progress |
| `idea.md` + `plan.md` + `shipped.md` | completed |

### Key Principles

| Principle | How It Works |
|-----------|--------------|
| **Directory-based** | Each feature has its own directory |
| **Status by files** | No JSON status field - file presence determines status |
| **Auto-generated index** | DASHBOARD.md regenerated on every change |
| **Human-readable** | All data in markdown with YAML frontmatter |
| **Claude reads, hook writes** | Claude reads DASHBOARD.md, hooks regenerate it |

## Multi-repo workspaces

When several repos in one org are developed together, set up a **workspace**: a thin coordination repo with each member repo nested inside it as an independent, gitignored clone (not a submodule). Scaffold it with `/feature-init --workspace`. Launch Claude at the workspace root — every member is in the working tree, so cross-repo edits never prompt, yet each member stays its own git repo (operate on one with `git -C <dir>` / `gh -R <owner/repo>`, both allowlisted).

- **Single-member feature** → `cd <member>` and use the normal flow; docs land in that member's `docs/features/`.
- **Cross-repo feature** → an **epic** in the workspace `docs/features/`, one child per member (`children: [engine:engine-api, app:app-ui]`); `/feature-autopilot <epic>` dispatches each child into its member repo.
- **Contracts** (`contracts:` in the manifest) drive a producer-edit warning; **deploy groups** (`deploy:`) drive `/feature-deploy`.
- The dashboard auto-aggregates across the workspace and all members.

Full model + helper reference: [`skills/shared/workspace.md`](./skills/shared/workspace.md). Setup on-ramp: `project-workflow`'s `/project-init` offers it too. Design doc: [`docs/designs/2026-06-08-multi-repo-workspace.md`](../docs/designs/2026-06-08-multi-repo-workspace.md).

## Commands

All commands below are user-invocable skills. Type `/<name>` in Claude Code to trigger them.

### Setup

#### `/feature-init`
One-time setup for a new project. Creates `docs/features/`, `.feature-workflow.yml`, and — if you choose an external reviewer — generates the GitHub Actions workflow, review prompts, and `post-review.sh` under `.github/`, and uploads your API key as a repo secret.

Flags:
- `--update` — refresh the CI workflow + review prompts + `post-review.sh` from the current plugin templates without touching `.feature-workflow.yml`, your API secret, or `docs/features/`. Use this after a plugin upgrade.
- `--workspace --org <org> --member <dir>=<owner/repo> …` — scaffold a **multi-repo workspace** (a coordination repo with member repos nested as independent clones) instead of initializing a single repo. See [Multi-repo workspaces](#multi-repo-workspaces).

### Lifecycle

#### `/feature-capture`
Interactive capture for a new feature idea. Asks for type (Feature / Enhancement / Tech Debt / Bug Fix), name, problem statement, priority, effort, impact, and affected areas. Writes `docs/features/<id>/idea.md` — the hook regenerates DASHBOARD.md.

#### `/feature-plan [id]`
Produces a structured `plan.md` for a backlog feature. Runs requirements analysis, system design, and implementation breakdown using the specialized planning agents. Writing `plan.md` moves the feature to In Progress and sets the terminal statusline.

#### `/feature-review-plan [id]`
Pushes `idea.md` + `plan.md` to a feature branch, opens a draft PR targeted at your base branch, and adds the `plan-review` label. If a CI reviewer is configured, the workflow runs automatically and posts findings on the PR. If not, you trigger a reviewer manually (see [CLI fallback](#cli-fallback)).

Flags:
- `--respond` — fetch open review threads, classify each finding, implement fixes, reply inline on each thread with `Resolved in <sha>: <one-line>`, and resolve the thread via GraphQL. Disagreed findings get an inline reply but stay open.

#### `/feature-implement [id]`
Implements an approved plan. Tracks progress in `plan.md`'s progress log and keeps scope guarded by the `guarding-scope` skill.

#### `/feature-review-impl [id]`
Pushes the implementation to the same feature branch, swaps `plan-review` → `impl-review`, and triggers the impl review. Same `--respond` flow as `/feature-review-plan --respond`.

#### `/feature-ship [id]`
Final quality gates before merge. Runs the security-reviewer and qa-engineer agents, executes tests/type checks/build, removes review labels, merges the PR, and writes `shipped.md` — the hook moves the feature to Completed and clears the statusline.

### Coordination (multi-repo)

#### `/feature-deploy [id]`
Coordinated deploy across a workspace's member repos. Walks the manifest's `deploy:` groups in producer-first order, preflighting each member (clean working tree, on its release branch) and gating each group healthy before the next. With an epic id, scopes to the members that epic touched. Workspace-only — see [Multi-repo workspaces](#multi-repo-workspaces).

### Diagnostics

#### `/feature-status`
Quick snapshot of the dashboard — what's in progress, what's in the backlog, what shipped recently. Read-only.

#### `/feature-audit [id]`
Evidence-based runtime verification for a completed or in-progress feature. Injects observational logs, captures execution data, and analyzes runtime behavior to confirm the feature actually does what the plan said it would. Uses the `runtime-auditor` agent.

#### `/feature-troubleshoot`
Structured problem-definition → hypothesis → investigation → resolution → verification flow for bugs found in a shipped feature. Good for "this isn't working and I don't know why" situations.

## Feature States and Relations

Beyond the file-presence lifecycle (`idea.md` → `plan.md` → `shipped.md`), features carry an orthogonal **state** field in `idea.md` frontmatter:

| State | Meaning | Shown in |
|---|---|---|
| `active` (default) | Normal lifecycle | Backlog / In Progress / Completed |
| `paused` | Work started, blocked on something external | Paused section |
| `replaced` | Replaced by another feature (one-shot tombstone) | Archive (collapsed) |
| `abandoned` | Decided not to pursue | Archive (collapsed) |

Manage states with `/feature-state`:

```
/feature-state <id> paused --reason "Waiting on vendor"
/feature-state <id> replaced --replaced-by <new-id>
/feature-state <id> abandoned --reason "Out of scope"
/feature-state <id> active                            # resume
```

### Assignee

Add `assignee:` to `idea.md` frontmatter to track ownership. Single (`assignee: court`) or multiple (`assignee: [court, alex]`).

### Stronger Dependency Markers

| Field | Meaning |
|---|---|
| `dependsOn: [a, b]` | Hard blockers — must be completed before this can start |
| `relatedTo: [c, d]` | Soft links — informational only |
| `parallelSafe: true/false` | Can this run alongside siblings? Default `true` |

The dashboard computes `blockedBy` dynamically from the graph; you no longer need to maintain it manually. Cycles and unknown references show up as Validation Warnings on the dashboard.

### Search

Find features across all filters:

```
/feature-search --state paused
/feature-search --assignee court
/feature-search --epic auth-overhaul        # Epic concept in v9.7 (Plan 3)
/feature-search --depends-on user-roles
/feature-search --archive                   # include replaced + abandoned
```

## Per-Feature Review Override

By default, every feature uses the project-wide `reviewer:` setting from `.feature-workflow.yml`. For one-off needs, individual features can override this in their `idea.md` frontmatter:

```yaml
review: external   # use the project's configured CI reviewer
review: internal   # run an in-session review subagent and post the result as a PR comment
review: skip       # no review at all (rare; doc fixes, typo corrections)
```

Precedence: per-feature `review:` wins if set; otherwise the project default applies; if both are absent, the feature ships without review.

**Internal review** dispatches a same-session subagent with the same prompt the external CI reviewers use (`templates/review-prompt-{plan,impl}.md`), and posts the verdict as a normal PR comment. The autopilot, respond flow, and verdict classifier work identically across external and internal — the only difference is who runs the prompt.

**Skip** is for changes where review would be ceremonial — pure typo fixes, README tweaks, etc. Use sparingly; the audit trail is real value.

## Epic Dispatch

Multi-feature initiatives can be coordinated as an Epic. The epic is a feature with `type: Epic` and a `children:` list:

```yaml
# docs/features/auth-overhaul/idea.md
---
id: auth-overhaul
name: Auth Overhaul
type: Epic
priority: P0
children: [user-roles, sso-saml, mfa-totp]
---
```

Each child references the epic:

```yaml
# docs/features/user-roles/idea.md
---
id: user-roles
type: Feature
epic: auth-overhaul
---
```

The post-write hook auto-syncs both directions — write `epic:` on a child and the epic's `children:` updates, or vice versa. You don't have to maintain both manually.

Run `/feature-autopilot auth-overhaul` and the dispatcher walks the children in topo order, running each via its own subagent. Sequential by default; pass `--parallel` to run independent children concurrently.

```
/feature-autopilot auth-overhaul             # sequential (default)
/feature-autopilot auth-overhaul --parallel  # parallel waves where deps allow
```

Every dispatched subagent runs in its own worktree (`isolation: "worktree"`) — no shared-tree collisions, no PR-identity confusion. Concurrency cap in parallel mode is 3.

When the last non-skipped child ships, the dispatcher offers to write the epic's `shipped.md`. Decline to keep the epic open.

See [skills/feature-autopilot/epic-dispatch.md](skills/feature-autopilot/epic-dispatch.md) for the full procedure.

## Automated PR Reviews

Every feature can be reviewed twice — once at the plan stage, once at the implementation stage — by an external AI reviewer (Gemini or Codex) running in GitHub Actions. Reviews are posted as PR comments with a human-readable verdict (PASS / CONDITIONAL PASS / FAIL) that the author reads and acts on.

### Setup (one command)

```bash
/feature-init
```

When prompted, choose `gemini` or `codex` as the reviewer and paste the corresponding API key. The init script then:

1. Writes `.github/workflows/feature-review.yml` from the plugin's template for your chosen reviewer.
2. Writes `.github/review-prompt-plan.md` and `.github/review-prompt-impl.md` — the reviewer's instructions.
3. Uploads your API key as a repo secret (`GOOGLE_API_KEY` or `OPENAI_API_KEY`) via `gh secret set` — never stored on disk.
4. Records `reviewer: gemini|codex` in `.feature-workflow.yml`.

Commit and push `.github/` to your default branch. The workflow must exist on the default branch before Actions will trigger.

### Review lifecycle

```
/feature-review-plan submit  →  creates draft PR, adds "plan-review" label
                             →  GitHub Actions runs plan reviewer
                             →  review posted as PR comment with verdict
/feature-review-plan respond →  push fixes → "synchronize" re-triggers review automatically
/feature-review-impl submit  →  removes "plan-review", adds "impl-review" → same loop for impl
/feature-ship                →  removes review labels → merges PR
```

The `synchronize` trigger means pushing new commits re-runs the review without any manual re-labeling.

### CLI fallback

If you don't want GitHub Actions in the loop, leave `reviewer: none` in `.feature-workflow.yml` and instead install one of the CLI-mode reviewer plugins:

- **Gemini CLI** — [`schuettc/gemini-reviewer`](https://github.com/schuettc/gemini-reviewer)
- **Codex CLI** — [`schuettc/codex-reviewer`](https://github.com/schuettc/codex-reviewer)

Those plugins contain the same review prompts but gate on human approval before posting. They're kept in sync with this repo via `feature-workflow/reviewers/sync.sh`.

### Updating after a plugin upgrade

When you upgrade the plugin and want to pick up improvements to the workflow template or review prompts in an existing project:

```bash
/feature-init --update
```

This refreshes only:
- `.github/workflows/feature-review.yml`
- `.github/review-prompt-plan.md`
- `.github/review-prompt-impl.md`
It does **not** touch `.feature-workflow.yml`, your uploaded API secret, or `docs/features/`. Commit and push the refreshed files to your default branch.

> **Why this is needed:** the workflow and prompt files are copied into each user's repo at init time — they're not live references. A plugin upgrade cannot edit files inside consumer repos automatically, so `--update` is the explicit opt-in to re-copy them.

### What files live where

| Layer | File | Source of truth | Update mechanism |
|---|---|---|---|
| Plugin | `feature-workflow/templates/feature-review-{gemini,codex}.yml` | This repo | Normal plugin update |
| Plugin | `feature-workflow/templates/review-prompt-{plan,impl}.md` | This repo | Normal plugin update |
| Plugin | `feature-workflow/reviewers/skills/feature-review-{plan,impl}.md` | This repo (authoritative) | Edit directly |
| CLI reviewer repos | `gemini-reviewer/*/SKILL.md`, `codex-reviewer/skills/*/SKILL.md` | Mirrored from `reviewers/skills/` | Run `feature-workflow/reviewers/sync.sh` then commit/push those repos |
| User project | `.github/workflows/feature-review.yml` | Copied from plugin templates | `/feature-init --update` |
| User project | `.github/review-prompt-{plan,impl}.md` | Copied from plugin templates | `/feature-init --update` |

## File Formats

### idea.md (Feature Idea)

```markdown
---
id: dark-mode-toggle
name: Dark Mode Toggle
type: Feature
priority: P1
effort: Medium
impact: High
created: 2024-01-20
---

# Dark Mode Toggle

## Problem Statement
Users working late need reduced eye strain. Many have requested dark mode support.

## Proposed Solution
Add a toggle in settings that switches between light/dark themes.

## Affected Areas
- settings
- theme-system
- all-components
```

### plan.md (Implementation Plan)

```markdown
---
started: 2024-01-21
---

# Implementation Plan: Dark Mode Toggle

## Overview
Add theme switching with light/dark modes...

## Implementation Steps
- [ ] Create theme context
- [ ] Add CSS variables
- [ ] Update components
- [ ] Add settings toggle

## Testing Strategy
...

## Progress Log
### 2024-01-21
- Created implementation plan
- Next: Create theme context
```

### shipped.md (Completion Notes)

```markdown
---
shipped: 2024-01-25
---

# Shipped: Dark Mode Toggle

## Summary
Implemented theme switching with system preference detection...

## Key Changes
- Added ThemeContext provider
- CSS variables for all colors
- Settings toggle with persistence

## Testing
- All tests passing
- Manual testing completed

## Notes
Consider adding more themes in future.
```

### DASHBOARD.md (Auto-Generated)

```markdown
# Feature Dashboard

*Auto-generated by hooks. Do not edit directly.*
*Last updated: 2024-01-25 14:30:00*

## In Progress

| ID | Name | Priority | Started |
|----|------|----------|---------|
| [user-auth](./user-auth/) | User Authentication | P0 | 2024-01-24 |

## Backlog

| ID | Name | Priority | Effort | Added |
|----|------|----------|--------|-------|
| [api-cache](./api-cache/) | API Caching | P1 | Medium | 2024-01-20 |

## Completed

| ID | Name | Shipped |
|----|------|---------|
| [dark-mode-toggle](./dark-mode-toggle/) | Dark Mode Toggle | 2024-01-25 |
```

## How Hooks Work

Status transitions and context loading are handled automatically via event-driven hooks.

### Hook Architecture

```
Session starts  →  SessionStart hook  →  Brief project summary
User prompt     →  UserPromptSubmit   →  Detect /feature-*, load context
Claude works    →  PostToolUse        →  Set statusline, trigger dashboard
Claude done     →  Stop hook          →  Sync dashboard, clear stale statusline
```

### Registered Hooks

| Hook | Trigger | Script | Purpose |
|------|---------|--------|---------|
| SessionStart | Session start/resume | session-start.sh | Show feature status summary |
| UserPromptSubmit | Before prompt processed | prompt-handler.sh | Load context for /feature-* commands |
| Stop | After response complete | stop-verifier.sh | Sync dashboard, clear stale statusline |
| PreToolUse | Before Write/Edit | block-direct-writes.sh | Block DASHBOARD.md writes |
| PostToolUse | After Write/Edit/Bash | transition-handler.sh | Set statusline, regenerate dashboard |

### What Triggers Hook Actions

| File Written | Hook Action |
|--------------|-------------|
| `docs/features/[id]/idea.md` | Regenerate DASHBOARD.md |
| `docs/features/[id]/plan.md` | Set statusline + regenerate DASHBOARD.md |
| `docs/features/[id]/shipped.md` | Clear statusline + regenerate DASHBOARD.md |

### Blocked Writes

The PreToolUse hook blocks direct writes to:
- `docs/features/DASHBOARD.md` (auto-generated)

## Terminal Statusline

The plugin displays the current feature in Claude Code's status line.

**Setup script** (`~/dotfiles/config/claude/statusline.sh`):

```bash
#!/bin/bash
input=$(cat)
SESSION_ID=$(echo "$input" | jq -r '.session_id')
MODEL=$(echo "$input" | jq -r '.model.display_name // "Claude"')

mkdir -p ~/.claude/sessions

if [[ -n "$ITERM_SESSION_ID" ]]; then
  echo "$SESSION_ID" > ~/.claude/sessions/iterm-${ITERM_SESSION_ID}.session
fi

FEATURE=""
if [[ -f ~/.claude/sessions/${SESSION_ID}.feature ]]; then
  FEATURE=$(cat ~/.claude/sessions/${SESSION_ID}.feature)
fi

if [[ -n "$FEATURE" ]]; then
  echo "[$FEATURE] $MODEL"
else
  echo "[$MODEL] ${SESSION_ID:0:8}"
fi
```

**Add to `~/.claude/settings.json`:**

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/dotfiles/config/claude/statusline.sh"
  }
}
```

## Skills (Model-Invoked)

Skills are **automatically invoked by Claude** when context is relevant.

| Skill | Behavior | Purpose |
|-------|----------|---------|
| **checking-backlog** | Silent (read-only) | Auto-check DASHBOARD.md when discussing features |
| **tracking-progress** | Ask first (writes) | Update plan.md progress log when completing tasks |
| **displaying-status** | Silent (read-only) | Quick status overview when asking "what's next?" |
| **guarding-scope** | Silent (read-only) | Flag scope creep, suggest adding to backlog |
| **auditing-context** | Silent (read-only) | Auto-load audit session context |

## Included Agents

The plugin includes specialized agents dispatched based on feature type and workflow phase:

### Planning & Design Agents

| Agent | Purpose |
|-------|---------|
| **project-manager** | Requirements analysis, user stories |
| **code-archaeologist** | Reverse-engineer legacy code |
| **system-designer** | High-level architecture |
| **api-designer** | API/GraphQL design |
| **frontend-architect** | React component architecture |
| **integration-designer** | Frontend-backend integration |
| **ux-optimizer** | UX optimization |

### Quality Gate Agents

| Agent | Purpose |
|-------|---------|
| **security-reviewer** | OWASP Top 10, CVE scanning |
| **qa-engineer** | Test coverage, acceptance criteria |
| **test-generator** | TDD - write tests before implementation |
| **documentation-agent** | Documentation maintenance |

## Troubleshooting

### "jq is required but not installed"

Install jq using your package manager (see Requirements section).

### DASHBOARD.md not updating

Manually regenerate:
```bash
./feature-workflow/hooks/generate-dashboard.sh /path/to/project
```

### Hook not firing

1. Verify the plugin is enabled: `/plugin list`
2. Check hook scripts are executable: `chmod +x feature-workflow/hooks/*.sh`

## Philosophy

**"Never Code Without a Plan"**

This plugin enforces thoughtful planning before implementation:

1. **Capture ideas quickly** - `/feature-capture` takes ~5 minutes
2. **Plan thoroughly when ready** - `/feature-plan` takes 15-30 minutes but saves hours
3. **Ship with confidence** - `/feature-ship` ensures quality gates pass
4. **Human-readable everything** - All data in markdown, no JSON to edit

## License

MIT
