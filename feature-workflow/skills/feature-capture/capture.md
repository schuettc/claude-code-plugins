# Phase 3: Create Feature Directory

Create the feature's idea.md file, which triggers the hook to regenerate DASHBOARD.md.

## Step 1: Create Feature Directory

```bash
mkdir -p docs/features/[id]
```

## Step 2: Write idea.md

Write `docs/features/[id]/idea.md` with the following format:

```markdown
---
id: [kebab-case-id]
name: [Original Name]
type: [Feature|Enhancement|Bug Fix|Tech Debt]
priority: [P0|P1|P2]
effort: [Small|Medium|Large]
impact: [Low|Medium|High]
created: [YYYY-MM-DD]
---

# [Original Name]

## Problem Statement
[User's problem description - the WHAT and WHY]

## Proposed Solution
[High-level approach, if provided - keep brief]

## Affected Areas
- [area1]
- [area2]
```

## Frontmatter Fields

All metadata goes in YAML frontmatter between `---` markers:

| Field | Required | Description |
|-------|----------|-------------|
| id | Yes | Kebab-case identifier (matches directory name) |
| name | Yes | Human-readable name |
| type | Yes | Feature, Enhancement, Bug Fix, or Tech Debt |
| priority | Yes | P0 (critical), P1 (important), P2 (nice to have) |
| effort | Yes | Small (<1 day), Medium (1-3 days), Large (>3 days) |
| impact | Yes | Low, Medium, High |
| created | Yes | Date in YYYY-MM-DD format |

## Hook Behavior

**IMPORTANT**: Writing idea.md automatically triggers the PostToolUse hook. You do NOT need to run any script manually.

The hook automatically:
1. Detects the new idea.md file
2. Parses the frontmatter metadata
3. Regenerates DASHBOARD.md with the new feature in the Backlog section

## Verification

After writing idea.md:
1. Check that the file was created successfully
2. Read DASHBOARD.md to verify the feature appears in the Backlog table

## Error Handling

If the write fails:
- Check that docs/features/ directory exists
- Verify file permissions
- Display error to user

If hook fails to update DASHBOARD.md:
- The feature is still valid (idea.md exists)
- User can manually run: `./hooks/generate-dashboard.sh [project-root]`
