---
name: github-repo-setup
description: Use when bootstrapping a new repo's GitHub-side setup — branch protection / rulesets, deploy environments, environment secrets, OIDC cloud auth, or required reviewers — or whenever deploy workflows reference secrets.* / environment: that don't exist yet. Captures the repo settings that make the feat → dev → main promotion model *enforced* rather than convention, and scopes deploy credentials to the environment that gates them.
---

# GitHub repo setup (protection, environments, secrets, OIDC)

## The rule

The promotion model and the CI gate are only real if GitHub enforces them server-side. Convention ("we always PR into dev") protects nothing — someone pushes to `main`, or merges a red PR, and the soak never happened. Four settings close that:

1. **Branch protection on `main` (and `dev`).** Require a PR, require the `ci` status check to pass, require ≥1 approval on `main`, block force-push and deletion. Without this, the promotion model is a suggestion.
2. **A required status check.** The `ci.yml` PR gate must be marked *required* in branch protection. A workflow that merely runs is advisory — only a required check blocks the merge.
3. **Deploy environments (`dev`, `prod`) with protection rules.** The `prod` environment gets **required reviewers** + a **deployment branch policy** limiting it to `main`. This is the literal mechanism behind the promotion model's "every prod deploy is a chosen moment" — the prod job pauses in the Actions UI until a human approves.
4. **Environment-scoped secrets + OIDC trust scoped to the environment.** Deploy credentials live on the environment, not the repo, so prod creds are only reachable from the (reviewer-gated) prod environment. With OIDC there's no long-lived key at all — just an IAM role whose trust policy is scoped to `…:environment:prod`.

## Why

The `branch-promotion-model` skill describes the *flow*; this skill makes it *binding*. A deploy workflow that says `environment: prod` and `secrets.AWS_ROLE_ARN_PROD` is inert until the environment, the secret, and the cloud trust exist — the first push to `dev` fails with "environment not found" or a missing-credentials error. And a `dev → main` promotion PR that can be merged red, or bypassed by a direct push, defeats the entire point of having a soak stage.

The security payoff of scoping is concrete: if the prod role's trust is scoped only to `repo:OWNER/REPO` (not `…:environment:prod`), then *any* workflow in the repo — including one on an attacker's PR branch — can assume the prod deploy role. Scoping the trust to the environment means only the reviewer-gated prod job can.

## How to apply

These use `gh` + `gh api`. Substitute `OWNER/REPO`. Run after the `dev` branch and the workflows exist (the `ci` check must have run at least once before it can be marked required).

### 1. Environments + protection rules

```bash
# Create environments
gh api --method PUT repos/OWNER/REPO/environments/dev >/dev/null
gh api --method PUT repos/OWNER/REPO/environments/prod >/dev/null

# prod: require a reviewer and restrict deploys to the main branch only
gh api --method PUT repos/OWNER/REPO/environments/prod \
  -F 'reviewers[][type]=User' -F 'reviewers[][id]=<REVIEWER_USER_ID>' \
  -F 'deployment_branch_policy[protected_branches]=false' \
  -F 'deployment_branch_policy[custom_branch_policies]=true' >/dev/null
gh api --method POST repos/OWNER/REPO/environments/prod/deployment-branch-policies \
  -f name=main >/dev/null
# (find a user id: gh api users/<login> --jq .id)
```

For `dev`, restrict the deployment branch policy to `dev` the same way; reviewers are usually unnecessary there — the whole point of dev is fast iteration.

### 2. Environment-scoped secrets

```bash
gh secret set AWS_ROLE_ARN_DEV  --env dev  --body "arn:aws:iam::<acct>:role/<dev-deploy-role>"
gh secret set AWS_ROLE_ARN_PROD --env prod --body "arn:aws:iam::<acct>:role/<prod-deploy-role>"
```

Environment-scoped (not repo-scoped) so the prod ARN is only resolvable inside the reviewer-gated prod environment. Repo-level secrets are fine for things needed everywhere (e.g. a read-only token); deploy creds should not be.

### 3. OIDC cloud trust (AWS shown; same idea on GCP/Azure)

No stored cloud key — the `aws-actions/configure-aws-credentials` step exchanges the GitHub OIDC token for short-lived STS creds.

1. Add GitHub as an IAM OIDC identity provider (once per AWS account):
   - Provider URL: `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. Create the deploy role with a trust policy scoped to the **environment**, not just the repo:
   ```json
   {
     "Condition": {
       "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
       "StringLike": { "token.actions.githubusercontent.com:sub": "repo:OWNER/REPO:environment:prod" }
     }
   }
   ```
   Use `:environment:dev` for the dev role. Scoping to `:ref:refs/heads/main` is a weaker alternative — prefer `:environment:` so the reviewer gate is part of the trust boundary.

### 4. Branch protection / rulesets

Mark `ci` required and lock down `main`. Prefer a **ruleset** (newer, supports multiple branches via fnmatch); the legacy per-branch API also works.

```bash
# main: PR required, ci must pass, 1 approval, no force-push/deletion
gh api --method PUT repos/OWNER/REPO/branches/main/protection \
  --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["ci"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 1, "dismiss_stale_reviews": true },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

For `dev`, a lighter version (PR + `ci` required, no required approvals) keeps iteration fast while still blocking red merges. The status-check *context* must match the job/check name in `ci.yml` (here, `ci`) — if you rename the job, update both.

### When someone proposes skipping protection "just to move fast"

Push back. The promotion model's entire value is the enforced soak; unprotected branches turn it back into a naming convention. Required reviewers on `prod` cost one click per deploy and are what make "deliberate prod promotion" true instead of aspirational. See `branch-promotion-model`.

## Related

- `branch-promotion-model` — the flow these settings enforce.
- `quality-stack-setup` — the local half (lefthook commit/push hooks + the shared justfile); the `ci` required check is the server-side half. The standing suppression rule and ongoing operation live in `quality-workflow`.
- Deploy templates `github-workflows/deploy-{dev,prod}.yml` reference `environment:` and `secrets.AWS_ROLE_ARN_*` set up here; `github-workflows/ci.yml` is the gate marked required here.
