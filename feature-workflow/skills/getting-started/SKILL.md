---
name: getting-started
description: Interactive onboarding for the feature-workflow plugin. Use when the user just installed the plugin, asks "how do I use this", "where do I start", "walk me through it", or wants a demo. Detects current project state, explains concepts tailored to that state, and optionally guides a live end-to-end walkthrough of a demo feature.
allowed-tools: Read, Write, Bash, Glob, Grep, Edit
user-invocable: true
---

# Getting Started with feature-workflow

Help a new user understand and start using the feature-workflow plugin. This skill is intentionally conversational — meet the user where they are, don't dump the whole manual on them.

## Step 1: Detect Project State

Run these checks in parallel to figure out where the user is in the setup journey:

```bash
test -f .feature-workflow.yml && echo "initialized" || echo "fresh"
test -d docs/features && ls docs/features 2>/dev/null | grep -v DASHBOARD.md | head -5
test -f .github/workflows/feature-review.yml && echo "ci-configured" || echo "no-ci"
git rev-parse --is-inside-work-tree 2>/dev/null
gh auth status 2>/dev/null && echo "gh-authenticated" || echo "gh-not-authenticated"
```

Classify the user into one of these states:

| State | Indicator | Branch to |
|---|---|---|
| **Fresh** | No `.feature-workflow.yml`, no `docs/features/` | Step 2 (concepts) → Step 3 (run init) → Step 4 (walkthrough) |
| **Initialized, empty** | `.feature-workflow.yml` exists, `docs/features/` has only DASHBOARD.md | Step 2 (quick concept recap) → Step 4 (walkthrough) |
| **In use** | `docs/features/` has real features | Step 5 (quick reference) |
| **Not a git repo** | `git rev-parse` fails | Warn: init a git repo first (`git init`), then re-run |

## Step 2: Explain the Core Concepts (only if Fresh or user asks)

Keep this to ~6 bullets. If the user says they already know, skip to Step 3.

> **The idea:** features live as directories under `docs/features/<id>/`. Status is determined by which files exist — no JSON, no state machine.
>
> - `idea.md` only → **Backlog**
> - `idea.md` + `plan.md` → **In Progress**
> - `idea.md` + `plan.md` + `shipped.md` → **Completed**
>
> A hook regenerates `docs/features/DASHBOARD.md` every time one of those files changes, so you always have a live index.
>
> **The lifecycle** is a sequence of user-invocable commands — each one writes a file, which triggers a state transition:
>
> ```
> /feature-capture   → writes idea.md  (Backlog)
> /feature-plan      → writes plan.md  (In Progress)
> /feature-review-plan  → draft PR + plan review
> /feature-implement → code the plan
> /feature-review-impl  → impl review on the same PR
> /feature-ship      → merge + writes shipped.md  (Completed)
> ```
>
> **Optional gate:** if you configure a reviewer (Gemini or Codex) in `/feature-init`, the review steps auto-run in GitHub Actions and post findings on the draft PR. Otherwise, the review is manual (you call Gemini/Codex CLI yourself, or skip the review step).

Ask: **"Make sense? Want me to explain any piece in more depth, or should we set up your project?"**

## Step 3: Run `/feature-init` Together (Fresh users)

Before invoking `/feature-init`, walk through the decisions the user will make so they aren't caught off-guard:

1. **Reviewer choice** — `gemini`, `codex`, or `none`.
   - `gemini` → needs `GOOGLE_API_KEY` (free tier available at aistudio.google.com).
   - `codex` → needs `OPENAI_API_KEY`.
   - `none` → skip CI review entirely; you can still use CLI reviewers or no review at all.
2. **Branch prefix + target** — defaults to `feature/` and `main`. Adjust if your repo uses `dev` or another convention.
3. **API key handling** — uploaded via `gh secret set`, never written to disk. Requires `gh auth status` to already be green.

If the user is ready, invoke `/feature-init` yourself via the Skill tool. Otherwise, let them run it when they have their API key handy.

After init succeeds, confirm:

