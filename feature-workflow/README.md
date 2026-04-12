# Feature Workflow Plugin

**Version:** 9.0.0

A Claude Code plugin for feature lifecycle management using a directory-based architecture with event-driven hooks. Capture feature ideas, plan implementations, and ship features through a review-gated pipeline — optionally with automated PR reviews from an external AI (Gemini or Codex) via GitHub Actions.

## What's New in 9.0

- **Automated PR Reviews** — draft PRs can be auto-reviewed by Gemini or Codex via GitHub Actions. See [Automated PR Reviews](#automated-pr-reviews) below.
- **`/feature-init --update`** — refresh the generated CI workflow + review prompts in an existing project without re-running full init or re-uploading your API key.
- **Bot approval setup** — `feature-init` automatically enables the repo-level "Allow GitHub Actions to approve pull requests" setting so PASS verdicts actually land as approvals.
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

## Commands

### `/feature-capture`

Interactive workflow for adding features to the backlog.

**Usage:**
```
/feature-capture
```

**What it does:**
1. Asks questions to capture the feature:
   - Item type (Feature, Enhancement, Tech Debt, Bug Fix)
   - Feature name
   - Problem statement
   - Priority (P0, P1, P2)
   - Effort estimate (Small, Medium, Large)
   - Impact level (Low, Medium, High)
   - Affected areas (optional)

2. Creates `docs/features/[id]/idea.md` with frontmatter metadata

3. Hook automatically regenerates DASHBOARD.md

### `/feature-plan [feature-id]`

Start implementing a feature from the backlog with comprehensive planning.

**Usage:**
```
/feature-plan dark-mode-toggle
```

Or without an ID to see available items:
```
/feature-plan
```

**What it does:**
1. **Feature Selection** - Choose from DASHBOARD.md backlog or validate provided ID
2. **Requirements Analysis** - Deep dive with project-manager agent
3. **System Design** - Adaptive architecture planning based on feature type
4. **Implementation Plan** - Creates structured plan with actionable steps
5. **Write plan.md** - Creates the plan file, triggering status change
6. **Kickoff Summary** - Creates todos and provides next steps

Writing `plan.md` triggers the hook to:
- Set terminal statusline to feature ID
- Regenerate DASHBOARD.md (feature moves to In Progress)

### `/feature-ship [feature-id]`

Complete a feature with quality gates.

**Usage:**
```
/feature-ship dark-mode-toggle
```

Or without an ID to see in-progress items:
```
/feature-ship
```

**What it does:**
1. **Pre-flight Check** - Verify feature is in-progress
2. **Security Review** - Run security-reviewer agent (BLOCKS on Critical/High)
3. **QA Validation** - Run qa-engineer agent
4. **Final Verification** - Run tests, type checks, build
5. **Write shipped.md** - Creates completion notes, triggering status change
6. **Summary** - Display completion report

Writing `shipped.md` triggers the hook to:
- Clear terminal statusline
- Regenerate DASHBOARD.md (feature moves to Completed)

## Automated PR Reviews

Every feature can be reviewed twice — once at the plan stage, once at the implementation stage — by an external AI reviewer (Gemini or Codex) running in GitHub Actions. Reviews post comments and requested changes directly on the draft PR, and on a PASS verdict the bot approves the PR automatically.

### Setup (one command)

```bash
/feature-init
```

When prompted, choose `gemini` or `codex` as the reviewer and paste the corresponding API key. The init script then:

1. Writes `.github/workflows/feature-review.yml` from the plugin's template for your chosen reviewer.
2. Writes `.github/review-prompt-plan.md` and `.github/review-prompt-impl.md` — the reviewer's instructions.
3. Uploads your API key as a repo secret (`GOOGLE_API_KEY` or `OPENAI_API_KEY`) via `gh secret set` — never stored on disk.
4. Enables the repo-level **"Allow GitHub Actions to approve pull requests"** setting via the GitHub API. Without this, `gh pr review --approve` silently downgrades to a comment-only review.
5. Records `reviewer: gemini|codex` in `.feature-workflow.yml`.

Commit and push `.github/` to your default branch. The workflow must exist on the default branch before Actions will trigger.

### Review lifecycle

```
/feature-review-plan submit  →  creates draft PR, adds "plan-review" label
                             →  GitHub Actions runs plan reviewer
                             →  comments posted inline, PASS = approval, FAIL = changes requested
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
- Re-applies the bot-approval repo setting (idempotent)

It does **not** touch `.feature-workflow.yml`, your uploaded API secret, or `docs/features/`. Commit and push the refreshed files to your default branch.

> **Why this is needed:** the workflow and prompt files are copied into each user's repo at init time — they're not live references. A plugin upgrade cannot edit files inside consumer repos automatically, so `--update` is the explicit opt-in to re-copy them.

### What files live where

| Layer | File | Source of truth | Update mechanism |
|---|---|---|---|
| Plugin | `feature-workflow/templates/feature-review-{gemini,codex}.yml` | This repo | Normal plugin update |
| Plugin | `feature-workflow/templates/review-prompt-{plan,impl}.md` | Generated from `reviewers/skills/*.md` | Normal plugin update |
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
