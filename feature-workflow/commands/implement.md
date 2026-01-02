---
name: implement
description: Start implementing a feature from the JSON backlog with adaptive agent dispatch
version: 1.2.0
argument-hint: "[feature-id-from-backlog]"
---

# Implement Feature Command

You are executing the **IMPLEMENT FEATURE** workflow - a comprehensive feature kickoff process that ensures proper planning before any implementation begins.

## Feature Target
$ARGUMENTS

If no specific feature ID was provided above, you will help the user select from the backlog.

## File Organization

All feature artifacts are stored in a single location:

```
docs/planning/
├── backlog.json                    # Single source of truth (status, metadata)
└── features/
    └── [feature-id]/               # One directory per feature
        ├── plan.md                 # Implementation plan
        ├── requirements.md         # Detailed requirements
        └── design.md               # System design (if applicable)
```

**Key Principles**:
- `backlog.json` tracks ALL items and their status (backlog → in-progress → completed)
- Files are created once in `features/[id]/` and never move
- Status changes update the JSON, not file locations

---

## Workflow Overview

This command orchestrates an 8-phase workflow:

1. **Feature Selection** - Choose from backlog or validate provided ID
2. **Requirements Analysis** - Deep dive with project-manager agent
3. **System Design** - Architecture planning (adaptive based on feature type)
4. **Implementation Planning** - Create detailed plan document
5. **Documentation Preparation** - Prepare docs with documentation-agent
6. **Backlog Status Update** - Update status to "in-progress" in JSON
7. **Environment Verification** - Ensure local setup is ready
8. **Kickoff Summary** - Create todos and provide clear next steps

---

## Phase 1: Feature Selection

### Read Backlog
Read `docs/planning/backlog.json` to get the current backlog.

### If Feature ID Provided ($ARGUMENTS not empty)
1. Find item in `items` array where `id` matches the argument
2. If not found:
   - List available items with status "backlog"
   - Ask user to select one
3. If found, confirm:
   ```
   Ready to start: [name]
   Priority: [priority] | Effort: [effort] | Impact: [impact]

   Problem: [problemStatement]

   Proceed? (yes/no)
   ```

### If No Feature ID Provided
1. Filter items where `status === "backlog"`
2. Display organized by priority:
   ```
   ## Available Backlog Items

   ### P0 (High Priority)
   - [id]: [name] - [effort] effort, [impact] impact

   ### P1 (Medium Priority)
   - [id]: [name] - [effort] effort, [impact] impact

   ### P2 (Low Priority)
   - [id]: [name] - [effort] effort, [impact] impact
   ```
3. Ask user to select by ID

**Output**: Selected feature with full details

---

## Phase 2: Requirements Deep Dive

First, create the feature directory:
```bash
mkdir -p docs/planning/features/[feature-id]
```

### Step 2a: Legacy Code Analysis (If Modifying Existing Code)

**AGENT**: `epcc-workflow:code-archaeologist` (OPTIONAL)

If the feature modifies existing, undocumented code, launch the code-archaeologist agent FIRST:

```
Launch Task tool with:
subagent_type: "epcc-workflow:code-archaeologist"
description: "Analyze existing code before modification"
prompt: "
Analyze the existing code that will be modified for this feature:

Feature: [name]
Affected Areas: [affectedAreas from backlog item]

Tasks:
1. Find and map the existing code in affected areas
2. Trace data flows through the code
3. Identify hidden dependencies
4. Document business logic embedded in code
5. Identify technical debt and risks
6. Create a safe modification strategy

Output: Archaeological report with:
- Dependency graph
- Data flow analysis
- Business logic documentation
- Risk assessment for modifications
"
```

**When to use**:
- Feature affects existing code with poor documentation
- Touching legacy systems
- Modifying code you didn't write
- `affectedAreas` references existing components

**Skip if**: Greenfield feature with no existing code dependencies

### Step 2b: Requirements Analysis

**AGENT**: `epcc-workflow:project-manager`

Launch the project-manager agent:

