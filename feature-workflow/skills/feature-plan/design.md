# Phase 3: System Design (Adaptive)

## Contents

- [Step 1: Classify Feature Type](#step-1-classify-feature-type)
- [Step 2: Dispatch Appropriate Agents](#step-2-dispatch-appropriate-agents)
- [Step 3: Save Design Documents](#step-3-save-design-documents)

---

**CONCEPT**: Detect feature type and dispatch appropriate specialized agents.

## Step 1: Classify Feature Type

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

---

## Step 2: Dispatch Appropriate Agents

### Type A: Backend-Only

Launch single agent: **feature-workflow:api-designer**

```
Design the API layer for [feature name]:

Requirements: docs/features/[feature-id]/requirements.md
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Schema changes only. Brief function specs.
- Medium: Standard API design.
- Large: Comprehensive design with full error handling.

Deliverables:
1. GraphQL schema updates (types, queries, mutations)
2. Lambda function specifications (input, output, errors)
3. Data flow diagram: Frontend -> API -> Storage -> Response
4. Authorization design (who can access, permission checks)

Output: API design document scaled to effort level.
```

### Type B: Frontend-Only

Launch IN PARALLEL: **feature-workflow:ux-optimizer** + **feature-workflow:frontend-architect**

**UX-Optimizer**:
```
Analyze user flows and optimize UX for [feature name]:

Requirements: docs/features/[feature-id]/requirements.md
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Key UX considerations only.
- Medium: Standard UX analysis.
- Large: Full journey mapping with accessibility audit.

Deliverables:
1. User journey analysis with pain points
2. Interaction pattern recommendations
3. Accessibility audit (WCAG compliance)
4. Performance impact assessment

Output: UX recommendations scaled to effort level.
```

**Frontend-Architect**:
```
Design React component architecture for [feature name]:

Requirements: docs/features/[feature-id]/requirements.md
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Component list with key props only.
- Medium: Standard component architecture.
- Large: Full hierarchy with detailed interfaces.

Deliverables:
1. Component hierarchy diagram
2. TypeScript props interfaces for each component
3. State management strategy (local vs Context vs global)
4. Integration points (where components plug into existing UI)

Output: Frontend architecture scaled to effort level.
```

### Type C: Full-Stack (MOST COMMON)

Launch IN PARALLEL: **feature-workflow:api-designer** + **feature-workflow:frontend-architect** + **feature-workflow:integration-designer**

**API-Designer**: [Same as Type A]

**Frontend-Architect**: [Same as Type B]

**Integration-Designer**:
```
Design integration layer for [feature name]:

Requirements: docs/features/[feature-id]/requirements.md
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Query usage only. Basic error handling.
- Medium: Standard integration patterns.
- Large: Full caching and retry strategies.

Deliverables:
1. GraphQL query usage in components
2. Loading/error state handling
3. Authorization flow (JWT tokens)
4. Caching strategy
5. Error handling and retry logic

Output: Integration design scaled to effort level.
```

### Type D: UI-Heavy Full-Stack

Two-phase approach:
- Phase 3a: Run **feature-workflow:ux-optimizer** for detailed UX requirements
- Phase 3b: Launch Type C agents with UX input

### Type E: Infrastructure

Launch single agent: **feature-workflow:system-designer**

```
Design the system architecture for this feature:

Feature: [name]
Requirements: docs/features/[feature-id]/requirements.md
**Effort Level**: [effort]

**Scaling guidance**:
- Low: Component changes only. Brief diagram.
- Medium: Standard system design.
- Large: Full architecture with scaling patterns.

Create:
1. Component diagram showing new/modified components
2. Data flow diagrams
3. Scalability and fault tolerance patterns
4. Monitoring and operational considerations

Output: System design scaled to effort level.
```

---

## Step 3: Save Design Documents

**Save combined output to**: `docs/features/[feature-id]/design.md`

If no system design was needed (simple feature), skip creating design.md.

**Output**: Comprehensive design document saved (if applicable)
