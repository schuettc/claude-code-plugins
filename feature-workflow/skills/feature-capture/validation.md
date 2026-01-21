# Phase 2: Validation

## Step 1: Check for Existing Features

1. **Read DASHBOARD.md**: Check `docs/features/DASHBOARD.md` if it exists
   - If it doesn't exist yet, that's OK - hook will create it
   - Parse the tables to find existing feature IDs

2. **Generate ID**: Convert feature name to kebab-case
   - "Dark Mode Toggle" -> "dark-mode-toggle"
   - Remove special characters, lowercase, replace spaces with hyphens

3. **Check for duplicate ID**: Look for matching IDs in DASHBOARD.md tables
   - If duplicate exists, ask user to choose a different name or cancel

## Step 2: Validate Required Fields

Ensure all required data was captured from interview phase:

| Field | Required | Validation |
|-------|----------|------------|
| name | Yes | Non-empty string |
| type | Yes | One of: Feature, Enhancement, Bug Fix, Tech Debt |
| priority | Yes | One of: P0, P1, P2 |
| effort | Yes | One of: Small, Medium, Large |
| impact | Yes | One of: Low, Medium, High |
| problemStatement | Yes | Non-empty string |

## Step 3: Check Feature Directory

1. **Check if directory exists**: `docs/features/[id]/`
   - If exists, this is a duplicate - ask user to choose different name
   - If not exists, proceed to Phase 3

## Duplicate Detection Methods

There are two ways to detect duplicates:

1. **Parse DASHBOARD.md**: Look for ID links like `[my-feature](./my-feature/)`
2. **Check filesystem**: Check if `docs/features/[id]/` directory exists

Both methods should be used for reliable duplicate detection.

## Error Handling

If validation fails:
- Display specific error message
- Ask user to correct the issue
- Do NOT proceed to Phase 3 until validation passes