```
Launch Task tool with:
subagent_type: "feature-workflow:project-manager"
description: "Analyze feature requirements"
prompt: "
Analyze this feature from our backlog and create detailed requirements:

Feature ID: [id]
Feature Name: [name]
Type: [type]
Priority: [priority]
Problem Statement: [problemStatement]
Affected Areas: [affectedAreas]

Create:
1. Detailed problem statement with user context
2. User stories with acceptance criteria
3. Technical requirements and constraints
4. Dependencies and prerequisites
5. Success metrics
6. Risks and mitigation strategies
7. Implementation task breakdown

Review existing architecture in docs/ to understand current patterns.
Output a comprehensive requirements document.
"
```

**Save output to**: `docs/planning/features/[feature-id]/requirements.md`

**Output**: Comprehensive requirements document saved

---

## Phase 3: System Design (Adaptive)

**CONCEPT**: Detect feature type and dispatch appropriate specialized agents.

### Step 1: Classify Feature Type

Analyze the requirements to determine feature type:

- **Type A: Backend-Only** - API/Lambda changes, no UI
- **Type B: Frontend-Only** - UI components, no new API
- **Type C: Full-Stack** - New UI + New API + Integration
- **Type D: UI-Heavy Full-Stack** - Complex UI interactions + API
- **Type E: Infrastructure** - Deployment, monitoring, performance

**Classification Logic**:
```
Look for keywords in requirements:
- UI keywords: 'UI', 'component', 'page', 'frontend', 'interface', 'React'
- API keywords: 'API', 'Lambda', 'endpoint', 'GraphQL', 'backend', 'database'
- Infrastructure keywords: 'deployment', 'monitoring', 'infrastructure', 'performance'

has_ui = any UI keyword found
has_api = any API keyword found
has_infra = any infrastructure keyword found

if has_infra: Type E
elif has_ui and has_api and (UI keyword count > 10): Type D
elif has_ui and has_api: Type C
elif has_ui: Type B
elif has_api: Type A
else: Type C (default to full-stack)
```

### Step 2: Dispatch Appropriate Agents

#### Type A: Backend-Only
Launch single agent: **feature-workflow:api-designer**

```
Design the API layer for [feature name]:

Requirements: docs/planning/features/[feature-id]/requirements.md

Deliverables:
1. GraphQL schema updates (types, queries, mutations)
2. Lambda function specifications (input, output, errors)
3. Data flow diagram: Frontend -> API -> Storage -> Response
4. Authorization design (who can access, permission checks)

Output: API design document with all contracts clearly defined.
```

#### Type B: Frontend-Only
Launch IN PARALLEL: **feature-workflow:ux-optimizer** + **feature-workflow:frontend-architect**

**UX-Optimizer**:
```
Analyze user flows and optimize UX for [feature name]:

Requirements: docs/planning/features/[feature-id]/requirements.md

Deliverables:
1. User journey analysis with pain points
2. Interaction pattern recommendations
3. Accessibility audit (WCAG compliance)
4. Performance impact assessment

Output: UX optimization recommendations.
```

**Frontend-Architect**:
```
Design React component architecture for [feature name]:

Requirements: docs/planning/features/[feature-id]/requirements.md

Deliverables:
1. Component hierarchy diagram
2. TypeScript props interfaces for each component
3. State management strategy (local vs Context vs global)
4. Integration points (where components plug into existing UI)

Output: Frontend architecture document with component tree and interfaces.
```

#### Type C: Full-Stack (MOST COMMON)
Launch IN PARALLEL: **feature-workflow:api-designer** + **feature-workflow:frontend-architect** + **feature-workflow:integration-designer**

**API-Designer**: [Same as Type A]

**Frontend-Architect**: [Same as Type B]

**Integration-Designer**:
```
Design integration layer for [feature name]:

Requirements: docs/planning/features/[feature-id]/requirements.md

Deliverables:
1. GraphQL query usage in components
2. Loading/error state handling
3. Authorization flow (JWT tokens)
4. Caching strategy
5. Error handling and retry logic

Output: Integration design document.
```

#### Type D: UI-Heavy Full-Stack
Two-phase approach:
- Phase 3a: Run **feature-workflow:ux-optimizer** for detailed UX requirements
- Phase 3b: Launch Type C agents with UX input

