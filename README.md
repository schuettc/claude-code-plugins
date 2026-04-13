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

**Onboarding:**
- `/getting-started` — after installing the plugin, run this for an interactive walkthrough: it checks your current state, explains the concepts, and can guide you through a live demo feature end-to-end.

**Install:**
```bash
/plugin install feature-workflow@schuettc-claude-code-plugins
```

See [feature-workflow/README.md](./feature-workflow/README.md) for full documentation.

## Development Mode

To test plugins locally:

```bash
git clone https://github.com/schuettc/claude-code-plugins.git
claude --plugin-dir ./claude-code-plugins/<plugin-name>
```

## License

MIT
