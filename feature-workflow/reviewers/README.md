# Reviewer Skills

Authoritative source for the Gemini and Codex PR review prompts used by the feature-workflow plugin. Everything here feeds two downstream consumers:

1. **CI mode** (GitHub Actions) — the plugin's `templates/review-prompt-{plan,impl}.md` files are derived from the skills here and copied into user projects by `/feature-init`. These are what `google-github-actions/run-gemini-cli` or `openai/codex-action` execute.
2. **CLI mode** (manual terminal invocation) — the separate [`gemini-reviewer`](https://github.com/schuettc/gemini-reviewer) and [`codex-reviewer`](https://github.com/schuettc/codex-reviewer) plugin repos get their `SKILL.md` files from `sync.sh` in this directory. Those skills add a human-approval gate before any `gh` command runs.

## Files

| File | Purpose |
|---|---|
| `skills/feature-review-plan.md` | Authoritative plan review prompt (reviewer-agnostic) |
| `skills/feature-review-impl.md` | Authoritative implementation review prompt (reviewer-agnostic) |
| `sync.sh` | Mirrors skills to the CLI reviewer repos, injecting the approval-gate mandate |

## When to edit what

- **Changing review logic** (findings structure, signal-over-noise guidance, verdict handling): edit `skills/feature-review-{plan,impl}.md`. That file is the single source of truth.
- **Changing the CI prompt only** (env-var handling, CI-specific posting instructions): edit `../templates/review-prompt-{plan,impl}.md` directly. These are not auto-regenerated — they're hand-maintained derivatives that strip the CLI approval gate and fill in CI-specific Step 1 behavior.
- **Changing the CLI approval-gate copy**: edit the `CLI_APPROVAL_MANDATE` / `CLI_APPROVAL_STEP` constants at the top of `sync.sh`.

## Sync to CLI reviewer repos

```bash
./feature-workflow/reviewers/sync.sh
```

Expects sibling checkouts:
- `../gemini-reviewer` — writes flat `<skill>/SKILL.md`
- `../codex-reviewer` — writes nested `skills/<skill>/SKILL.md`

Override the paths by setting `GEMINI_REPO=...` or `CODEX_REPO=...` before invoking.

After it finishes:

```bash
cd ../gemini-reviewer && git diff && git add . && git commit -m "..." && git push
cd ../codex-reviewer  && git diff && git add . && git commit -m "..." && git push
```

The CLI reviewer repos are separate marketplaces — users installing them pull directly from those repos, so pushing is the publish step.

## Update flow end-to-end

When you change a review prompt:

1. Edit `skills/feature-review-{plan,impl}.md` here.
2. If the change also applies to the CI variant, edit the matching `../templates/review-prompt-*.md` too (or copy-paste the new section in).
3. Bump `../.claude-plugin/plugin.json` version.
4. Commit + push this repo, merge to `main`.
5. Run `./sync.sh`, commit + push the two CLI reviewer repos.
6. Existing user projects:
   - CI mode users run `/feature-init --update` to refresh their `.github/review-prompt-*.md` + workflow.
   - CLI mode users get updates automatically when their plugin marketplace refreshes.