#### Type E: Infrastructure
Launch single agent: **feature-workflow:system-designer**

```
Design the system architecture for this feature:

Feature: [name]
Requirements: docs/planning/features/[feature-id]/requirements.md

Create:
1. Component diagram showing new/modified components
2. Data flow diagrams
3. Scalability and fault tolerance patterns
4. Monitoring and operational considerations

Output: System design document.
```

### Step 3: Save Design Documents

**Save combined output to**: `docs/planning/features/[feature-id]/design.md`

If no system design was needed (simple feature), skip creating design.md.

**Output**: Comprehensive design document saved (if applicable)

---

## Phase 4: Implementation Plan & Test Specifications

### Step 4a: Test-First Planning (TDD)

**AGENT**: `epcc-workflow:test-generator`

Launch the test-generator agent to create test specifications BEFORE implementation:

```
Launch Task tool with:
subagent_type: "epcc-workflow:test-generator"
description: "Create test specifications for feature"
prompt: "
Create comprehensive test specifications for this feature:

Feature: [name]
Requirements: docs/planning/features/[feature-id]/requirements.md
Design: docs/planning/features/[feature-id]/design.md (if exists)

Tasks:
1. Review requirements and acceptance criteria
2. Create test specifications using TDD approach:
   - Unit tests for each new function/method
   - Integration tests for component interactions
   - Edge cases and boundary conditions
   - Error handling scenarios

Output test specs with:
- Test file locations (where tests should be created)
- Test case names with descriptions
- AAA structure (Arrange, Act, Assert)
- Expected inputs and outputs
- Mocking strategy for dependencies

Target: 90%+ code coverage for new code

These specs will guide implementation - code should be written to make these tests pass.
"
```

**Output**: Test specifications to guide implementation

### Step 4b: Implementation Plan Creation

Create file: `docs/planning/features/[feature-id]/plan.md`

Use this template:

```markdown
# [Feature Name]

**Status**: In Progress
**Priority**: [priority]
**Effort**: [effort]
**Started**: [YYYY-MM-DD]
**Backlog ID**: [id]

## Problem Statement
[From requirements.md - why we're building this]

## Requirements
[Summary from requirements.md - key acceptance criteria]

## System Design
[Summary from design.md, or "No architecture changes required"]

## Implementation Steps
- [ ] Step 1: [Specific, actionable task with file references]
- [ ] Step 2: [Specific, actionable task with file references]
- [ ] Step 3: [Continue with all steps...]

Each step should:
- Be concrete and testable
- Reference specific files or components
- Be completable in 1-4 hours ideally

## Testing Strategy

### Unit Tests
- [What needs unit testing]
- [Coverage targets]

### Integration Tests
- [What needs integration testing]
- [Test scenarios]

### Manual Testing Checklist
- [ ] Test scenario 1
- [ ] Test scenario 2
- [ ] Test scenario 3

## Documentation Updates Needed
- [ ] Update [doc file 1] - [what needs updating]
- [ ] Update [doc file 2] - [what needs updating]

## Dependencies
- [Any prerequisite work]
- [Any external dependencies]

## Risks/Unknowns
- **Risk**: [Description]
  - **Mitigation**: [How to address]

## Progress Log
### [Today's Date]
- Created implementation plan
- Next: [First implementation step]
```

Write this file using the Write tool.

**Output**: Implementation plan file created at `docs/planning/features/[feature-id]/plan.md`

---

## Phase 5: Documentation Preparation

**AGENT**: `feature-workflow:documentation-agent`

Launch documentation-agent:

```
Launch Task tool with:
subagent_type: "feature-workflow:documentation-agent"
description: "Prepare documentation structure"
prompt: "
Prepare documentation for this new feature:

Feature: [name]
Feature Directory: docs/planning/features/[feature-id]/
Implementation Plan: docs/planning/features/[feature-id]/plan.md
Requirements: docs/planning/features/[feature-id]/requirements.md

Tasks:
1. Review the implementation plan and requirements thoroughly
2. Identify ALL documentation files that will need updates based on:
   - New components being added
   - Modified behavior in existing components
   - Architecture changes
   - New integrations
3. For each affected doc:
   - Add a <!-- TODO: [feature-id] - [what needs updating] --> comment
   - Create placeholder sections if needed
4. If new components are being created:
   - Determine where documentation should live
   - Create stub documentation files
5. Update docs/README.md navigation if new docs are added

Create a documentation checklist and add it to the implementation plan.
"
```

