# Claude Code Plugins

A collection of plugins for [Claude Code](https://code.claude.com), Anthropic's CLI for Claude.

## Installation

Add this marketplace to Claude Code:

```bash
/plugin marketplace add schuettc/claude-code-plugins
```

Then install any plugin:

```bash
/plugin install <plugin-name>@schuettc-claude-code-plugins
```

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [feature-workflow](./feature-workflow) | Feature lifecycle with directory-based tracking, event-driven hooks, and optional automated PR reviews via Gemini/Codex in GitHub Actions | 9.2.0 |
| [website-deployment](./website-deployment) | Guided workflow to deploy Node.js/Express apps to AWS serverless (S3 + CloudFront + Lambda + API Gateway + CDK). Analyzes your app, scaffolds infra, and deploys with step-by-step explanations | 1.0.0 |
| [sprint-planner](./sprint-planner) | Sprint planning and team coordination for small teams (2-6 devs). Triage backlogs by deadline, assign work with self-service specs, audit specs for completeness, and generate team communication. Pairs with feature-workflow | 0.1.0 |

## Plugin: feature-workflow

Structured feature development from idea to production, with draft-PR review gates and optional automated review by an external AI (Gemini or Codex) in GitHub Actions.

**Setup:**
- `/feature-init` — one-time project setup. Choose a reviewer (gemini / codex / none), drop in an API key, and the skill writes the workflow, prompts, and `post-review.sh` to `.github/`, uploads the secret, and enables bot PR approvals.

**Lifecycle:**
- `/feature-capture` — capture a feature idea to `docs/features/<id>/idea.md`
- `/feature-plan <id>` — produce `plan.md` with requirements, design, and an implementation breakdown
- `/feature-review-plan <id>` — open a draft PR and trigger plan review; `--respond` replies inline on review threads
- `/feature-implement <id>` — implement the approved plan with scope guarding
- `/feature-review-impl <id>` — trigger impl review on the same PR; `--respond` replies inline
- `/feature-ship <id>` — run security + QA gates, merge the PR, and write `shipped.md`

**Diagnostics:**
- `/feature-status` — snapshot of the dashboard
- `/feature-audit <id>` — evidence-based runtime verification
- `/feature-troubleshoot` — structured debugging for shipped features

**Install:**
```bash
/plugin install feature-workflow@schuettc-claude-code-plugins
```

See [feature-workflow/README.md](./feature-workflow/README.md) for full documentation.

## Plugin: website-deployment

Deploy a local Node.js / Express / Vite web app to AWS serverless infrastructure, guided step-by-step. Claude analyzes your app, explains what needs to happen, scaffolds the infrastructure, and walks you through each decision.

**What it handles:**
- Static frontend hosting via S3 + CloudFront
- Server-side routes converted to Lambda functions behind API Gateway
- DynamoDB for data
- Cognito for authentication
- Infrastructure as code via AWS CDK
- Cost awareness — most dev-traffic deployments fit in the free tier

**Bundled MCP servers** (start automatically): AWS Documentation for live docs lookups, and Playwright for end-to-end browser testing of the deployed app.

**Prerequisites:** Node.js 18+, AWS CLI v2 with credentials, Python + `uvx` (for the AWS docs MCP server).

**Install:**
```bash
/plugin install website-deployment@schuettc-claude-code-plugins
```

See [website-deployment/README.md](./website-deployment/README.md) for prerequisites, usage, and teardown instructions.

## Plugin: sprint-planner

Sprint planning and team coordination for small teams (2-6 devs) with mixed experience levels preparing for demos, releases, or time-boxed sprints. Turns a messy backlog into an actionable sprint plan with assignments that developers can work from independently.

**Skills:**
- `/sprint-triage` — clean up the backlog; close stale items, verify PR status, categorize by deadline
- `/sprint-plan` — create a weekly sprint plan; triage backlog, assign owners, identify critical path
- `/sprint-audit-specs` — audit feature specs for completeness so devs can work independently
- `/sprint-assign` — generate a shareable team assignment message for Slack/email
- `/sprint-retro` — end-of-sprint review; planned vs. actual, lessons learned

**Pairs with feature-workflow:** reads `docs/features/DASHBOARD.md` and feature idea files. Use `/feature-capture` to add items, `/feature-plan` to start work, `/feature-ship` to close them.

**Prerequisites:** Git repository with feature tracking (e.g., `docs/features/DASHBOARD.md` from feature-workflow), GitHub CLI (`gh`) for PR status checks.

**Install:**
```bash
/plugin install sprint-planner@schuettc-claude-code-plugins
```

See [sprint-planner/README.md](./sprint-planner/README.md) for the full workflow and design principles.

## Cloning This Repo? Start Here

If you cloned this repo and want Claude to walk you through installing and using `feature-workflow` in your own project, open Claude Code in this repo and run:

```
/getting-started
```

It's a local skill defined in [.claude/skills/getting-started/SKILL.md](./.claude/skills/getting-started/SKILL.md) — not shipped with the plugin. It orients you to what this repo is, helps you install the plugin from this marketplace, and can drive a live end-to-end demo feature (capture → plan → review → implement → review → ship) against a project of your choice so you see the whole lifecycle before touching real work.

## Development Mode

To test plugins locally:

```bash
git clone https://github.com/schuettc/claude-code-plugins.git
claude --plugin-dir ./claude-code-plugins/<plugin-name>
```

## License

MIT
