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
| [feature-workflow](./feature-workflow) | Feature lifecycle with directory-based tracking and event-driven hooks | 4.0.0 |

## Plugin: feature-workflow

Structured feature development with commands, agents, and skills.

**Commands:**
- `/feature-capture` - Capture feature ideas to docs/features/
- `/feature-plan` - Plan implementation with specialized agents
- `/feature-ship` - Verify quality gates before completion

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
