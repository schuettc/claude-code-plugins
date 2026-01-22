---
name: feature-init
description: Initialize feature-workflow directory structure in a project. Run this first before using /feature-capture.
user-invocable: true
---

# Initialize Feature Workflow

Run the bundled initialization script to create the `docs/features/` directory structure.

## Execute This Script

```bash
bash ~/.claude/plugins/cache/schuettc-claude-code-plugins/feature-workflow/*/skills/feature-init/scripts/init.sh "$(pwd)"
```

Or if using the skill directory directly:

```bash
bash "$(dirname "$0")/scripts/init.sh" "$(pwd)"
```

## What It Creates

- `docs/features/` - Directory for all features
- `docs/features/DASHBOARD.md` - Initial dashboard template

## After Initialization

Use these commands:
- `/feature-capture` - Add a feature to the backlog
- `/feature-plan` - Start implementing a feature
- `/feature-ship` - Complete a feature

## Script Location

The init script is bundled at: [scripts/init.sh](scripts/init.sh)