**Output**: Documentation structure prepared with TODOs

---

## Phase 6: Backlog Status Update

1. **Read** `docs/planning/backlog.json`

2. **Find and update the item**:
   ```json
   {
     "status": "in-progress",
     "updatedAt": "[current ISO timestamp]",
     "startedAt": "[current ISO timestamp]",
     "implementationPlan": "docs/planning/features/[feature-id]/plan.md"
   }
   ```

3. **Recalculate summary**:
   - Decrement `byStatus.backlog`
   - Increment `byStatus.in-progress`
   - Update `lastUpdated`

4. **Write** updated JSON back to `docs/planning/backlog.json`

5. **Stage changes**:
   ```bash
   git add docs/planning/backlog.json
   git add docs/planning/features/[feature-id]/
   ```

**Output**: Backlog JSON updated, feature files staged

---

## Phase 7: Environment Verification

1. **Check project setup**:
   ```bash
   # Check if common tools exist
   node --version 2>/dev/null || echo "Node.js not found"
   npm --version 2>/dev/null || echo "npm not found"
   ```

2. **Install dependencies** (if package.json exists):
   ```bash
   npm install
   ```

3. **Run type check** (if available):
   ```bash
   npm run type-check 2>/dev/null || echo "No type-check script"
   ```

4. **Note any pre-commit hooks** the project uses

**Output**: Environment verified

---

## Phase 8: Kickoff Summary & Todo Creation

1. **Create TodoWrite list** with implementation steps from the plan

2. **Display comprehensive summary**:

```markdown
# Feature Development Kickoff Complete

## Feature: [Name]
**ID**: [id]
**Priority**: [priority]

---

## Feature Files Created:
- `docs/planning/features/[feature-id]/requirements.md` - Detailed requirements
- `docs/planning/features/[feature-id]/design.md` - System design [if applicable]
- `docs/planning/features/[feature-id]/plan.md` - Implementation plan

---

## What's Ready:
- Requirements analyzed with detailed acceptance criteria
- System design completed [or "No architecture changes needed"]
- Implementation plan created with [N] actionable steps
- Documentation structure prepared
- Backlog status updated to "in-progress"
- Local environment verified

---

## Next Steps:

### 1. Review Your Plan
Read: docs/planning/features/[feature-id]/plan.md

### 2. Start First Implementation Step
Task: [First step description]
Files: [Affected files]

### 3. Development Workflow
- Update progress in plan.md as you work
- Run tests frequently
- Before committing: ensure tests pass

---

## Key Files:
- **Feature Directory**: docs/planning/features/[feature-id]/
- **Backlog**: docs/planning/backlog.json

---

Ready to start coding!
```

**Output**: Complete kickoff summary with clear next steps

---

## Completing a Feature

When the feature is done, use the `/feature-workflow:complete` command:

```
/feature-workflow:complete [feature-id]
```

This runs quality gates before marking the feature complete:
1. **Security Review** - Scans for vulnerabilities (OWASP Top 10, CVEs)
2. **QA Validation** - Verifies test coverage and acceptance criteria
3. **Final Verification** - Runs tests, type checks, and build
4. **Status Update** - Updates backlog.json to "completed"

The complete workflow ensures no feature ships without passing security and quality standards.

**Files stay in place** - `docs/planning/features/[feature-id]/` remains as a permanent record

---

## Error Handling

- **Backlog not found**: Create empty backlog.json and inform user
- **Feature not found**: List available items, ask to select
- **Agent errors**: Retry with more context or continue without that design phase
- **Directory missing**: Create `docs/planning/features/` if needed

---

## Philosophy: "Never Code Without a Plan"

By completing these 8 phases, you ensure:
- Requirements are clearly understood
- Architecture is properly designed
- Implementation is broken into manageable steps
- Documentation will stay current
- Testing is considered upfront
- Risks are identified and mitigated

---

**Let's get started!**
