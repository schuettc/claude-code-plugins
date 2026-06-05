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
type: [Feature|Enhancement|Bug Fix|Tech Debt|Epic]
priority: [P0|P1|P2]
effort: [Small|Medium|Large]
impact: [Low|Medium|High]
category: [category]
created: [YYYY-MM-DD]

# Ownership (optional)
assignee: [name OR list of names]

# State (optional, default active)
state: [active|paused|replaced|abandoned]
pausedReason: "..."         # if paused
replacedBy: <feature-id>  # if replaced
abandonedReason: "..."      # if abandoned

# Relations (optional)
epic: <epic-id>             # parent epic
children: [id1, id2]        # only for type: Epic
dependsOn: [id1, id2]       # hard blockers
relatedTo: [id3, id4]       # soft links
parallelSafe: true          # default true

# Review override (optional, defers to project config if absent)
review: [external|internal|skip]
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
| type | Yes | Feature, Enhancement, Bug Fix, Tech Debt, or Epic |
| priority | Yes | P0 (critical), P1 (important), P2 (nice to have) |
| effort | Yes | Small (<1 day), Medium (1-3 days), Large (>3 days) |
| impact | Yes | Low, Medium, High |
| category | No | Grouping category (default: "general") |
| created | Yes | Date in YYYY-MM-DD format |
| dependsOn | No | Array of feature IDs this feature depends on: `[id1, id2]` |
| assignee | No | Single name or list |
| state | No | active (default) / paused / replaced / abandoned |
| pausedReason | If state=paused | What we're waiting on |
| replacedBy | If state=replaced | The replacing feature's ID |
| abandonedReason | If state=abandoned | Why we dropped it |
| epic | No | Parent epic ID |
| children | No | List of child IDs (Epic features only) |
| relatedTo | No | Soft links to related features |
| parallelSafe | No | Default `true`; set `false` for features that touch shared files |
| review | No | external / internal / skip — overrides project default |

## Dependency Handling

When capturing a feature with dependencies:

1. **Validate IDs**: Check that each dependency ID exists (soft warning if not — may be pre-capturing).
2. **Write `dependsOn:`** on the new feature.
3. **Do NOT write `blockedBy:` on the dependency targets** — blocked-by is computed dynamically from the dependency graph by the dashboard. Legacy stored `blockedBy:` fields are still parsed for backward compat but no longer maintained on writes.

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
