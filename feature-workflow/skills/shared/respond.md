# Respond to Review Feedback

Read PR review feedback from external reviewers, validate findings, implement fixes, reply inline on each resolved thread, and push updates. This file is shared by `/feature-review-plan` and `/feature-review-impl`.

## Step 1: Find the PR

```bash
gh api "repos/{owner}/{repo}/pulls?state=open&per_page=100" \
  --jq '[.[] | select(.head.ref == "feature/<id>")] | .[0] | {number, url: .html_url}'
```

> **Why REST here:** `gh pr list --json` uses GraphQL. REST has a much larger request budget. Below in Step 2 we still use GraphQL — but only because review-thread IDs (needed for resolution) are not exposed by REST.

Capture `owner/repo` from `gh api "repos/{owner}/{repo}" --jq '.full_name'` — you'll need it in every subsequent call.

If no PR exists, suggest running `/feature-review-plan <id>` or `/feature-review-impl <id>` first.

## Step 2: Collect Review Feedback (with thread IDs)

Use GraphQL to fetch review threads. Unlike the REST endpoint, GraphQL returns the **thread ID** which is required to resolve the thread later.

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 20) {
            nodes {
              databaseId
              body
              author { login }
            }
          }
        }
      }
      reviews(first: 50) {
        nodes {
          author { login }
          state
          body
          submittedAt
        }
      }
    }
  }
}' -F owner=OWNER -F repo=REPO -F pr=PR_NUMBER
```

Store the response. You need:
- `reviewThreads.nodes[].id` — GraphQL thread ID (for resolving)
- `reviewThreads.nodes[].comments.nodes[0].databaseId` — REST comment ID of the first (top) comment in the thread (for replying)
- `reviewThreads.nodes[].path` + `.line` + `.comments.nodes[0].body` — to match against findings
- `reviews.nodes[]` — top-level review bodies (Critical Findings, Recommendations sections)
- `isResolved` — skip threads that are already resolved; you don't need to re-respond

If no reviews or unresolved threads exist:
**"No open review feedback on the PR. Reviewers may not have run yet, or all threads are already resolved."**

## Step 3: Synthesize Findings

Build one consolidated list. For each finding, record:

1. **Source** — reviewer GitHub login (e.g., `github-actions[bot]`)
2. **Origin** — `inline-thread` (has thread ID) or `top-level-review` (body only, no thread to resolve)
3. **Severity** — Blocking / Should-fix (from the finding text)
4. **Thread ID** — GraphQL ID, if inline
5. **Top comment ID** — REST `databaseId` of the first comment in the thread, if inline
6. **Location** — `path:line`
7. **Summary** — one sentence
8. **Full body** — the original finding text

Group by severity. For inline threads, also note if multiple reviewers agree on the same path+line.

## Step 4: Present to User

```
## PR Review Feedback Summary

PR: <pr-url>

### Reviewers
- github-actions[bot]: commented (2026-04-13T02:39:16Z)

### Blocking
1. [Summary] — inline thread at `path:line` — (thread-id abbreviated)
2. [Summary] — top-level only (no thread)

### Should-fix
1. ...

### Already Resolved (will not re-respond)
- [Threads that were already resolved — listed for context only]
```

Ask: **"Which findings should we address? Any you want to push back on or mark as already handled?"**

## Step 5: Classify Each Finding

| Classification | Action |
|---|---|
| **Agree** | Implement fix → reply inline with what changed → resolve thread |
| **Disagree** | Reply inline with reasoning → leave thread open (reviewer can respond) |
| **Already addressed** | Reply inline pointing to the existing code/test/plan-section → resolve thread |
| **Deferred** | Reply inline explaining why it's deferred and where it's tracked → resolve thread |

## Step 6: Implement Changes

Work through **Agree** findings by severity (Blocking first). For plan reviews: edit `plan.md`. For impl reviews: edit the code and tests.

Keep a mapping of `finding → files-changed → one-line summary` so Step 7 can reference specific commits and code.

Commit and push in a single batch at the end:

```bash
git add -A
git commit -m "fix(<id>): address review feedback"
git push
```

## Step 7: Reply Inline on Each Thread

For every finding that has a thread (inline origin), post a reply to the top comment of that thread. Replies use the REST `replies` endpoint and the top comment's `databaseId` from Step 2.

```bash
gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments/TOP_COMMENT_ID/replies" \
  --method POST \
  -f "body=Resolved in <short-sha>: <one-sentence description of the fix>. <Optional pointer to the specific line/section that changed.>"