```bash
git status
cat .feature-workflow.yml
ls .github/workflows/ .github/scripts/ 2>/dev/null
```

Remind the user: **commit and push the `.github/` files to your default branch** before the first PR, or the workflow won't trigger.

## Step 4: Walkthrough — Create a Demo Feature End-to-End

Ask: **"Want me to walk you through a live demo feature? I'll pick something tiny and safe — like a README typo fix or a comment cleanup — and run it through every stage so you can see each step for real."**

If yes, drive the demo. Be explicit about what each step does so the user sees the full lifecycle:

### Demo: "docs-typo-fix" (or whatever the user names it)

1. **Capture.** Run `/feature-capture`. Walk the user through the interview: pick `Bug Fix`, name it something like `docs-typo-fix`, use a tiny real problem ("README.md has a typo on line X"), priority P2, effort Small, impact Low. Show them the generated `docs/features/docs-typo-fix/idea.md`.

2. **Plan.** Run `/feature-plan docs-typo-fix`. The planning skill will ask about the change. Keep it intentionally trivial — the point is to show the lifecycle, not to produce a 500-line plan. Show the resulting `plan.md` and note that the dashboard now lists this feature under In Progress.

3. **Plan review (optional but demonstrate if CI is configured).** Run `/feature-review-plan docs-typo-fix`. This opens a draft PR with `idea.md` and `plan.md`, labeled `plan-review`. If CI is configured, watch the Actions tab — the reviewer will post inline findings within a minute or two. Then run `/feature-review-plan docs-typo-fix --respond` to show the inline-reply-and-resolve flow.

4. **Implement.** Run `/feature-implement docs-typo-fix`. For a typo fix this is one Edit call. Show the diff.

5. **Impl review (if CI is configured).** Run `/feature-review-impl docs-typo-fix`. Labels swap to `impl-review`, the workflow re-runs. Again, demonstrate `--respond` if there are findings.

6. **Ship.** Run `/feature-ship docs-typo-fix`. This runs the security + QA gates (they'll pass trivially for a typo), merges the PR, and writes `shipped.md`. Show the dashboard — the feature has moved to Completed.

After the demo, ask: **"Want to keep the demo feature in history or revert it? It's a real commit, so either way is fine."**

## Step 5: Quick Reference (already-using users)

If the user is already using the plugin and just wants a refresher, skip the walkthrough and give them:

- **Full command list**: see `feature-workflow/README.md` in the plugin, or type `/feature-status` to see current state.
- **Plugin upgrades**: after a plugin version bump, run `/feature-init --update` to refresh the CI workflow, review prompts, and `post-review.sh` in `.github/`. This doesn't touch your config, secret, or `docs/features/`.
- **Reviewer tuning**: the authoritative review prompts live at `feature-workflow/reviewers/skills/feature-review-{plan,impl}.md` in the plugin repo. Changes there sync to the CLI reviewer repos via `feature-workflow/reviewers/sync.sh`.
- **Inline responses**: `/feature-review-plan <id> --respond` and `/feature-review-impl <id> --respond` reply inline on each review thread and resolve them via GraphQL.

## Red Flags (stop and help the user)

- **`gh` not authenticated** — `/feature-init` will fail to upload the API secret. Run `gh auth login` first.
- **Not inside a git repo** — the plugin needs git for branch management. Run `git init` first.
- **Wrong default branch** — if the repo's default branch isn't `main`, tell the user to pass `--target <branch>` to `/feature-init` or edit `.feature-workflow.yml` after the fact.
- **No remote configured** — draft PRs need a GitHub remote. `git remote -v` should show an origin.
- **Branch protection with required reviews** — the bot can approve, but the user must also enable "Allow GitHub Actions reviews" in branch protection settings, or bot approvals won't count.

## Tone

Be a friendly pair programmer, not a tutorial narrator. Stop and ask questions when the user's state is ambiguous. Don't dump the whole README. When you show commands, explain *what they'll do* before running them, and pause for confirmation on anything that writes files, creates branches, or opens PRs.
