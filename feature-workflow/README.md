# Feature Workflow Plugin

**Version:** 2.0.0

A Claude Code plugin for feature lifecycle management with JSON-based backlog tracking. Capture feature ideas, plan implementations, and kick off development with adaptive agent dispatch.

## What's New in 2.0

- **Hook-based atomic transitions** - File operations are now handled by shell scripts via Claude Code hooks, making status transitions reliable and deterministic
- **Automatic recovery** - Interrupted transitions are detected and repaired automatically
- **Testable independently** - Hook scripts can be tested outside of Claude Code

## Requirements

- **jq** - Required for JSON manipulation in hooks
  ```bash
  # macOS
  brew install jq

  # Ubuntu/Debian
  sudo apt-get install jq

  # Check installation
  jq --version
  ```

## Installation

### From GitHub (recommended)
```bash
# Add the marketplace
/plugin marketplace add schuettc/claude-code-plugins

# Install the plugin
/plugin install feature-workflow@schuettc-claude-code-plugins
```

### Development Mode
```bash
git clone https://github.com/schuettc/claude-code-plugins.git
claude --plugin-dir ./claude-code-plugins/feature-workflow
```

## Recommended Setup

### Terminal Context (Status Line)

This plugin can display the current feature name in Claude Code's status line, making it easy to identify which feature you're working on in each terminal tab.

**1. Create the status line script** (`~/dotfiles/config/claude/statusline.sh` or your preferred location):

```bash
#!/bin/bash
input=$(cat)
SESSION_ID=$(echo "$input" | jq -r '.session_id')
MODEL=$(echo "$input" | jq -r '.model.display_name // "Claude"')

mkdir -p ~/.claude/sessions

# Write session mapping for iTerm tab identification
if [[ -n "$ITERM_SESSION_ID" ]]; then
  echo "$SESSION_ID" > ~/.claude/sessions/iterm-${ITERM_SESSION_ID}.session
fi

# Read feature name if set by /feature-plan
FEATURE=""
if [[ -f ~/.claude/sessions/${SESSION_ID}.feature ]]; then
  FEATURE=$(cat ~/.claude/sessions/${SESSION_ID}.feature)
fi

# Display feature name or session ID
if [[ -n "$FEATURE" ]]; then
  echo "[$FEATURE] $MODEL"
else
  echo "[$MODEL] ${SESSION_ID:0:8}"
fi
```

Make it executable: `chmod +x ~/dotfiles/config/claude/statusline.sh`

**2. Add to `~/.claude/settings.json`:**

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/dotfiles/config/claude/statusline.sh"
  },
  "permissions": {
    "allow": [
      "Bash(*/.claude/sessions/*)"
    ]
  }
}
```

The permissions rule auto-approves the bash command that writes the feature mapping, so you won't be prompted each time.

## Commands

### `/feature-capture`

Interactive workflow for adding items to the JSON backlog.

**Usage:**
```
/feature-capture
```

**What it does:**
1. Asks 8 focused questions to capture the backlog item:
   - Item type (Feature, Enhancement, Tech Debt, Bug Fix)
   - Feature name
   - Problem statement
   - Priority (P0, P1, P2)
   - Effort estimate (Low, Medium, Large)
   - Impact level (Low, Medium, High)
   - Affected areas (optional)
   - **Dependencies (optional)** - Other features that must complete first

2. Creates/updates `docs/planning/backlog.json` with the new item
   - If dependencies specified, creates bidirectional relationships

3. Provides a summary and next steps

### `/feature-plan [feature-id]`

Start implementing a feature from the backlog with comprehensive planning.

**Usage:**
```
/feature-plan dark-mode-toggle
```

Or without an ID to see available items:
```
/feature-plan
```

**What it does:**
1. **Feature Selection** - Choose from backlog or validate provided ID
2. **Dependency Check** - Warns if feature has unmet dependencies
   - Shows which dependencies are incomplete
   - Offers to show alternative features with no blockers
   - Allows proceeding anyway if user confirms
3. **Requirements Analysis** - Deep dive with project-manager agent
   - Optional: code-archaeologist for legacy code analysis
3. **System Design** - Adaptive architecture planning based on feature type:
   - Backend-only → api-designer
   - Frontend-only → ux-optimizer + frontend-architect
   - Full-stack → api-designer + frontend-architect + integration-designer
   - UI-heavy → ux-optimizer first, then full-stack agents
   - Infrastructure → system-designer
4. **Test Specifications** - TDD approach with test-generator agent
5. **Implementation Plan** - Creates structured plan with actionable steps
6. **Documentation Setup** - Prepares docs with documentation-agent
7. **Status Update** - Updates backlog.json to "in-progress"
8. **Kickoff Summary** - Creates todos and provides next steps

### `/feature-ship [feature-id]`

Complete a feature with quality gates - security review, QA validation, and final verification.

**Usage:**
```
/feature-ship dark-mode-toggle
```

Or without an ID to see in-progress items:
```
/feature-ship
```

**What it does:**
1. **Pre-flight Check** - Verify feature is in-progress, has implementation artifacts
2. **Security Review** - Run security-reviewer agent (BLOCKS on Critical/High issues)
   - OWASP Top 10 vulnerability scanning
   - Dependency CVE checking
   - Authentication/authorization validation
3. **QA Validation** - Run qa-engineer agent
   - Test coverage assessment
   - Acceptance criteria verification
   - Release readiness evaluation
4. **Final Verification** - Run tests, type checks, build
5. **Status Update** - Update backlog.json to "completed"
6. **Unblock Notification** - Shows which features are now unblocked
   - Lists features that are fully ready to start
   - Lists features that are partially unblocked (some deps remaining)
7. **Summary** - Display completion report with timeline and quality metrics

## File Organization

All files are organized in a clean, predictable structure:

```
docs/planning/
├── backlog.json                    # Items with status: "backlog"
├── in-progress.json                # Items with status: "in-progress"
├── completed.json                  # Items with status: "completed"
└── features/
    ├── dark-mode-toggle/           # One directory per feature
    │   ├── requirements.md         # Detailed requirements
    │   ├── design.md               # System design (if applicable)
    │   └── plan.md                 # Implementation plan
    └── user-authentication/
        ├── requirements.md
        ├── design.md
        └── plan.md
