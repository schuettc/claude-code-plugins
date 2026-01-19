# Phase 2: Validation

## Step 1: Format Detection

Determine if using single-file (v1.x) or multi-file (v2.0) format:

1. **Check for multi-file indicators**:
   - If `docs/planning/in-progress.json` exists -> multi-file format
   - If `docs/planning/completed.json` exists -> multi-file format
   - If `docs/planning/backlog.json` exists with `version === "2.0.0"` -> multi-file format
   - Otherwise -> single-file format (or new backlog)

2. **Store format for later phases**:
   - `isMultiFile = true` if any multi-file indicator found
   - This determines whether to sync summaries to other files

## Step 2: Initialize or Load Backlog

1. **Check if backlog.json exists**: If not, create initial structure:
```json
{
  "version": "2.0.0",
  "lastUpdated": "[current ISO timestamp]",
  "summary": {
    "total": 0,
    "byStatus": { "backlog": 0, "in-progress": 0, "completed": 0 },
    "byPriority": { "P0": 0, "P1": 0, "P2": 0 }
  },
  "items": []
}
```

2. **Read existing backlog**: Load `docs/planning/backlog.json`

3. **Generate ID**: Convert feature name to kebab-case
   - "Dark Mode Toggle" -> "dark-mode-toggle"
   - Remove special characters, lowercase, replace spaces with hyphens

4. **Check for duplicate ID**: Search items array for matching id
   - If duplicate exists, ask user to choose a different name or cancel

5. **Validate required fields**: Ensure all required data is captured

6. **Validate dependencies (if provided)**:
   a. Parse comma-separated list, trim whitespace
   b. For each dependency ID:
      - Check it exists in the items array -> If not found: "Feature '[id]' not found. Available IDs: [list]"
      - Check it's not the same as new item's ID -> If same: "A feature cannot depend on itself"
   c. Check for circular dependencies using BFS algorithm (see below)
   d. If any validation fails, report error and ask for correction

## Circular Dependency Detection Algorithm

Before adding dependencies, verify no cycles would be created:

```
FUNCTION hasCircularDependency(newItemId, targetDepId, allItems):
    """
    Check if making newItemId depend on targetDepId would create a cycle.
    A cycle exists if targetDepId already depends (directly or transitively) on newItemId.
    """

    visited = Set()
    queue = [targetDepId]

    WHILE queue is not empty:
        current = queue.shift()

        IF current === newItemId:
            RETURN true  // Cycle detected!

        IF current in visited:
            CONTINUE

        visited.add(current)

        item = findItemById(current, allItems)
        IF item AND item.dependsOn:
            FOR EACH depId IN item.dependsOn:
                IF depId not in visited:
                    queue.push(depId)

    RETURN false  // No cycle
```

If a cycle is detected, reject with: "Circular dependency detected: [chain path]"
