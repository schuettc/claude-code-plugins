# Phase 3: Add to Backlog (Hook-Based)

Trigger the atomic addition by writing a transition intent file. The hook will handle all JSON manipulation reliably.

## Step 1: Create Transition Directory

```bash
mkdir -p docs/planning/.transition
```

## Step 2: Write Transition Intent File

Write the following to `docs/planning/.transition/intent.json`:

```json
{
  "type": "add-to-backlog",
  "projectRoot": "[absolute path to project root]",
  "item": {
    "id": "[kebab-case-name]",
    "name": "[Original Name]",
    "type": "[Feature|Enhancement|Tech Debt|Bug Fix]",
    "priority": "[P0|P1|P2]",
    "effort": "[Low|Medium|Large]",
    "impact": "[Low|Medium|High]",
    "problemStatement": "[User's problem description]",
    "proposedSolution": "",
    "affectedAreas": ["[parsed from user input]"],
    "status": "backlog",
    "dependsOn": ["[parsed dependency IDs, or empty array]"],
    "blockedBy": [],
    "metadata": {}
  }
}
```

**Important**: The `projectRoot` must be an absolute path (e.g., `/Users/username/project`).

## Step 3: Verify Result

**IMPORTANT**: Writing the intent file automatically triggers the PostToolUse hook. You do NOT need to run any script manually. The hook runs immediately after your Write tool completes.

The hook automatically:
1. Validates the item structure
2. Checks for duplicate IDs across all status files
3. Validates dependencies exist and no circular dependencies
4. Adds item to backlog.json
5. Updates blockedBy arrays on dependency targets
6. Syncs global summary across all files

Read the result from `docs/planning/.transition/result.json`:

```json
{
  "success": true,
  "transition": "add-to-backlog",
  "itemId": "[id]",
  "timestamp": "[ISO timestamp]",
  "filesModified": ["docs/planning/backlog.json"]
}
```

If there's an error, the result will contain:
```json
{
  "success": false,
  "error": "[error message]"
}
```

Display the error to the user and stop the workflow.