```

### Key Principles

| Principle | How It Works |
|-----------|--------------|
| **Split by status** | Items are organized into three JSON files by status (v2.0 format) |
| **Global summary in each file** | Any single file contains counts across all files |
| **Atomic transitions via hooks** | Shell scripts handle file operations reliably (write-first pattern) |
| **Nothing moves** | Feature artifact files are created once and stay in place |
| **Feature isolation** | Each feature's artifacts live together in `features/[id]/` |

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FEATURE LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ADD TO BACKLOG                                              │
│     /feature-capture                                             │
│     └─> Creates entry in backlog.json                           │
│     └─> Syncs summary to all status files                       │
│                                                                  │
│  2. START IMPLEMENTING                                           │
│     /feature-plan [id]                                           │
│     └─> Creates features/[id]/ directory                        │
│     └─> Creates requirements.md, design.md, plan.md             │
│     └─> Moves item: backlog.json → in-progress.json             │
│                                                                  │
│  3. DEVELOPMENT WORK                                             │
│     [You build the feature]                                      │
│     └─> Update plan.md progress log as you work                 │
│                                                                  │
│  4. COMPLETE WITH QUALITY GATES                                  │
│     /feature-ship [id]                                           │
│     └─> Runs security-reviewer agent (blocks on issues)         │
│     └─> Runs qa-engineer agent (validates quality)              │
│     └─> Verifies all tests pass                                 │
│     └─> Moves item: in-progress.json → completed.json           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## How Hooks Work

Status transitions are handled by shell scripts that run automatically via Claude Code's hook system. This ensures reliable, atomic file operations.

### Hook Architecture

```
Command (decides)  →  Intent File  →  Hook (detects)  →  Shell Script (executes)
       │                   │                │                     │
  /feature-plan     .transition/      PostToolUse           jq-based
  decides to         intent.json      hook fires            atomic ops
  transition
```

### What Happens During a Transition

1. **Command writes intent** - Claude writes a JSON file describing the desired transition
2. **Hook fires** - Claude Code's PostToolUse hook detects the write
3. **Script executes** - Shell script performs atomic file operations with `jq`
4. **Result returned** - Script writes success/error to result file
5. **Cleanup** - Stop hook removes temporary files when session ends

### Hook Files

```
feature-workflow/hooks/
├── transition-handler.sh      # Main dispatcher
├── lib/
│   ├── common.sh              # Shared utilities
│   ├── validate.sh            # JSON validation
│   ├── summary.sh             # Summary sync across files
│   └── recover.sh             # Recovery from interruptions
└── transitions/
    ├── add-to-backlog.sh      # /feature-capture
    ├── backlog-to-inprogress.sh   # /feature-plan
    └── inprogress-to-completed.sh # /feature-ship
