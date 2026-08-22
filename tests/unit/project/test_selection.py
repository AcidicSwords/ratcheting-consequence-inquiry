from __future__ import annotations

from itertools import permutations

from rci.project import (
    CapabilitySuccessorCandidate,
    ProjectCost,
    ProjectGainKind,
    SuccessorKind,
    candidate_dominates,
    derive_capability_frontier,
)


def _candidate(
    identity: str, *, gains: tuple[ProjectGainKind, ...], cost: int | None
) -> CapabilitySuccessorCandidate:
    return CapabilitySuccessorCandidate(
        id=identity,
        anchor_id="anchor",
        limitation_id="limitation",
        kind=SuccessorKind.METHOD_REPERTOIRE,
        current_state="current",
        desired_state="desired",
        preserved_capability_ids=("sealed",),
        gain_kinds=gains,
        discriminator_id=f"disc-{identity}",
        evidence_mechanism_ids=("test",),
        estimated_costs=(ProjectCost(axis="steps", value=cost),),
        reversible=True,
    )


def test_dominance_requires_exact_comparable_costs_and_strict_gain() -> None:
    weak = _candidate("weak", gains=(ProjectGainKind.NEW_METHOD,), cost=5)
    strong = _candidate(
        "strong",
        gains=(ProjectGainKind.INDEPENDENT_CHECKABILITY, ProjectGainKind.NEW_METHOD),
        cost=4,
    )
    unknown = _candidate("unknown", gains=strong.gain_kinds, cost=None)
    assert candidate_dominates(strong, weak)
    assert not candidate_dominates(weak, strong)
    assert not candidate_dominates(strong, unknown)
    assert not candidate_dominates(unknown, strong)


def test_frontier_is_stable_across_all_input_permutations() -> None:
    candidates = (
        _candidate("a", gains=(ProjectGainKind.NEW_METHOD,), cost=4),
        _candidate("b", gains=(ProjectGainKind.NEW_SEPARATOR,), cost=2),
        _candidate("c", gains=(ProjectGainKind.REPAIRED_FAILURE,), cost=None),
    )
    expected = derive_capability_frontier(frontier_id="frontier", candidates=candidates)
    for ordering in permutations(candidates):
        assert derive_capability_frontier(frontier_id="frontier", candidates=ordering) == expected


def test_incomparable_or_unknown_cost_axes_do_not_become_a_scalar_ranking() -> None:
    left = _candidate("left", gains=(ProjectGainKind.NEW_METHOD,), cost=1).model_copy(
        update={
            "estimated_costs": (
                ProjectCost(axis="risk", value=1),
                ProjectCost(axis="steps", value=10),
            )
        }
    )
    right = _candidate("right", gains=(ProjectGainKind.NEW_SEPARATOR,), cost=1).model_copy(
        update={
            "estimated_costs": (
                ProjectCost(axis="risk", value=5),
                ProjectCost(axis="steps", value=5),
            )
        }
    )
    incomparable = derive_capability_frontier(
        frontier_id="incomparable-costs", candidates=(left, right)
    )
    assert incomparable.status == "unknown"
    assert incomparable.selected_discriminator_candidate_id is None

    unknown = _candidate("unknown", gains=(ProjectGainKind.REPAIRED_FAILURE,), cost=None)
    unresolved = derive_capability_frontier(frontier_id="unknown-cost", candidates=(left, unknown))
    assert unresolved.status == "unknown"