```

**Reply body guidance:**
- Lead with the commit SHA and a one-sentence description of what changed.
- If the fix is in a specific file/line, point to it.
- For **Disagree**: explain the reasoning in 1-2 sentences. Example: *"Not changing this — the caller contract in `src/auth/types.ts:14` guarantees `user` is non-null by the time this runs, so the defensive check would be dead code."*
- For **Already addressed**: point to the existing code. Example: *"Already handled at `src/api/errors.ts:17` — the `errorResponder` wraps all route handlers and translates thrown errors to 503."*
- Keep replies under ~3 sentences. Detail belongs in the commit, not the comment.

Do **one reply per thread**. Do not reply to every comment in a thread.

## Step 8: Resolve the Threads You Addressed

For every finding classified as **Agree**, **Already addressed**, or **Deferred**, resolve the thread after replying. For **Disagree**, leave the thread open so the reviewer can respond.

Use GraphQL (REST does not support thread resolution):

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { id isResolved }
  }
}' -F threadId=GRAPHQL_THREAD_ID
```

If a reviewer reopens the thread later (e.g., the next re-review decides the fix wasn't enough), that's expected — you'll see it as unresolved again on the next `/feature-review-plan <id> --respond` pass.

## Step 9: Top-Level Summary Comment

After all inline replies and resolutions, post a single top-level comment summarizing the round. This gives the reviewer (human or bot) a high-level view for the next pass:

```bash
gh pr comment PR_NUMBER --body-file - <<'EOF'
## Review Response (round N)

Addressed in <commit-sha>:

**Blocking resolved**
- [Finding summary] — [1-line fix description]

**Should-fix resolved**
- [Finding summary] — [1-line fix description]

**Disagreed (thread left open)**
- [Finding summary] — [1-line reasoning]

**Deferred**
- [Finding summary] — [where it's tracked]

Ready for another look.
EOF
```

Only include sections that have entries. If every finding is resolved, skip the Disagreed/Deferred sections entirely.

## Step 10: Next Steps

Read `.feature-workflow.yml` and check the `reviewer:` setting.

**If CI reviewer is configured (`gemini` or `codex`):**

```
## Review Response Complete

Changes pushed to feature/<id>. Inline threads resolved where fixes landed.
The CI reviewer will re-run automatically on the updated PR.

### Next Steps
- Watch the PR for the next review round
- `/feature-review-plan <id> --respond` or `/feature-review-impl <id> --respond` — handle the next round when it arrives
- `/feature-implement <id>` — start coding (if plan review is satisfactory)
- `/feature-ship <id>` — merge PR and ship (if implementation review is satisfactory)
```

**If no CI reviewer (`reviewer: none`):**

```
## Review Response Complete

Changes pushed to feature/<id>. Inline threads resolved where fixes landed.

### Next Steps
- Trigger reviewers again for another pass
- `/feature-review-plan <id> --respond` or `/feature-review-impl <id> --respond` — handle the next round
- `/feature-implement <id>` — start coding (if plan review is satisfactory)
- `/feature-ship <id>` — merge PR and ship (if implementation review is satisfactory)
```

## Common Pitfalls

- **Replying to the wrong comment ID** — use the `databaseId` of the **first** comment in the thread, not a later reply. GraphQL returns comments in order.
- **Forgetting to resolve after replying** — resolving is a separate GraphQL mutation. A replied-but-unresolved thread still shows as unresolved on the PR.
- **Resolving a thread you disagree with** — don't. Leave disagreed threads open so the reviewer can respond or escalate.
- **Reply body too long** — inline replies should be 1-3 sentences. Push detail into the commit message.
- **Skipping already-resolved threads** — Step 2 returns `isResolved` so you can filter. Don't re-reply to resolved threads; it's noise.
