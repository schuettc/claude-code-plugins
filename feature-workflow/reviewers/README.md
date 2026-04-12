# Reviewer Skills

Authoritative source for Gemini and Codex reviewer skill content.

## Files

- `skills/feature-review-plan.md` — plan review prompt (reviewer-agnostic)
- `skills/feature-review-impl.md` — implementation review prompt (reviewer-agnostic)
- `sync.sh` — syncs skills to external reviewer repos

## Sync

```bash
./feature-workflow/reviewers/sync.sh
```

Writes to:
- `../gemini-reviewer/feature-review-plan/SKILL.md` (flat root layout)
- `../gemini-reviewer/feature-review-impl/SKILL.md`
- `../codex-reviewer/skills/feature-review-plan/SKILL.md` (nested layout)
- `../codex-reviewer/skills/feature-review-impl/SKILL.md`

After syncing, review diffs and commit/push each repo.

## CI vs CLI

The skills here are the **CI version** (auto-post, verdict maps to approve/comment/request-changes).

The sync script writes them directly. For CLI usage (manual invocation in Gemini/Codex terminals), the CLI skills in the external repos may retain an approval gate — but that's managed by editing those repos directly if needed.
