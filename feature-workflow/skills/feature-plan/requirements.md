# Phase 2: Requirements Deep Dive

## Contents

- [Effort-Based Scaling](#effort-based-scaling)
- [Step 2a: Legacy Code Analysis](#step-2a-legacy-code-analysis-if-modifying-existing-code)
- [Step 2b: Requirements Analysis](#step-2b-requirements-analysis)

---

First, create the feature directory:
```bash
mkdir -p docs/planning/features/[feature-id]
```

## Effort-Based Scaling

The workflow adapts based on the effort level from backlog.json:

| Effort | Analysis Depth | Design Scope |
|--------|----------------|--------------|
| **Low** (< 8 hours) | Brief, essentials only | Skip design.md if simple |
| **Medium** (1-2 weeks) | Standard analysis | Full design workflow |
| **Large** (2+ weeks) | Comprehensive | Full design with extra detail |

**All agent prompts include effort context** so they self-regulate their output depth.

---

## Step 2a: Legacy Code Analysis (If Modifying Existing Code)

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
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Quick scan of affected files. Key dependencies only.
- Medium: Standard analysis depth.
- Large: Comprehensive deep-dive with full documentation.

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

---

## Step 2b: Requirements Analysis

**AGENT**: `feature-workflow:project-manager`

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
**Effort Level**: [effort]
Problem Statement: [problemStatement]
Affected Areas: [affectedAreas]

**Scaling guidance**:
- Low: Brief requirements. 2-3 user stories max. Key risks only.
- Medium: Standard requirements document.
- Large: Comprehensive requirements with full stakeholder analysis.

Create:
1. Detailed problem statement with user context
2. User stories with acceptance criteria
3. Technical requirements and constraints
4. Dependencies and prerequisites
5. Success metrics
6. Risks and mitigation strategies
7. Implementation task breakdown

Review existing architecture in docs/ to understand current patterns.
Output a requirements document scaled to the effort level.
"
```

**Save output to**: `docs/planning/features/[feature-id]/requirements.md`

**Output**: Comprehensive requirements document saved
