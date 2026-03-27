# Watch Mode

Continuous monitoring mode for the reviewer terminal. Polls for new artifacts and auto-reviews when they appear.

## Usage

```
/feature-review <id> --watch
```

## Behavior

When invoked with `--watch`, enter a polling loop:

### Step 1: Initial State Capture

Record the current state of the feature directory:

```bash
ls -la docs/features/<id>/
ls -la docs/features/<id>/reviews/ 2>/dev/null || echo "No reviews yet"
```

Note which files exist and their modification times.

### Step 2: Poll Loop

Check for changes every 30 seconds:

```bash
# Check for new or modified files
ls -la docs/features/<id>/
ls -la docs/features/<id>/reviews/ 2>/dev/null
```

### Step 3: Auto-Review Triggers

When a new file or change is detected:

| Trigger | Action |
|---------|--------|
| `plan.md` created or modified | Run plan review ([plan-review.md](plan-review.md)) |
| `reviews/request-plan.md` appears | Run plan review |
| `reviews/request-impl.md` appears | Run implementation review ([impl-review.md](impl-review.md)) |
| `reviews/request-preship.md` appears | Run pre-ship review ([ship-review.md](ship-review.md)) |
| Plan.md checkboxes change | Run implementation review |

### Step 4: Notification

After each auto-review, display:

```
[WATCH] Detected: [trigger description]
[WATCH] Running: [phase] review
[WATCH] Verdict: [PASS/CONDITIONAL PASS/FAIL]
[WATCH] Review written to: reviews/[filename]
```

### Step 5: Exit Conditions

Continue watching until:
- User interrupts (Ctrl+C)
- `shipped.md` is created (feature completed)
- User explicitly asks to stop

## Notes

- Watch mode is a convenience feature — on-demand `/feature-review <id>` is the primary interface
- The polling interval (30s) balances responsiveness with resource usage
- Each auto-review follows the exact same process as a manual review
- Watch mode should not run reviews redundantly — if a review was just written for the current state, skip until the next change
