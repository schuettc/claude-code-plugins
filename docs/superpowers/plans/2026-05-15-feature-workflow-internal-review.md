# Feature-Workflow Internal Review Implementation Plan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow per-feature opt-out from the configured external CI reviewer in favor of an in-session internal review pass, while preserving the same review-comment surface so `wait-for-review.sh`, the respond flow, and autopilot keep working unchanged.

**Architecture:** The internal review path piggy-backs on the **existing** review-comment format. A subagent dispatched in-session loads the same `templates/review-prompt-{plan,impl}.md` content as the CI reviewer, reads the plan/diff, and produces a `## Plan Review` / `## Implementation Review` markdown block with a `### Verdict:` line. The orchestrator posts that block to the PR as a normal comment via `gh pr comment`. From `wait-for-review.sh`'s perspective, an internal-review comment looks identical to a CI-review comment — same classification, same auto-respond loop, same UI in the PR thread.

**Tech Stack:** Python 3 (stdlib), pytest, markdown skill files. Builds on Plan 1's `ctx.review` field and `models.py` shape.

**Spec:** `docs/superpowers/specs/2026-05-15-feature-workflow-foundations-design.md` (§5 Internal Review)

**Precondition:** Plan 1 (`feature/foundations-v9.6.0` branch / PR #5) must be merged first. This plan references `ctx.review` and other fields Plan 1 introduces.

**Version target:** `9.7.0` (because origin/main already has a different `9.6.0` — see Plan 4 for version reconciliation).

---

## File Structure

### Modified files
- `feature-workflow/skills/feature-review-plan/SKILL.md` — branch on effective review setting (external/internal/skip)
- `feature-workflow/skills/feature-review-impl/SKILL.md` — same branch
- `feature-workflow/skills/feature-review-plan/submit.md` — internal-mode path skips CI label, runs subagent, posts comment
- `feature-workflow/skills/feature-review-impl/submit.md` — same
- `feature-workflow/skills/feature-autopilot/SKILL.md` — reviewer-mode table grows a row for `internal`
- `feature-workflow/skills/shared/lib/models.py` — `FeatureContext.effective_review(project_default)` helper
- `feature-workflow/skills/shared/tests/test_models.py` — tests for `effective_review`
- `feature-workflow/.claude-plugin/plugin.json` — version 9.7.0
- `.claude-plugin/marketplace.json` — version 9.7.0
- `feature-workflow/README.md` — document the `review:` per-feature override

### New files
- `feature-workflow/skills/shared/internal-review.md` — shared internal-review workflow (invoked from both review-plan and review-impl)
- `feature-workflow/skills/shared/lib/effective_review.py` — pure helper to compute effective review setting from feature + project config
- `feature-workflow/skills/shared/tests/test_effective_review.py` — tests for the helper

### Files NOT created (intentional)
- **No separate `/feature-review-internal` slash command.** Internal review is a *mode* of the existing review skills, not a new command. Users still type `/feature-review-plan <id>` and `/feature-review-impl <id>`; the skill detects the `review:` field and routes accordingly.
- **No `--internal` flag on `wait-for-review.sh`.** Internal-review comments use the same `## Plan Review` / `## Implementation Review` headers and `### Verdict:` lines; the existing classifier handles both without modification.

### Out of scope (Plan 3)
- Epic concept + dispatch (Plan 3)
- Autopilot worktree + subagent guidance for epics (Plan 3)

---

## Phase A: Effective Review Helper

Pure logic for "given a feature's `review:` field and the project's `reviewer:` setting, which review path should run?" Test-first.

### Task A1: effective_review pure function

**Files:**
- Create: `feature-workflow/skills/shared/lib/effective_review.py`
- Create: `feature-workflow/skills/shared/tests/test_effective_review.py`

- [ ] **Step 1: Write the failing test**

Create `feature-workflow/skills/shared/tests/test_effective_review.py`:

```python
"""Tests for effective_review resolution."""

import sys
from pathlib import Path

# Path setup
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import pytest
from effective_review import resolve_review, ReviewMode


class TestResolveReview:
    """Per-feature override beats project default; if both absent, return SKIP."""

    def test_feature_external_wins(self):
        assert resolve_review(feature_review="external", project_reviewer="none") == ReviewMode.EXTERNAL_DEFAULT
        # With project reviewer=none and feature override=external, we still
        # try external — though it has no concrete reviewer to dispatch to,
        # so the caller surfaces a usage error. The mode is EXTERNAL.

    def test_feature_internal_wins(self):
        assert resolve_review(feature_review="internal", project_reviewer="gemini") == ReviewMode.INTERNAL

    def test_feature_skip_wins(self):
        assert resolve_review(feature_review="skip", project_reviewer="gemini") == ReviewMode.SKIP

    def test_empty_feature_falls_back_to_project_gemini(self):
        assert resolve_review(feature_review="", project_reviewer="gemini") == ReviewMode.EXTERNAL_GEMINI

    def test_empty_feature_falls_back_to_project_codex(self):
        assert resolve_review(feature_review="", project_reviewer="codex") == ReviewMode.EXTERNAL_CODEX

    def test_both_absent_means_skip(self):
        assert resolve_review(feature_review="", project_reviewer="none") == ReviewMode.SKIP
        assert resolve_review(feature_review="", project_reviewer="") == ReviewMode.SKIP

    def test_unknown_feature_value_falls_back_with_warning(self, capsys):
        result = resolve_review(feature_review="garbled", project_reviewer="gemini")
        assert result == ReviewMode.EXTERNAL_GEMINI
        captured = capsys.readouterr()
        assert "garbled" in captured.err

    def test_external_mode_value(self):
        """The EXTERNAL_DEFAULT mode encodes 'use whatever project says (or refuse if project=none)'."""
        # Just verify the enum has the values we depend on:
        assert ReviewMode.INTERNAL.value == "internal"
        assert ReviewMode.SKIP.value == "skip"
        assert ReviewMode.EXTERNAL_GEMINI.value == "external_gemini"
        assert ReviewMode.EXTERNAL_CODEX.value == "external_codex"
        assert ReviewMode.EXTERNAL_DEFAULT.value == "external_default"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd feature-workflow && venv/bin/pytest skills/shared/tests/test_effective_review.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'effective_review'`

- [ ] **Step 3: Implement effective_review.py**

Create `feature-workflow/skills/shared/lib/effective_review.py`:

```python
"""Resolve the effective review mode for a feature.

Pure function. No I/O. The caller is responsible for reading the project's
.feature-workflow.yml and the feature's idea.md.

Precedence:
    1. Feature's `review:` frontmatter field (if set and recognized)
    2. Project's `reviewer:` config in .feature-workflow.yml
    3. SKIP (no review at all)
"""

import sys
from enum import Enum
from typing import Optional


class ReviewMode(Enum):
    """The concrete reviewer to invoke for this feature/phase."""

    EXTERNAL_GEMINI = "external_gemini"
    EXTERNAL_CODEX = "external_codex"
    EXTERNAL_DEFAULT = "external_default"  # feature says "external" but project hasn't picked one
    INTERNAL = "internal"
    SKIP = "skip"


_RECOGNIZED_FEATURE_VALUES = {"external", "internal", "skip"}
_RECOGNIZED_PROJECT_VALUES = {"gemini", "codex", "none", ""}


def resolve_review(feature_review: Optional[str], project_reviewer: Optional[str]) -> ReviewMode:
    """Compute the effective review mode."""
    f = (feature_review or "").strip().lower()
    p = (project_reviewer or "").strip().lower()

    # Feature override path
    if f and f in _RECOGNIZED_FEATURE_VALUES:
        if f == "internal":
            return ReviewMode.INTERNAL
        if f == "skip":
            return ReviewMode.SKIP
        if f == "external":
            # Delegate to project's choice
            if p == "gemini":
                return ReviewMode.EXTERNAL_GEMINI
            if p == "codex":
                return ReviewMode.EXTERNAL_CODEX
            # Feature requested external but project has no reviewer configured —
            # signal this to the caller; they'll need to error out usefully.
            return ReviewMode.EXTERNAL_DEFAULT

    # Unknown feature value — warn and fall through to project default
    if f and f not in _RECOGNIZED_FEATURE_VALUES:
        print(f"[effective_review] Unknown feature review value '{feature_review}', falling back to project default", file=sys.stderr)

    # Project default path
    if p == "gemini":
        return ReviewMode.EXTERNAL_GEMINI
    if p == "codex":
        return ReviewMode.EXTERNAL_CODEX

    # No reviewer at any level
    return ReviewMode.SKIP
```

- [ ] **Step 4: Run tests**

Run: `cd feature-workflow && venv/bin/pytest skills/shared/tests/test_effective_review.py -v`

Expected: PASS for all 8 tests.

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/effective_review.py feature-workflow/skills/shared/tests/test_effective_review.py
git commit -m "feat(review): add resolve_review helper for per-feature review precedence"
```

---

### Task A2: FeatureContext.effective_review() method

**Files:**
- Modify: `feature-workflow/skills/shared/lib/models.py`
- Modify: `feature-workflow/skills/shared/tests/test_models.py`

Convenience method so callers don't have to thread the project_reviewer through everywhere.

- [ ] **Step 1: Write the failing test**

Append to `feature-workflow/skills/shared/tests/test_models.py` inside `TestFeatureContext`:

```python
    def test_effective_review_feature_override(self, feature_with_epic_and_relations: Path):
        """A1 fixture has review: internal in frontmatter."""
        from effective_review import ReviewMode
        ctx = FeatureContext.from_directory(feature_with_epic_and_relations)
        assert ctx.effective_review(project_reviewer="gemini") == ReviewMode.INTERNAL

    def test_effective_review_falls_back_to_project(self, feature_in_backlog: Path):
        """Default fixture has no review field; should defer to project."""
        from effective_review import ReviewMode
        ctx = FeatureContext.from_directory(feature_in_backlog)
        assert ctx.effective_review(project_reviewer="gemini") == ReviewMode.EXTERNAL_GEMINI

    def test_effective_review_both_absent_is_skip(self, feature_in_backlog: Path):
        from effective_review import ReviewMode
        ctx = FeatureContext.from_directory(feature_in_backlog)
        assert ctx.effective_review(project_reviewer="none") == ReviewMode.SKIP
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd feature-workflow && venv/bin/pytest skills/shared/tests/test_models.py -v -k effective_review`

Expected: FAIL — `'FeatureContext' object has no attribute 'effective_review'`

- [ ] **Step 3: Add effective_review method to FeatureContext**

In `feature-workflow/skills/shared/lib/models.py`, add the import at the top (alongside the existing `from .frontmatter` block):

```python
# Handle both package and standalone imports
try:
    from .effective_review import resolve_review, ReviewMode
except ImportError:
    from effective_review import resolve_review, ReviewMode
```

Then add the method to the `FeatureContext` dataclass (place near `is_active()` / `is_epic()`):

```python
    def effective_review(self, project_reviewer: str) -> "ReviewMode":
        """Compute the effective review mode for this feature.

        Combines the per-feature `review:` override with the project's `reviewer:`
        config to decide which review path runs.
        """
        return resolve_review(self.review, project_reviewer)
```

- [ ] **Step 4: Run tests**

Run: `cd feature-workflow && venv/bin/pytest skills/shared/tests/test_models.py -v -k effective_review`

Expected: PASS for all 3 tests.

- [ ] **Step 5: Commit**

```bash
git add feature-workflow/skills/shared/lib/models.py feature-workflow/skills/shared/tests/test_models.py
git commit -m "feat(models): add FeatureContext.effective_review convenience method"
```

---

## Phase B: Internal Review Workflow Doc

The shared workflow document that both `feature-review-plan` and `feature-review-impl` reference when the effective mode is `internal`.

### Task B1: shared/internal-review.md

**Files:**
- Create: `feature-workflow/skills/shared/internal-review.md`

This is a markdown procedure document — no Python tests. Manual verification only.

- [ ] **Step 1: Write internal-review.md**

Create `feature-workflow/skills/shared/internal-review.md`:

```markdown
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
```

- [ ] **Step 2: Manual verification**

Read the file end-to-end and confirm:
- The 6 steps form a complete workflow
- Step 3's comment format matches what `wait-for-review.sh` expects (`## Plan Review` / `## Implementation Review` headers, `### Verdict:` line)
- The audit file naming pattern matches what implementation tasks (Phase C) reference

- [ ] **Step 3: Commit**

```bash
git add feature-workflow/skills/shared/internal-review.md
git commit -m "feat(review): add shared internal-review workflow doc"
```

---

## Phase C: Wire Internal Review Into review-plan / review-impl

The existing skills already detect the `--respond` flag for response mode. We add a second branch: detect effective review mode, route to internal-review.md when `internal`.

### Task C1: feature-review-plan branches on effective mode

**Files:**
- Modify: `feature-workflow/skills/feature-review-plan/SKILL.md`
- Modify: `feature-workflow/skills/feature-review-plan/submit.md`

- [ ] **Step 1: Update SKILL.md mode detection**

In `feature-workflow/skills/feature-review-plan/SKILL.md`, find the "Mode Detection" section (currently a 2-row table). Replace it with:

```markdown
## Mode Detection

| Arguments | Mode | Skill File |
|-----------|------|------------|
| `<id>` (effective: external) | Submit plan for external CI review | [submit.md](submit.md) |
| `<id>` (effective: internal) | Submit plan for internal review | [submit.md](submit.md) (branches internally) |
| `<id>` (effective: skip) | Refuse — review opted out | (stop, surface to user) |
| `<id> --respond` | Respond to feedback (works for any mode) | [../shared/respond.md](../shared/respond.md) |

## Step 0: Determine Effective Review Mode

Before routing, compute the effective review mode for this feature:

1. Read `.feature-workflow.yml` for `reviewer:` (defaults to none if absent).
2. Read `docs/features/<id>/idea.md` frontmatter for `review:`.
3. Compute the mode using `feature-workflow/skills/shared/lib/effective_review.py`:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/skills/shared/lib')
from effective_review import resolve_review
# parse project_reviewer from .feature-workflow.yml
# parse feature_review from idea.md frontmatter
mode = resolve_review(feature_review='<value>', project_reviewer='<value>')
print(mode.value)
"
```

Or simpler: read both values yourself and apply the precedence rule (feature override wins, else project default, else skip).

| Mode | Behavior |
|---|---|
| `external_gemini` / `external_codex` / `external_default` | Original flow — open PR, apply `plan-review` label, let CI run |
| `internal` | Open PR, then dispatch the internal-review subagent (see `../shared/internal-review.md`) |
| `skip` | Don't run any review; just open the PR if not present, and surface to the user that they've opted out of review |
```

- [ ] **Step 2: Update submit.md with the mode branch**

In `feature-workflow/skills/feature-review-plan/submit.md`, find Step 4 (or wherever the label is applied — search for `plan-review` label). Insert a mode check BEFORE the label-application step:

```markdown
## Step 3.5: Branch by Effective Review Mode

You have the effective review mode from Step 0 of SKILL.md. Branch:

**external_gemini / external_codex / external_default:**
Continue to Step 4 (apply `plan-review` label).

**internal:**
Skip Step 4 entirely. Follow `${CLAUDE_PLUGIN_ROOT}/skills/shared/internal-review.md` to dispatch the subagent and post the review comment. Then continue to Step 5 (success message).

**skip:**
Print: "`<id>` is configured for `review: skip`. No review will be performed for this submission. Continue with `/feature-implement <id>` when ready." Stop here.
```

- [ ] **Step 3: Manual verification**

Walk through the SKILL.md mentally for each mode:
- `external_gemini` + no respond flag → opens PR, applies label, CI runs. (Unchanged from today.)
- `internal` + no respond flag → opens PR, dispatches subagent, posts comment. No label.
- `skip` + no respond flag → opens PR (or not?), no review. **Decision:** still open the PR (audit trail), just don't run any review.

For `--respond` flag: the existing flow works regardless of mode because respond.md just reads PR comments and posts replies — it doesn't care who wrote the comments.

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/feature-review-plan/SKILL.md feature-workflow/skills/feature-review-plan/submit.md
git commit -m "feat(review-plan): branch on effective review mode (external/internal/skip)"
```

---

### Task C2: feature-review-impl branches on effective mode

**Files:**
- Modify: `feature-workflow/skills/feature-review-impl/SKILL.md`
- Modify: `feature-workflow/skills/feature-review-impl/submit.md`

Apply the same branching pattern. The difference: `feature-review-impl` swaps the label from `plan-review` to `impl-review` for external mode. Internal mode skips the label entirely (same as C1).

- [ ] **Step 1: Update SKILL.md mode detection**

Mirror the Step 0 + Mode Detection table changes from C1 onto `feature-workflow/skills/feature-review-impl/SKILL.md`. Use the same template — only "plan" becomes "impl" in the user-facing text.

- [ ] **Step 2: Update submit.md with the mode branch**

In `feature-workflow/skills/feature-review-impl/submit.md`, find the label-swap step (search for `--remove-label plan-review --add-label impl-review`). Add Step 3.5 before it:

```markdown
## Step 3.5: Branch by Effective Review Mode

You have the effective review mode from Step 0 of SKILL.md. Branch:

**external_gemini / external_codex / external_default:**
Continue to Step 4 (swap labels: remove `plan-review`, add `impl-review`).

**internal:**
Skip the label swap. If `plan-review` is still on the PR, remove it (no replacement). Then follow `${CLAUDE_PLUGIN_ROOT}/skills/shared/internal-review.md` to dispatch the subagent and post the impl review comment. Continue to Step 5.

**skip:**
Print: "`<id>` is configured for `review: skip`. Implementation review will not be performed." Stop here.
```

- [ ] **Step 3: Manual verification**

Walk through each mode again, this time for impl phase. Confirm the label state is correct after each path:
- external: PR has `impl-review` label, CI fires
- internal: PR has no review label, subagent posts the comment
- skip: PR has no review label, no comment, no further action

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/feature-review-impl/SKILL.md feature-workflow/skills/feature-review-impl/submit.md
git commit -m "feat(review-impl): branch on effective review mode (external/internal/skip)"
```

---

### Task C3: Autopilot honors effective review mode

**Files:**
- Modify: `feature-workflow/skills/feature-autopilot/SKILL.md`

- [ ] **Step 1: Update reviewer-mode table**

In `feature-workflow/skills/feature-autopilot/SKILL.md`, find the existing "Reviewer-mode adaptations" table (currently has rows for gemini / codex / none). Replace with:

```markdown
## Reviewer-mode adaptations

The autopilot's behavior at each review gate is driven by the **effective** review mode for the feature being processed:

| Effective mode | Step 2 (plan review) | Step 4 (impl review) |
|---|---|---|
| `external_gemini` / `external_codex` | Active — apply label, wait-for-review polls CI | Active — same |
| `external_default` (feature says external, project says none) | **Error** — surface to user; can't dispatch without a configured reviewer | Same — error |
| `internal` | Dispatch internal-review subagent → post comment → wait-for-review polls comments | Same — post impl-review comment, same poll |
| `skip` | Skip review gate entirely; advance to implement | Skip; advance to ship |

The effective mode is computed per-feature using:
- Project default from `.feature-workflow.yml` (`reviewer:` setting)
- Per-feature override from `idea.md` frontmatter (`review:` field)

See `feature-workflow/skills/shared/lib/effective_review.py` for precedence rules.

**Important:** `wait-for-review.sh` works identically across external and internal modes. Internal-review comments use the same `## Plan Review` / `## Implementation Review` headers and `### Verdict:` line that the external CI reviewer posts. No special flag is needed.

For `internal` mode, the autopilot's FAIL → respond loop also works unchanged: the respond flow reads PR comments, classifies findings, replies, and pushes — exactly as for external review. The subagent re-runs on the next round because the orchestrator detects the new commits and dispatches it again.
```

- [ ] **Step 2: Update the "When NOT to use" section**

Find the "When NOT to use" section at the top of the SKILL.md. Add a bullet:

```markdown
- The user wants a different review path than what's configured — set `review:` in the feature's `idea.md` frontmatter BEFORE running autopilot (see `feature-workflow/skills/feature-state/SKILL.md` is for state, but the `review:` field can be edited directly).
```

- [ ] **Step 3: Manual verification**

Read the autopilot SKILL.md end-to-end. Confirm:
- The reviewer-mode table includes all 4 effective modes
- The FAIL → respond loop is described as working for all modes
- No new flag is needed in autopilot — it just reads the effective mode and routes

- [ ] **Step 4: Commit**

```bash
git add feature-workflow/skills/feature-autopilot/SKILL.md
git commit -m "feat(autopilot): honor effective review mode (external/internal/skip) per-feature"
```

---

## Phase D: Polish

### Task D1: Update README

**Files:**
- Modify: `feature-workflow/README.md`

- [ ] **Step 1: Add Review Overrides section**

Edit `feature-workflow/README.md`. After the existing "Feature States and Relations" section (added in Plan 1), add a new "Per-Feature Review Override" section:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add feature-workflow/README.md
git commit -m "docs(README): document per-feature review override (external/internal/skip)"
```

---

### Task D2: Version bump 9.6.0 → 9.7.0

**Files:**
- Modify: `feature-workflow/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

This plan ships after Plan 1's PR is merged. Plan 1 (foundations) needs to bump to 9.7.0 during its own rebase (see Plan 4). When Plan 2 lands, it bumps to 9.7.0 as well — but Plan 2 will already be on a branch from a post-9.7.0 main. So this version bump is just confirming the manifests are consistent.

- [ ] **Step 1: Verify current version**

Check both files. They should already say `9.7.0` if Plan 1 landed correctly. If for some reason they still say `9.6.0` or `9.6.x`, bump them.

- [ ] **Step 2: Run the full test suite**

```bash
cd feature-workflow && venv/bin/pytest skills/shared/tests/ 2>&1 | tail -5
```

Expected: 148 + new tests from Phase A pass.

- [ ] **Step 3: Commit (only if a bump was needed)**

```bash
git add feature-workflow/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: confirm feature-workflow at v9.7.0 (internal review path)"
```

If the manifests already said 9.7.0 from Plan 1, skip this commit.

---

### Task D3: Smoke test — internal review end-to-end

**Files:** none (verification only)

After all commits, run a manual end-to-end test in a sandbox project.

- [ ] **Step 1: Set up sandbox**

```bash
mkdir -p /tmp/internal-review-test
cd /tmp/internal-review-test
git init
# Pretend feature-workflow is installed; reference the local checkout
echo 'branch:
  prefix: "feature/"
  target: "main"
reviewer: "gemini"' > .feature-workflow.yml
mkdir -p docs/features/test-feature
cat > docs/features/test-feature/idea.md <<'EOF'
---
id: test-feature
name: Test Feature
type: Enhancement
priority: P2
effort: Small
impact: Low
review: internal
created: 2026-05-15
---

# Test Feature
Verify the internal review path.
EOF
```

- [ ] **Step 2: Compute effective mode**

```bash
python3 -c "
import sys
sys.path.insert(0, '/Users/courtschuett/GitHub/schuettc/claude-code-plugins/feature-workflow/skills/shared/lib')
from effective_review import resolve_review
print(resolve_review(feature_review='internal', project_reviewer='gemini').value)
"
```

Expected: `internal`

- [ ] **Step 3: Verify the SKILL.md docs are coherent**

Re-read both `feature-workflow/skills/feature-review-plan/SKILL.md` and `submit.md`, plus `shared/internal-review.md`. Confirm a reader could execute the internal path without getting stuck.

- [ ] **Step 4: No commit**

This is verification only.

---

## Self-Review Checklist

After completing all tasks:

1. **Spec coverage** — §5 of the design doc is fully covered. The deliberate design simplification (PR comment instead of separate verdict file) is documented in this plan.

2. **Type consistency:**
   - `ReviewMode` enum: same values everywhere (`external_gemini`, `external_codex`, `external_default`, `internal`, `skip`)
   - `resolve_review(feature_review, project_reviewer)` signature: same in helper, test, models.py method
   - `FeatureContext.effective_review(project_reviewer)` returns `ReviewMode`

3. **Backward compatibility:**
   - Features without `review:` field → defer to project default → identical to today's behavior
   - Projects with `reviewer: gemini` and features without `review:` field → exact same flow as Plan 1
   - The only changed behavior is for features that explicitly opt in via `review: internal` or `review: skip`

4. **Surface area changes:**
   - No new slash commands
   - No new flags on existing commands
   - One new shared lib helper, one new shared workflow doc, four modified skill files

5. **Test counts (expected):**
   - 11 new tests in test_effective_review.py
   - 3 new tests in test_models.py for effective_review method
   - Total new: 14 tests
   - Plan 1 + Plan 2 cumulative: ~162 tests

---

## Execution Note

Like Plan 1, this is meant for `superpowers:subagent-driven-development` execution. Each task is bite-sized. The phases are dependent: A → B → C → D.

**Precondition for execution:** Plan 1 must be merged to main first. The `ctx.review` field, `feature_with_epic_and_relations` fixture (which has `review: internal`), and Plan 1's models.py changes are all referenced.

After Plan 2 ships, Plan 3 (Epic Dispatch) gets written against the updated codebase.