```

### Testing Hooks Independently

You can test hook scripts without Claude Code:

```bash
# Test adding an item
echo '{
  "type": "add-to-backlog",
  "projectRoot": "/path/to/project",
  "item": { "id": "test", "name": "Test", ... }
}' | ./hooks/transitions/add-to-backlog.sh

# Check result
cat docs/planning/.transition/result.json
```

## JSON Backlog Structure

The plugin stores backlog items split across three files by status (v2.0 format):

**backlog.json** - Items waiting to be started:
```json
{
  "version": "2.0.0",
  "lastUpdated": "2026-01-01T12:00:00Z",
  "summary": {
    "total": 3,
    "byStatus": { "backlog": 1, "in-progress": 1, "completed": 1 },
    "byPriority": { "P0": 1, "P1": 1, "P2": 1 }
  },
  "items": [
    {
      "id": "analytics-dashboard",
      "name": "Analytics Dashboard",
      "status": "backlog",
      "...": "other fields"
    }
  ]
}
```

**in-progress.json** - Items currently being worked on:
```json
{
  "version": "2.0.0",
  "lastUpdated": "2026-01-01T14:00:00Z",
  "summary": { "...": "same global summary" },
  "items": [
    {
      "id": "dark-mode-toggle",
      "name": "Dark Mode Toggle",
      "status": "in-progress",
      "startedAt": "2026-01-01T14:00:00Z",
      "implementationPlan": "docs/planning/features/dark-mode-toggle/plan.md",
      "...": "other fields"
    }
  ]
}
```

**completed.json** - Finished items:
```json
{
  "version": "2.0.0",
  "lastUpdated": "2026-01-01T16:00:00Z",
  "summary": { "...": "same global summary" },
  "items": [
    {
      "id": "user-authentication",
      "name": "User Authentication",
      "status": "completed",
      "completedAt": "2026-01-01T16:00:00Z",
      "...": "other fields"
    }
  ]
}
```

**Key points:**
- Each file contains only items matching its status
- The `summary` section is identical across all files (global counts)
- Files are created on-demand (in-progress.json created by first `/feature-plan`)
- Version 2.0.0 indicates multi-file format

### Dependency Fields

| Field | Type | Description |
|-------|------|-------------|
| `dependsOn` | `string[]` | Feature IDs that must be completed before this one can start |
| `blockedBy` | `string[]` | Feature IDs that are waiting for this feature to complete |

**Bidirectional Invariant**: If A.dependsOn contains B, then B.blockedBy contains A.
```

## Dependency Management

The plugin tracks dependencies between features to prevent blocked work and improve planning.

### How Dependencies Work

```
Feature A (depends on B)          Feature B (blocks A)
┌──────────────────────┐         ┌──────────────────────┐
│ dependsOn: ["B"]     │ ───────▶│ blockedBy: ["A"]     │
└──────────────────────┘         └──────────────────────┘
```

### Declaring Dependencies

**During capture:**
```
/feature-capture
...
Q8: Dependencies (optional)?
> user-auth, analytics-api
```

**What happens:**
1. New feature's `dependsOn` gets `["user-auth", "analytics-api"]`
2. `user-auth.blockedBy` gets the new feature's ID added
3. `analytics-api.blockedBy` gets the new feature's ID added

### Dependency Warnings

When you run `/feature-plan` on a feature with unmet dependencies:

```
⚠️ Dependency Warning

This feature has unmet dependencies:

| Dependency    | Status      | Notes              |
|---------------|-------------|--------------------|
| analytics-api | in-progress | Started 3 days ago |
| user-auth     | completed   | ✓ Ready            |

1 of 2 dependencies unmet.

Options:
1. Proceed anyway
2. Show alternative features (no blockers)
3. Cancel
```

### Unblock Notifications

When you complete a feature with `/feature-ship`, you'll see what's unblocked:

```
## Features Now Unblocked

### Fully Unblocked (ready to start)
- **New Dashboard** (new-dashboard): All dependencies met

### Partially Unblocked
- **Reporting Export** (reporting-export): 2/3 deps met
  - Still needs: data-export-api
```

### Circular Dependency Prevention

The plugin prevents impossible dependency chains:

```
Attempting: A depends on B, B depends on A

Error: Circular dependency detected: A -> B -> A
```

---

## Included Agents

