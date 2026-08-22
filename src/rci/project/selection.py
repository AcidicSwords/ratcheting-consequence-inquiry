"""Pure deterministic selection for project successor frontiers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from rci.project.models import CapabilityFrontier, CapabilitySuccessorCandidate


def candidate_dominates(
    left: CapabilitySuccessorCandidate, right: CapabilitySuccessorCandidate
) -> bool:
    """Return true only for an exact, comparable, strict partial-order improvement."""

    if (left.anchor_id, left.limitation_id) != (right.anchor_id, right.limitation_id):
        return False
    left_costs = {item.axis: item.value for item in left.estimated_costs}
    right_costs = {item.axis: item.value for item in right.estimated_costs}
    if left_costs.keys() != right_costs.keys() or any(
        value is None for value in (*left_costs.values(), *right_costs.values())
    ):
        return False
    preservation = set(left.preserved_capability_ids) >= set(right.preserved_capability_ids)
    gains = set(left.gain_kinds) >= set(right.gain_kinds)
    cost_no_worse = all(
        cast(int, left_costs[axis]) <= cast(int, right_costs[axis]) for axis in left_costs
    )
    strict = (
        set(left.preserved_capability_ids) > set(right.preserved_capability_ids)
        or set(left.gain_kinds) > set(right.gain_kinds)
        or any(cast(int, left_costs[axis]) < cast(int, right_costs[axis]) for axis in left_costs)
    )
    return preservation and gains and cost_no_worse and strict


def derive_capability_frontier(
    *,
    frontier_id: str,
    candidates: Iterable[CapabilitySuccessorCandidate],
) -> CapabilityFrontier:
    """Build a permutation-stable frontier and select the smallest discriminator first."""

    ordered = tuple(sorted(candidates, key=lambda item: item.id))
    if not ordered:
        raise ValueError("a capability frontier requires candidates")
    anchor_id = ordered[0].anchor_id
    limitation_id = ordered[0].limitation_id
    if any((item.anchor_id, item.limitation_id) != (anchor_id, limitation_id) for item in ordered):
        raise ValueError("frontier candidates must share an exact anchor and limitation")
    if len({item.id for item in ordered}) != len(ordered):
        raise ValueError("frontier candidate identities must be unique")
    nondominated = tuple(
        item
        for item in ordered
        if not any(candidate_dominates(other, item) for other in ordered if other.id != item.id)
    )
    incomparable: list[tuple[str, str]] = []
    for index, left in enumerate(nondominated):
        for right in nondominated[index + 1 :]:
            if not candidate_dominates(left, right) and not candidate_dominates(right, left):
                incomparable.append((left.id, right.id))
    selectable = tuple(
        item for item in nondominated if item.reversible and item.discriminator_id is not None
    )
    cost_maps = {
        item.id: {cost.axis: cost.value for cost in item.estimated_costs} for item in selectable
    }
    comparable = bool(selectable) and not any(
        value is None for costs in cost_maps.values() for value in costs.values()
    )
    if comparable:
        axes = {frozenset(costs) for costs in cost_maps.values()}
        comparable = len(axes) == 1
    cost_minima = (
        tuple(
            item
            for item in selectable
            if all(
                all(
                    cast(int, cost_maps[item.id][axis]) <= cast(int, cost_maps[other.id][axis])
                    for axis in cost_maps[item.id]
                )
                for other in selectable
            )
        )
        if comparable
        else ()
    )
    selected = min(cost_minima, key=lambda item: item.id) if cost_minima else None
    return CapabilityFrontier(
        id=frontier_id,
        anchor_id=anchor_id,
        limitation_id=limitation_id,
        candidate_ids=tuple(item.id for item in ordered),
        nondominated_candidate_ids=tuple(item.id for item in nondominated),
        incomparable_pairs=tuple(incomparable),
        selected_discriminator_candidate_id=selected.id if selected else None,
        status="ready" if selected else "unknown",
    )
