"""Dependency-graph utilities for features.

Cycle detection, blocked-by computation, and unknown-ref validation.
Pure functions over dicts of FeatureContext — no I/O.
"""

# Handle both package and standalone imports
try:
    from .models import FeatureContext, FeatureStatus
except ImportError:
    from models import FeatureContext, FeatureStatus


def detect_cycles(features: dict[str, FeatureContext]) -> list[list[str]]:
    """Return a list of cycles in the dependsOn graph.

    Each cycle is the list of feature IDs forming it (one direction).
    Self-loops are returned as single-element lists.
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: list[str] = []
    on_stack: set[str] = set()

    def dfs(node: str) -> None:
        if node in on_stack:
            # Cycle found — slice from where we first saw it
            cycle_start = stack.index(node)
            cycle = stack[cycle_start:]
            # Normalize: rotate so smallest ID is first, for stable comparison
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            if normalized not in cycles:
                cycles.append(normalized)
            return
        if node in visited:
            return
        visited.add(node)
        stack.append(node)
        on_stack.add(node)
        ctx = features.get(node)
        if ctx:
            for dep in ctx.depends_on:
                if dep in features:
                    dfs(dep)
        stack.pop()
        on_stack.discard(node)

    for fid in features:
        if fid not in visited:
            dfs(fid)

    return cycles


def compute_blocked_by(feature_id: str, features: dict[str, FeatureContext]) -> list[str]:
    """Return feature IDs that are blocked because `feature_id` is one of their unmet dependencies.

    `feature_id` blocks another feature B if:
    - B.depends_on contains feature_id, AND
    - feature_id is not completed (still active backlog/in-progress, paused, or tombstoned)

    Note: tombstoned features (replaced/abandoned) STILL block by design — they aren't shipped.
    Use /feature-state to surface the dependent and update its dependsOn.
    """
    ctx = features.get(feature_id)
    if ctx is None:
        return []
    if ctx.status == FeatureStatus.COMPLETED:
        return []
    blocked: list[str] = []
    for other_id, other in features.items():
        if feature_id in other.depends_on:
            blocked.append(other_id)
    return sorted(blocked)


def find_unknown_refs(features: dict[str, FeatureContext]) -> list[tuple[str, str, str]]:
    """Find references to feature IDs that don't exist in the corpus.

    Returns list of (referring_feature_id, field_name, missing_ref) tuples.
    Fields checked: dependsOn, relatedTo, epic, children, replacedBy, replaces.
    """
    known = set(features.keys())
    missing: list[tuple[str, str, str]] = []
    for fid, ctx in features.items():
        for ref in ctx.depends_on:
            if ref not in known:
                missing.append((fid, "dependsOn", ref))
        for ref in ctx.related_to:
            if ref not in known:
                missing.append((fid, "relatedTo", ref))
        if ctx.epic and ctx.epic not in known:
            missing.append((fid, "epic", ctx.epic))
        for ref in ctx.children:
            if ref not in known:
                missing.append((fid, "children", ref))
        if ctx.replaced_by and ctx.replaced_by not in known:
            missing.append((fid, "replacedBy", ctx.replaced_by))
        for ref in ctx.replaces:
            if ref not in known:
                missing.append((fid, "replaces", ref))
    return missing


def compute_dispatch_waves(epic_id: str, features: dict[str, FeatureContext]) -> list[list[str]]:
    """Compute the dispatch order for an epic's children, grouped into parallel-safe waves.

    Each wave is a list of child IDs that can be dispatched in parallel because none of
    them depend on another member of the same wave. Waves are emitted in topological order:
    wave N's members may depend on members of waves [0, N-1] but not on each other.

    Filters applied before topo-sort:
    - The target must exist and be `type: Epic`
    - Children that don't exist in `features` are skipped (silently — dashboard validation flags them)
    - Children that are already `COMPLETED` are excluded (their dependents are unblocked)
    - Children with state `PAUSED`, `REPLACED`, or `ABANDONED` are excluded

    Order within a wave: the epic's `children:` array order is preserved (NOT alphabetical).
    Dependencies are restricted to the epic's own dispatchable children — `dependsOn:` entries
    referring to features outside the epic are ignored (assumed already handled separately).
    """
    epic = features.get(epic_id)
    if epic is None or not epic.is_epic():
        return []

    # Build the dispatchable set: existing children that aren't already done/tombstoned/paused
    dispatchable: dict[str, FeatureContext] = {}
    for child_id in epic.children:
        child = features.get(child_id)
        if child is None:
            continue
        if child.status == FeatureStatus.COMPLETED:
            continue
        if child.is_tombstone() or child.is_paused():
            continue
        dispatchable[child_id] = child

    if not dispatchable:
        return []

    # Build the in-epic dependency graph (deps outside the dispatchable set don't count)
    deps_in_epic: dict[str, set[str]] = {
        child_id: {d for d in child.depends_on if d in dispatchable}
        for child_id, child in dispatchable.items()
    }

    # Topo-sort into waves. Each iteration emits a wave of nodes with no remaining in-wave deps.
    children_order = {cid: idx for idx, cid in enumerate(epic.children)}
    waves: list[list[str]] = []
    remaining = set(dispatchable.keys())

    while remaining:
        ready = [cid for cid in remaining if not (deps_in_epic[cid] & remaining)]
        if not ready:
            # Cycle in the epic's deps — bail with what we have rather than infinite-loop
            break
        # Order within the wave by the epic's children: array
        ready.sort(key=lambda cid: children_order.get(cid, 1_000_000))
        waves.append(ready)
        remaining -= set(ready)

    return waves
