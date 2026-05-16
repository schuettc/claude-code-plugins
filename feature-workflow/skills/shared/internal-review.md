# Internal Review Workflow

Shared workflow for in-session internal review. Invoked from `feature-review-plan/SKILL.md` and `feature-review-impl/SKILL.md` when the effective review mode is `internal`.

The output of internal review is a normal PR comment using the SAME format as the external CI reviewers. From `wait-for-review.sh`'s perspective, an internal-review comment is indistinguishable from a Gemini/Codex comment. This lets the autopilot, respond loop, and verdict classifier work without modification.

## Inputs

- `<id>` — feature ID
- `<phase>` — `plan` or `impl`
- `<PR_NUMBER>` — already-opened PR

## Step 1: Load the Review Prompt

The CI reviewers use prompts at:
- `feature-workflow/templates/review-prompt-plan.md` (for plan review)
- `feature-workflow/templates/review-prompt-impl.md` (for impl review)

These are the SAME prompts the GitHub Actions workflow loads. Internal review uses them too so the verdict surface stays uniform.

Resolve the prompt path via `${CLAUDE_PLUGIN_ROOT}`:

```
${CLAUDE_PLUGIN_ROOT}/templates/review-prompt-<phase>.md
```

Read the full file content.

## Step 2: Dispatch the Reviewer Subagent

Use the Agent tool with these parameters:

- **subagent_type:** `general-purpose`
- **model:** `sonnet` (default; bump to `opus` if the feature carries `category: security` or affects auth/crypto code)
- **description:** `"Internal review: <phase> for <id>"`
- **prompt:** The full content of `review-prompt-<phase>.md` PLUS a "Working Directory" section pointing at the current checkout, the feature ID, and the PR number.

The subagent's mandate is identical to the CI reviewer's: read-only, produces the standard `## Plan Review` / `## Implementation Review` markdown with a `### Verdict: PASS|CONDITIONAL PASS|FAIL` line. **Do NOT instruct it to post; you'll post the comment yourself in Step 3.**

Capture the subagent's stdout — that's the review markdown.

## Step 3: Post the Review as a PR Comment

Post the captured markdown verbatim as a PR top-level comment:

```bash
echo "<REVIEW_MARKDOWN>" | gh pr comment <PR_NUMBER> --body-file -
```

The comment now looks exactly like a CI reviewer's comment. `wait-for-review.sh` will classify it correctly.

## Step 4: Mirror to Local Audit File

Also write the review to a local audit copy under the feature directory:

```
docs/features/<id>/reviews/internal-review-<phase>-<round>.md
```

Where `<round>` increments each time internal review runs for the same phase (e.g., round 1, 2, 3 if FAIL → respond → re-review).

Compute the round by counting existing files matching `internal-review-<phase>-*.md` and adding 1.

The audit file is just the markdown that was posted to the PR. The PR is still the source of truth — this file is for grep-able history when offline.

## Step 5: Skip CI Label Application

The label-based workflow (`plan-review` / `impl-review` labels triggering `feature-review.yml`) is for the EXTERNAL reviewer only. **Do not apply these labels in internal mode.** If the GitHub Actions workflow doesn't fire, `wait-for-review.sh` won't see a CI check failure — but it will still find the posted comment and classify the verdict.

## Step 6: Return Control to Caller

The caller (feature-review-plan/impl SKILL.md) continues as if external review had been triggered. The next step in their flow is to poll `wait-for-review.sh` for the verdict — which is already on the PR.

## Reviewer Subagent Selection

| Heuristic | Subagent |
|---|---|
| Default | `general-purpose` (sonnet) |
| Feature `category: security` | `general-purpose` (sonnet) with security-focused prompt prefix |
| Feature has dependencies on auth/crypto code | bump to `opus` |
| Plan over 500 lines | `opus` (better context handling) |

For v1, defaulting to `sonnet` is fine. The model selection logic can grow if we see internal reviews missing things the external reviewers catch.

## What This Does NOT Do

- It does NOT replace external review. Projects with `reviewer: gemini` still use Gemini for all features unless a feature has `review: internal` in its frontmatter.
- It does NOT post a status check or block merge. The PR's branch protection rules govern merge gating.
- It does NOT re-run automatically. Each phase (plan vs impl) triggers internal review once per submission; FAIL → respond cycles trigger another round, just like external.

## Failure Modes

| Failure | Handling |
|---|---|
| Subagent returns empty or malformed markdown | Surface the raw output to the user; do not post. They can re-run or switch to `review: external`. |
| `gh pr comment` fails (auth, rate limit) | Save the markdown to the local audit file anyway; surface the error so the user can manually post. |
| Verdict line missing from subagent output | `wait-for-review.sh` will exit 2 (unparseable). User can read the audit file and decide manually. |

## When NOT to Use Internal Review

- For features that touch security-critical code paths, prefer external review (an independent fresh-context reviewer with the full prompt is harder to subvert than a same-session subagent).
- For features where multiple humans need to weigh in on the plan/diff, the PR comment thread is the better venue — internal review's one-shot comment leaves less surface for discussion.
- For features where the user already trusts their own judgment and `reviewer: none` makes more sense, just set the project default to `none` instead of using internal review.
