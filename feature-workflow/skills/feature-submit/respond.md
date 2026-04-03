# Respond Mode

Read external review feedback, validate findings, implement fixes, and prepare for the next round.

## Step 1: Determine Current Round

Count `context-round-*.md` files in `docs/features/<id>/reviews/` to determine the current round number N.

## Step 2: Collect Review Feedback

Scan `docs/features/<id>/reviews/` for all review files matching the current round:

- `gemini-review-round-N.md`
- `codex-review-round-N.md`
- Any other `*-review-round-N.md` files

Read each file that exists. If no review files are found for round N, inform the user:
**"No review feedback found for round N. Reviewers may not have completed their reviews yet."**

## Step 3: Synthesize Findings

Create a consolidated list of all findings across reviewers. For each finding:

1. **Source**: Which reviewer raised it
2. **Severity**: Critical / High / Medium / Low (use the reviewer's assessment)
3. **Summary**: What the issue is
4. **Location**: File/line if specified
5. **Agreement**: Do multiple reviewers flag the same thing?

Group findings by severity, with cross-reviewer agreements highlighted.

## Step 4: Present to User

Display the consolidated findings:

```
## Review Feedback Summary (Round N)

### Reviewers
- Gemini: [verdict if provided]
- Codex: [verdict if provided]

### Critical/High Findings
1. [Finding] — raised by [reviewer(s)]
2. ...

### Medium Findings
1. ...

### Low/Recommendations
1. ...

### Cross-Reviewer Agreement
- [Findings flagged by multiple reviewers — these deserve extra attention]
```

Ask the user: **"Which findings should we address? Any you want to discuss or disagree with?"**

## Step 5: Classify Findings

Based on the user's input, classify each finding:

| Classification | Action |
|----------------|--------|
| **Agree** | Will implement the fix |
| **Disagree** | Document reasoning — will note in next round's context |
| **Already addressed** | Point to existing code/test that handles this |
| **Not applicable** | Explain why this doesn't apply to this context |

## Step 6: Implement Changes

For each finding classified as "Agree":
1. Make the code change
2. Add or update tests if needed
3. Briefly note what was changed

Work through findings by severity (Critical first, then High, Medium, Low).

## Step 7: Commit Changes

After implementing all agreed-upon fixes:

```bash
git add -A
git commit -m "fix(<id>): address round N review feedback"
```

## Step 8: Next Steps

Present options to the user:

```
## Review Response Complete

### Changes Made
- [Summary of fixes implemented]

### Findings Deferred
- [Any disagreements or not-applicable items, with reasoning]

### Next Steps
- `/feature-submit <id>` — submit for another review round
- `/feature-ship <id>` — merge and ship (if satisfied with review state)
```
