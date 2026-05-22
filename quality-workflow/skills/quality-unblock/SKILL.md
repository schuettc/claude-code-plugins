---
name: quality-unblock
description: Triage a failing pre-commit hook (skylos or fallow). For each finding, look up the rule in the day-1 playbook and present three options — fix in code, suppress with a required # Why: justification, or defer to feature-workflow as a tech-debt epic. Use when a commit fails because of a quality hook, when the user pastes skylos/fallow output, or asks "the commit is blocked — what do I do?". Produces proposals; does NOT execute fixes itself.
user-invocable: true
allowed-tools: Read, Bash
---

# Quality Unblock

You are executing the **UNBLOCK** workflow — triage failures from skylos or fallow pre-commit hooks. Per the design (v0.2.0 MVP): you produce a **structured proposal** per finding. The user decides which proposal to apply. This skill does NOT modify code itself — the user (or a follow-up subagent dispatch) applies the chosen fix.

## Why this skill exists

When a pre-commit hook fails, three legitimate responses exist:

1. **Fix the code** — refactor to remove the underlying issue. The right answer most of the time.
2. **Suppress with a justification** — add a `# Why:` comment explaining why the finding is wrong or why the fix is worse than living with it. Legitimate for false positives, deliberately-coalesced state containers, parameterized SQL the linter mis-flags, etc.
3. **Defer to backlog** — capture the finding as a tech-debt epic via feature-workflow and ship the immediate work as-is.

The failure mode this plugin was built to prevent: agents reaching for option 2 every time because it's the cheapest path through the gate. **Suppression is a last resort.** This skill enforces that by requiring a defensible `# Why:` on every suppress action and capping suppressions per session.

## Arguments

`$ARGUMENTS` is one of:
- Empty — read the most recent pre-commit failure from the user's terminal/clipboard (the user pastes the output)
- A path to a JSON file from `skylos agent pre-commit --format json` or `fallow audit --format json`
- `--from-clipboard` — explicitly read from clipboard

## Step 1: Get the findings

If the user pasted the failure output:
1. Look for the JSON block (lines starting with `{` and a `"findings"`/`"quality"`/`"danger"` array).
2. Parse it via the appropriate adapter.

If the user said "run the hook for me":
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/skills/shared/lib')
from pathlib import Path
from skylos_adapter import run_agent_pre_commit
findings = run_agent_pre_commit(Path('.').resolve())
import json
print(json.dumps([f.to_dict() for f in findings], indent=2))
"
```

If there are no findings, tell the user the hook isn't currently failing and stop.

## Step 2: Load the playbooks

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
import sys
sys.path.insert(0, '$PLUGIN_ROOT/skills/shared/lib')
from pathlib import Path
from playbook import load_default_playbooks

pbs = load_default_playbooks(Path('$PLUGIN_ROOT'))
for tool, pb in pbs.items():
    print(f'{tool}: {len(pb.rules)} rules + fallback')
"
```

## Step 3: For each finding, propose actions

For each `QualityFinding`:

1. Look up the rule in the appropriate playbook (`skylos` or `fallow`).
2. Get the action list via `resolve_actions(playbook, finding.rule_id)`.
3. Render the finding + actions to the user. Format:

```
### Finding 1 of 3 — SKY-Q301 (HIGH severity)
File: pi/orchestrator/listener.py:45
Function: process_event
Message: Cyclomatic complexity is 17 (threshold: 10).

Action options:
[a] FIX (refactor)
    Suggestion: Extract helper functions for independent branches. Replace nested ifs with early returns.
    Agent prompt: "Refactor pi/orchestrator/listener.py:45 (process_event) to reduce cyclomatic complexity..."
[b] SUPPRESS (requires # Why:)
    Why template: "Complexity intrinsic to {what} — splitting would scatter {logic} across {N} files."
    NOTE: A vague suppression like "complexity" without a real reason will be flagged by impl-review. Write a defensible justification.
[c] DEFER (capture as tech-debt epic)
    Title: "Reduce cyclomatic complexity in pi/orchestrator/listener.py"
```

Use the action's `kind` to label `[a] FIX / [b] SUPPRESS / [c] DEFER`. If the playbook only has two actions, only show two options.

## Step 4: Wait for the user's choice per finding

After presenting all findings + options, ask the user:
> "Which option for each finding? Reply with `1a, 2c, 3b` or similar."

If they reply with a `b` (suppress), prompt for the `# Why:` text:
> "What's the justification for suppressing finding 2? (free-form text; will be added as a `# Why:` comment above the suppression directive)"

**Refuse to proceed with a bare suppression.** If the user types nothing or just `complexity`, push back:
> "That's the failure mode this plugin was built to catch. Either write a real justification (one-sentence explanation of why this finding shouldn't be silenced) or pick FIX or DEFER instead."

## Step 5: Output the proposal — do NOT execute

For each chosen action, output a structured proposal:

### For FIX actions:

```markdown
## Proposal — Finding 1 (FIX)
File: pi/orchestrator/listener.py:45
Refactor target: process_event
Suggested approach: Extract helper functions for independent branches.

To apply: dispatch a subagent with this prompt:
> Refactor pi/orchestrator/listener.py:45 (process_event) to reduce cyclomatic
> complexity. Extract helpers for independent branches; flatten guards with
> early returns; preserve behavior. Run the test suite.
```

### For SUPPRESS actions:

```markdown
## Proposal — Finding 2 (SUPPRESS)
File: pi/orchestrator/state.py:7
Insert above the line:
```python
# Why: State is intentionally one container — splitting scatters mutations
# across the codebase for no maintainability gain.
# skylos: ignore SKY-Q501
```

To apply: edit the file at the indicated line.
```

### For DEFER actions:

```markdown
## Proposal — Finding 3 (DEFER)
Capture as a tech-debt epic via `/feature-workflow:feature-capture`:
- Title: Reduce cyclomatic complexity in pi/orchestrator/listener.py
- Type: Tech Debt
- Category: tech-debt
- Body: includes finding details + suggested approach

To apply: invoke `/feature-workflow:feature-capture` with the above.
```

**Do not edit any files in this skill.** The skill ends with proposals on the screen. The user (or autopilot) applies them in a separate step.

## Step 6: Suppression budget warning

After all proposals are rendered, check how many were `SUPPRESS`. If more than 2:

```
⚠️ You're proposing 4 new suppressions in this triage. The plugin's pre-
commit-compat policy caps suppressions at 2 per PR — the autopilot's
impl-review prompt will flag this as a Critical Finding.

Either pick FIX for some of them, or split the work across multiple PRs.
See pre-commit-compat.md for the suppression-discipline rules.
```

This mirrors the impl-review prompt enforcement in feature-workflow v9.8.1.

## When NOT to use this skill

- For hook verification (testing whether the hook fires correctly) → use `/quality-verify-hook`
- For a full project audit (not triggered by a hook failure) → use `/quality-audit`
- For programmatic batch processing (e.g., a CI script) → use the lib directly: `from skylos_adapter import run_agent_pre_commit; ...`

## Notes

- This skill is **stateless** between invocations. Each triage is independent.
- The playbooks at `${CLAUDE_PLUGIN_ROOT}/playbooks/` ship day-1 coverage for ~25 rule_ids across skylos and fallow. Unknown rules fall through to a fallback action set.
- The skill cannot enforce that the user actually applies a chosen action — it only produces proposals. Pair it with autopilot for end-to-end automation.
