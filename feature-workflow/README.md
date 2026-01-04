# Feature Workflow Plugin

**Version:** 1.5.0

A Claude Code plugin for feature lifecycle management with JSON-based backlog tracking. Capture feature ideas, plan implementations, and kick off development with adaptive agent dispatch.

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

## Commands

### `/feature-capture`

Interactive workflow for adding items to the JSON backlog.

**Usage:**
```
/feature-capture
```

**What it does:**
1. Asks 7 focused questions to capture the backlog item:
   - Item type (Feature, Enhancement, Tech Debt, Bug Fix)
   - Feature name
   - Problem statement
   - Priority (P0, P1, P2)
   - Effort estimate (Low, Medium, Large)
   - Impact level (Low, Medium, High)
   - Affected areas (optional)

2. Creates/updates `docs/planning/backlog.json` with the new item

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
2. **Requirements Analysis** - Deep dive with project-manager agent
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
6. **Summary** - Display completion report with timeline and quality metrics

## File Organization

All files are organized in a clean, predictable structure:

```
docs/planning/
├── backlog.json                    # Single source of truth
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
| **Single source of truth** | `backlog.json` tracks ALL items and their status |
| **Nothing moves** | Files are created once and stay in place |
| **Status is a field, not a folder** | No `backlog/`, `in-progress/`, `completed/` directories |
| **Feature isolation** | Each feature's artifacts live together in `features/[id]/` |

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FEATURE LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ADD TO BACKLOG                                              │
│     /feature-capture                                             │
│     └─> Creates entry in backlog.json (status: "backlog")       │
│                                                                  │
│  2. START IMPLEMENTING                                           │
│     /feature-plan [id]                                           │
│     └─> Creates features/[id]/ directory                        │
│     └─> Creates requirements.md, design.md, plan.md             │
│     └─> Updates backlog.json (status: "in-progress")            │
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
│     └─> Updates backlog.json (status: "completed")              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## JSON Backlog Structure

The plugin stores backlog items in `docs/planning/backlog.json`:

```json
{
  "version": "1.0.0",
  "lastUpdated": "2026-01-01T12:00:00Z",
  "summary": {
    "total": 3,
    "byStatus": {
      "backlog": 1,
      "in-progress": 1,
      "completed": 1
    },
    "byPriority": {
      "P0": 1,
      "P1": 1,
      "P2": 1
    }
  },
  "items": [
    {
      "id": "dark-mode-toggle",
      "name": "Dark Mode Toggle",
      "type": "Feature",
      "priority": "P1",
      "effort": "Medium",
      "impact": "High",
      "problemStatement": "Users need to switch between themes.",
      "proposedSolution": "",
      "affectedAreas": ["frontend/settings"],
      "status": "in-progress",
      "createdAt": "2026-01-01T10:00:00Z",
      "updatedAt": "2026-01-01T14:00:00Z",
      "startedAt": "2026-01-01T14:00:00Z",
      "completedAt": null,
      "implementationPlan": "docs/planning/features/dark-mode-toggle/plan.md",
      "metadata": {}
    }
  ]
}
```

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
| **backlog-awareness** | Silent (read-only) | Auto-check backlog when discussing feature ideas |
| **feature-context** | Silent (read-only) | Auto-load requirements/design/plan during implementation |
| **progress-tracker** | Ask first (writes) | Update plan.md progress log when completing tasks |
| **status-dashboard** | Silent (read-only) | Quick status overview when asking "what's next?" |
| **scope-guard** | Silent (read-only) | Flag scope creep, suggest adding to backlog |

### How Skills Work

- **Silent skills**: Claude uses them automatically without asking (read-only operations)
- **Ask-first skills**: Claude asks permission before modifying files

### Skill Details

**backlog-awareness**
- Triggers when you say: "We should add...", "Is X planned?", "What features..."
- Shows matching backlog items or suggests `/feature-capture`

**feature-context**
- Triggers when working on code while a feature is in-progress
- Loads requirements.md, design.md, plan.md into context

**progress-tracker**
- Triggers when you complete tasks: "Done with X", "Finished Y"
- Asks before updating plan.md progress log and checking off items

**status-dashboard**
- Triggers when you ask: "What's next?", "Status?", "Show backlog"
- Displays formatted project status summary

**scope-guard**
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
3. **Keep everything organized** - One JSON file, one directory per feature
4. **Track status in data** - No file moves, just JSON field updates

## License

MIT
