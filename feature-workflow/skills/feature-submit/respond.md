# Respond Mode

Read PR review feedback from external reviewers, validate findings, implement fixes, and push updates.

## Step 1: Find the PR

```bash
gh pr list --head feature/<id> --json number,url --jq '.[0]'
```

If no PR exists, inform the user and suggest running `/feature-submit <id>` first.

## Step 2: Collect Review Feedback

Read all PR reviews and comments:

```bash
gh pr view <pr-number> --json reviews,comments
```

Also read individual review comments (inline code comments):

```bash
gh api repos/{owner}/{repo}/pulls/<pr-number>/comments --jq '.[] | {user: .user.login, body: .body, path: .path, line: .line, created_at: .created_at}'
```

And PR-level review comments:

```bash
gh api repos/{owner}/{repo}/pulls/<pr-number>/reviews --jq '.[] | {user: .user.login, state: .state, body: .body}'
```

If no reviews or comments are found, inform the user:
**"No review feedback found on the PR yet. Reviewers may not have completed their reviews."**

## Step 3: Synthesize Findings

Create a consolidated list of all findings across reviewers. For each finding:

1. **Source**: Which reviewer raised it (by GitHub username or name)
2. **Severity**: Critical / High / Medium / Low (infer from reviewer's language)
3. **Summary**: What the issue is
4. **Location**: File/line if it's an inline comment
5. **Agreement**: Do multiple reviewers flag the same thing?

Group findings by severity, with cross-reviewer agreements highlighted.

## Step 4: Present to User

Display the consolidated findings:

```
## PR Review Feedback Summary

PR: <pr-url>

### Reviewers
- [reviewer 1]: [state — approved/changes_requested/commented]
- [reviewer 2]: [state]

### Critical/High Findings
1. [Finding] — raised by [reviewer(s)]
   File: [path:line] (if inline comment)
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
| **Disagree** | Reply on the PR explaining reasoning |
| **Already addressed** | Reply pointing to existing code/test |
| **Not applicable** | Reply explaining why |

## Step 6: Implement Changes

For each finding classified as "Agree":
1. Make the code change
2. Add or update tests if needed
3. Briefly note what was changed

Work through findings by severity (Critical first, then High, Medium, Low).

## Step 7: Commit, Push, and Comment

After implementing all agreed-upon fixes:

```bash
git add -A
git commit -m "fix(<id>): address review feedback"
git push
```

Add a PR comment summarizing the response:

```bash
gh pr comment <pr-number> --body "## Review Response

### Changes Made
- [Summary of fixes implemented]

### Findings Addressed
- [List of items fixed with brief description]

### Findings Deferred
- [Any disagreements or not-applicable items, with reasoning]

Ready for another look."
```

## Step 8: Next Steps

Present options to the user:

```
## Review Response Complete

Changes pushed to feature/<id> and PR updated.

### Next Steps
- Wait for reviewers to re-review the PR
- `/feature-submit <id> --respond` — read next round of feedback
- `/feature-ship <id>` — merge PR and ship (if reviews are satisfactory)
```
