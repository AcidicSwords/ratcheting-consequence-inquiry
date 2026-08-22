import pytest
from pydantic import ValidationError

from rci.claims.models import Obligation, ObligationKind, ObligationStatus, Scope
from rci.orchestration.scheduler import (
    AttemptKey,
    ObligationEntry,
    PlanReason,
    PlanStatus,
    StepPlan,
    plan_next,
)


def _scope() -> Scope:
    return Scope(id="scope", binding_revision="binding-v1")


def _obligation(identifier: str, kind: ObligationKind, priority: int) -> Obligation:
    return Obligation(
        id=identifier,
        kind=kind,
        carrier_id="carrier",
        args=(),
        scope=_scope(),
        binding_revision="binding-v1",
        priority_vector=(priority,),
    )


def _entry(
    obligation: Obligation,
    *,
    creation_sequence: int,
    contract_id: str = "obligation-characterization",
) -> ObligationEntry:
    return ObligationEntry(
        obligation=obligation,
        attempt_key=AttemptKey(
            obligation_fingerprint=obligation.fingerprint,
            contract_id=contract_id,
            contract_version="1.0.0",
            binding_revision=obligation.binding_revision,
        ),
        creation_sequence=creation_sequence,
    )


def test_conflict_safety_precedes_ordinary_priority() -> None:
    ordinary = _entry(
        _obligation("ordinary", ObligationKind.CHARACTERIZE, 999), creation_sequence=1
    )
    conflict = _entry(
        _obligation("conflict", ObligationKind.LOCALIZE_CONFLICT, 1), creation_sequence=2
    )
    plan = plan_next((ordinary, conflict))
    assert plan.status is PlanStatus.READY
    assert plan.selected_obligation_id == "conflict"
    assert plan.selected_attempt_key == conflict.attempt_key
    assert plan == plan_next((conflict, ordinary))
    assert plan.id.startswith("step-plan:")


def test_budget_exhaustion_is_unknown_not_impossibility() -> None:
    plan = plan_next((), steps_used=100)
    assert plan.status is PlanStatus.UNKNOWN
    assert plan.reason is PlanReason.STEP_BUDGET_EXHAUSTED


def test_ready_plan_reserves_its_exact_atomic_event_batch_cost() -> None:
    entry = _entry(
        _obligation("ordinary", ObligationKind.CHARACTERIZE, 1),
        creation_sequence=1,
    )
    final_fitting = plan_next((entry,), steps_used=96, ready_event_cost=4)
    assert final_fitting.status is PlanStatus.READY
    assert final_fitting.remaining_budget == 0

    would_overshoot = plan_next((entry,), steps_used=97, ready_event_cost=4)
    assert would_overshoot.status is PlanStatus.UNKNOWN
    assert would_overshoot.reason is PlanReason.INSUFFICIENT_EVENT_BUDGET
    assert would_overshoot.remaining_budget == 3


@pytest.mark.parametrize(
    "status",
    (ObligationStatus.BLOCKED, ObligationStatus.UNKNOWN, ObligationStatus.IMPOSSIBLE),
)
def test_non_satisfied_non_open_obligation_is_unknown(status: ObligationStatus) -> None:
    obligation = _obligation("ordinary", ObligationKind.CHARACTERIZE, 1).model_copy(
        update={"status": status}
    )
    plan = plan_next((_entry(obligation, creation_sequence=1),))

    assert plan.status is PlanStatus.UNKNOWN
    assert plan.reason is PlanReason.UNRESOLVED_NONOPEN_OBLIGATION


def test_attempt_budget_is_scoped_to_contract_and_binding_tuple() -> None:
    obligation = _obligation("ordinary", ObligationKind.CHARACTERIZE, 1)
    first_contract = _entry(obligation, creation_sequence=1, contract_id="contract-a")
    exhausted = plan_next(
        (first_contract,),
        attempt_counts={first_contract.attempt_key: 3},
    )
    assert exhausted.status is PlanStatus.UNKNOWN
    assert exhausted.reason == "dependencies_or_attempt_budget_exhausted"

    alternate_contract = _entry(obligation, creation_sequence=1, contract_id="contract-b")
    alternate = plan_next(
        (alternate_contract,),
        attempt_counts={first_contract.attempt_key: 3},
    )
    assert alternate.status is PlanStatus.READY
    assert alternate.selected_obligation_id == obligation.id
    assert alternate.selected_attempt_key == alternate_contract.attempt_key


def test_step_plan_identity_covers_input_policy_and_exact_attempt_key() -> None:
    obligation = _obligation("ordinary", ObligationKind.CHARACTERIZE, 1)
    entry = _entry(obligation, creation_sequence=1)
    plan = plan_next((entry,), policy_version="scheduler-policy-1")

    assert plan.policy_version == "scheduler-policy-1"
    assert plan.selected_attempt_key == entry.attempt_key
    assert (
        plan.id
        != plan_next(
            (entry,),
            policy_version="scheduler-policy-2",
        ).id
    )
    assert (
        plan.id
        != plan_next(
            (entry,),
            attempt_counts={entry.attempt_key: 1},
            policy_version="scheduler-policy-1",
        ).id
    )

    forged = plan.model_dump()
    forged["id"] = "step-plan:forged"
    with pytest.raises(ValidationError, match="complete deterministic content"):
        StepPlan.model_validate(forged, strict=True)
