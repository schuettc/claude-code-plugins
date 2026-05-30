---
name: github-api-discipline
description: Use whenever build, deploy, or background code reads files from another GitHub repo at runtime — workshop content, manifests, configs fetched from a registry. Captures the rules that keep us under the GitHub App's 15000/hr installation rate limit (zipball over per-file, respect retry-after, share fetched content) and links the reference implementation.
---

# GitHub API discipline

## The rule

When build or deploy code fetches files from another GitHub repo at runtime, default to:

1. **One bulk fetch per repo, not one call per file.** Use `GET /repos/{owner}/{repo}/zipball/{ref}` (or the tarball/`/git/trees?recursive=true` endpoints) and read files from the in-memory archive. Per-file `/contents/{path}` is the trap.
2. **Honor rate-limit headers.** On `429` *or* `403 rate limit exceeded`, read `retry-after` or `x-ratelimit-reset`, sleep, retry (bounded). A single throttled response must never kill a deploy.
3. **Share fetched content within a workflow run.** Don't refetch the same files from two scripts in the same CI job; cache to disk between them.
4. **Authenticate.** Use a GitHub App installation token (15000/hr per installation, separate quota from user PATs). Don't use a user PAT for automation — it shares the user's 5000/hr quota with everything else they do on the same account.

The four are ranked by impact. The biggest single win is #1.

## Why

**Real incident (2026-05-29, learning-with-court/platform).** Each Deploy Dev / Deploy Prod ran two scripts (`bundle:{env}` in the server, `fetch-workshops.ts` in landing) that each iterated over ~8 workshops and called `GET /repos/{o}/{r}/contents/{path}` for each of ~25 files per workshop. ~400 calls per deploy. Under any meaningful burst — multiple PRs + cutover deploys in the same hour — we'd blow the App installation's 15000/hr ceiling and the deploy would fail with `403 API rate limit exceeded for installation ID …` in the middle of a build step.

The fix (`workshop-fetch-rate-limit-fix`) was just zipball + an `withRateLimitRetry` wrapper:

- **Before:** ~400 calls/deploy; Deploy Dev ~3m26s; sporadic deploy failure under bursts.
- **After:** ~16 calls/deploy (8 workshops × 2 scripts); Deploy Dev 1m13s (~3× faster); no rate-limit failures.

The audit also showed we'd been doing the *easy* GitHub best-practices items (authenticated requests, no polling, serial requests) but skipping every high-impact one (zipball, ETag, rate-limit-header backoff). It's the high-impact items that matter.

## How to apply

### When designing a new build/deploy pipeline that fetches GitHub content

- Reach for the **zipball/tarball endpoint** first. Don't list-then-fetch-each-file.
- Wrap the network call in a backoff helper — reference impl at `${CLAUDE_PLUGIN_ROOT}/templates/github-rate-limit/with-rate-limit-retry.ts`.
- If you have two pipeline stages that need the same content, fetch once and cache to a workspace-local dir; have the second stage read from cache.

### When auditing an existing build that hits the GitHub REST API

Walk this checklist; flag anything ❌:

| Practice | Doing it? |
|---|---|
| Authenticated requests (App token, not PAT) | |
| Avoid polling — use webhook/dispatch triggers | |
| Serial requests (not concurrent) | |
| Bulk fetch (zipball/tarball/trees) instead of per-file `/contents` | |
| Honor `retry-after` / `x-ratelimit-reset` on 429/403 | |
| Cache fetched content across stages in the same workflow | |
| Conditional requests with `If-None-Match` (ETag) for cross-run reuse | |

Tackle ❌s in the order shown — they're roughly ranked by payoff.

### When someone says "we should just raise the GitHub rate limit"

Push back. The 15000/hr App installation cap is already the standard high tier. Real fix is *cutting waste*, not asking GitHub for more headroom for waste.

## Reference implementation

- `${CLAUDE_PLUGIN_ROOT}/templates/github-rate-limit/manifest-fetch-zipball.ts` — `createGitHubFileFetcher` that downloads `/zipball/{ref}` once with `fflate` decompression and serves in-memory file reads. Same `FileFetcher` interface as a per-file fetcher — drop-in replacement.
- `${CLAUDE_PLUGIN_ROOT}/templates/github-rate-limit/with-rate-limit-retry.ts` — `withRateLimitRetry` helper + `isRateLimited` classifier.

Both lifted from `learning-with-court/platform`'s `packages/server/src/manifest/`. Same shape works for any "read files from a GitHub repo" use case.
