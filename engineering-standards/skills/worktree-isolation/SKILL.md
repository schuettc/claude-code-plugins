---
name: worktree-isolation
description: Use when about to make code changes while other work is in flight, when working in a repo's primary clone with live git worktrees, when starting a parallel line of work, or when dispatching agents that write to the tree. The rule — the primary clone is a coordination point, not a workspace; isolate every line of work (yours and agents') in its own git worktree so parallel lines never collide in one tree.
---

# Worktree isolation

## The rule

**The primary clone is a coordination point, not a workspace.** Every distinct line of work — a feature, a fix, a "quick change," an agent's task — runs in its **own git worktree on its own branch**. Two lines of work never share one checked-out tree.

This is non-negotiable when *any* parallel work is live: an autopilot running, another Claude session open, a long task mid-flight. The moment two actors touch one tree on different branches, you get clobbered uncommitted changes, "branch already checked out" errors, and "wait, what branch am I even on" — the classic shared-tree collision.

## Why

**Real incident (`now-playing`, 2026-05-16):** Feature B's uncommitted implementation was overlaid when Feature C's branch was checked out in the *same* tree. The autopilot already isolates its subagents (see `feature-workflow`), so the collision came from the **other** direction — a human/main-session "quick change" made directly in the primary clone while parallel work was live, because editing the shared tree was the path of least resistance. Under time pressure the *easy* path won, and git state got confused.

The fix is structural, not willpower: make isolation the easy path, so "just make the change" lands in a worktree instead of the shared tree.

## How to apply (this is guidance for *you*, the agent)

When the user asks for a change and there is — or might be — parallel work live, **don't edit the primary clone.** Isolate first:

1. **Check where you are.** If the repo has linked worktrees (`git worktree list` shows more than one) and you're in the primary clone, you're on the shared tree. (In a tmux setup the status bar flags this as `⚠ primary`.)
2. **Isolate the work** by the cheapest sufficient means:
   - **Dispatch an `isolation: "worktree"` subagent** (the Agent tool) to do the change — the harness gives it a clean worktree. Best for a self-contained task.
   - **Or create a worktree and work there:** `git worktree add .worktrees/<branch> -b <branch> <base>` (base off `dev` if it exists), then operate inside it. Best when you'll iterate interactively.
   - Use **worktree-relative paths**; never reconstruct primary-clone absolute paths inside a worktree (that's how agents drift back out and re-collide).
3. **Only edit the primary clone directly** when nothing else is live and the change is on the clone's own checked-out branch (e.g. a `dev` doc tweak you're about to commit immediately).

## Starting parallel work

To open a *new* parallel line of work, start it isolated from the beginning:

- **Native:** `claude -w <name>` launches Claude in its own worktree (`.claude/worktrees/<name>`). This is the built-in primitive — reach for it instead of opening a second session in the same tree.
- **Worktree-aware launcher (optional accelerator):** a launcher like the `proj` function in the operator's dotfiles makes "pick a branch → land in its worktree" one step — the default branch routes to the home-base/primary clone (read & coordinate), any other branch transparently gets a worktree. If such a launcher exists, prefer it.
- **`.worktreeinclude`** (gitignore syntax) lists gitignored files (e.g. `.env`) to copy into each new worktree; add `.claude/worktrees/` and `.worktrees/` to ignore rules.

## Knowing where you are

A worktree's git-dir path contains `/worktrees/`; the primary clone's does not — that's the reliable "am I isolated?" check. In a tmux status bar, surface the branch per pane and a `⚠ primary` marker when a pane sits in the primary clone with worktrees live, so the shared tree is visually obvious.

## Escalation — when isolation must be a hard guarantee

Worktrees + this discipline are a *soft* boundary: an agent can still drift back into the primary clone via absolute paths, and enforcement hooks have documented bypass paths. If you're running unattended fleets or `--dangerously-skip-permissions` and escape *must* be impossible, the real boundary is a **per-agent devcontainer** (filesystem-isolated, default-deny egress), not a hook. Reach for that only when the stakes require it — for interactive day-to-day parallel work, worktree-per-line-of-work is the right level.

## Related

- `feature-workflow` autopilot — already dispatches every write/git subagent with `isolation: "worktree"` (no opt-out). This skill covers the *other* paths (your ad-hoc changes, parallel sessions) that autopilot can't.
- `branch-promotion-model` — feature branches (the things you isolate) flow `feat → dev → main`.