The plugin includes 11 specialized agents that are dispatched based on feature type and workflow phase:

### Planning & Requirements Agents

| Agent | Purpose | Used In |
|-------|---------|---------|
| **project-manager** | Requirements analysis, user stories, acceptance criteria | implement Phase 2 |
| **code-archaeologist** | Reverse-engineer undocumented legacy code before modification | implement Phase 2 (optional) |

### Design Agents

| Agent | Purpose | Used In |
|-------|---------|---------|
| **system-designer** | High-level architecture for infrastructure features | implement Phase 3 |
| **api-designer** | GraphQL/API design for backend features | implement Phase 3 |
| **frontend-architect** | React component architecture | implement Phase 3 |
| **integration-designer** | Frontend-backend integration patterns | implement Phase 3 |
| **ux-optimizer** | UX optimization for UI-heavy features | implement Phase 3 |

### Implementation & Documentation Agents

| Agent | Purpose | Used In |
|-------|---------|---------|
| **test-generator** | TDD - write test specifications before implementation | implement Phase 4 |
| **documentation-agent** | Documentation preparation and maintenance | implement Phase 5 |

### Quality Gate Agents

| Agent | Purpose | Used In |
|-------|---------|---------|
| **security-reviewer** | OWASP Top 10, CVE scanning, vulnerability detection | complete Phase 2 |
| **qa-engineer** | Test coverage, acceptance criteria, release validation | complete Phase 3 |

## Skills (Model-Invoked)

Skills are **automatically invoked by Claude** when context is relevant. Unlike commands (which you explicitly call), skills work in the background to enhance your workflow.

| Skill | Behavior | Purpose |
|-------|----------|---------|
| **checking-backlog** | Silent (read-only) | Auto-check backlog when discussing feature ideas |
| **loading-feature-context** | Silent (read-only) | Auto-load requirements/design/plan during implementation |
| **tracking-progress** | Ask first (writes) | Update plan.md progress log when completing tasks |
| **displaying-status** | Silent (read-only) | Quick status overview when asking "what's next?" |
| **guarding-scope** | Silent (read-only) | Flag scope creep, suggest adding to backlog |

### How Skills Work

- **Silent skills**: Claude uses them automatically without asking (read-only operations)
- **Ask-first skills**: Claude asks permission before modifying files

### Skill Details

**checking-backlog**
- Triggers when you say: "We should add...", "Is X planned?", "What features..."
- Shows matching backlog items or suggests `/feature-capture`

**loading-feature-context**
- Triggers when working on code while a feature is in-progress
- Loads requirements.md, design.md, plan.md into context

**tracking-progress**
- Triggers when you complete tasks: "Done with X", "Finished Y"
- Asks before updating plan.md progress log and checking off items

**displaying-status**
- Triggers when you ask: "What's next?", "Status?", "Show backlog"
- Displays formatted project status summary

**guarding-scope**
- Triggers when requesting changes during implementation
- Compares against requirements, flags potential scope creep

## Feature Type Detection

The `/feature-plan` command automatically detects feature type and dispatches appropriate agents:

| Feature Type | Detection | Agents Used |
|--------------|-----------|-------------|
| Backend-Only | API/Lambda/database keywords | api-designer |
| Frontend-Only | UI/component/React keywords | ux-optimizer + frontend-architect |
| Full-Stack | Both UI and API keywords | api-designer + frontend-architect + integration-designer |
| UI-Heavy | Many UI keywords + API | ux-optimizer → then full-stack agents |
| Infrastructure | deployment/monitoring keywords | system-designer |

## Philosophy

**"Never Code Without a Plan"**

This plugin enforces thoughtful planning before implementation:

1. **Capture ideas quickly** - `/feature-capture` takes ~5 minutes
2. **Plan thoroughly when ready** - `/feature-plan` takes 15-30 minutes but saves hours
3. **Keep everything organized** - Three status files, one directory per feature
4. **Reliable operations** - Hook-based transitions that work consistently

## Troubleshooting

### "jq is required but not installed"

Install jq using your package manager (see Requirements section above).

### Hook not firing

1. Verify the plugin is enabled: `/plugin list`
2. Check hook scripts are executable: `ls -la feature-workflow/hooks/`
3. Manually test: `echo '{}' | ./hooks/transition-handler.sh`

### Data corruption / duplicates

Run the recovery script:
```bash
./feature-workflow/hooks/lib/recover.sh /path/to/project
```

This detects duplicates across files and syncs summaries.

## License

MIT
