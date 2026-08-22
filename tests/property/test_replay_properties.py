from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from rci.claims import BoundArgument, Obligation, ObligationKind, Scope
from rci.core import (
    ArtifactRef,
    AttemptKey,
    CancelledOutcome,
    DomainCommand,
    DomainEvent,
    EffectAttemptPlan,
    EffectRequest,
    InquiryContext,
    OpenObligation,
    PlanEffectAttempt,
    PlanReason,
    PlanStatus,
    RecordAttemptOutcome,
    RecordStepPlan,
    RequestEffect,
    RouteSnapshot,
    StartEffectAttempt,
    StartInquiry,
    build_step_plan,
    decide,
    evolve,
    initial_state,
    replay,
)
from rci.core.effects import CancellationReason
from rci.core.serialization import encode_event

BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def ref(character: str) -> ArtifactRef:
    return ArtifactRef(digest=character * 64, size=1)


def context() -> InquiryContext:
    return InquiryContext(
        binding_revision="binding-1",
        carrier_schema_ids=("carrier-1",),
        relation_schema_ids=("relation-1",),
        consequence_profile_id="consequence-1",
        protected_horizon_id="horizon-1",
        scope_id="scope-1",
        scope_fingerprint=inquiry_scope().fingerprint,
        catalog_manifest_digest="2" * 64,
        scheduler_policy_version="scheduler-1",
        warrant_policy_version="warrant-1",
        provenance_refs=("test",),
    )


def inquiry_scope() -> Scope:
    return Scope(id="scope-1", binding_revision="binding-1")


@given(st.integers(min_value=0, max_value=12))
def test_replay_is_deterministic_for_retry_histories(attempt_count: int) -> None:
    state = initial_state()
    events: list[DomainEvent] = []
    obligation = Obligation(
        id="obligation-property",
        kind=ObligationKind.CHARACTERIZE,
        carrier_id="carrier-property",
        args=(BoundArgument(name="target", value="carrier-property"),),
        scope=inquiry_scope(),
        binding_revision="binding-1",
    )
    step_plan = build_step_plan(
        input_fingerprint="3" * 64,
        policy_version="scheduler-1",
        status=PlanStatus.READY,
        selected_obligation_id=obligation.id,
        selected_attempt_key=AttemptKey(
            obligation_fingerprint=obligation.fingerprint,
            contract_id="contract-property",
            contract_version="1",
            binding_revision=obligation.binding_revision,
        ),
        reason=PlanReason.DETERMINISTIC_PRIORITY,
        remaining_budget=99,
    )

    commands: tuple[DomainCommand, ...] = (
        StartInquiry(
            event_id="event-start",
            inquiry_id="inquiry-property",
            occurred_at=BASE_TIME,
            manifest_artifact=ref("0"),
            policy_version="policy-1",
            context=context(),
        ),
        OpenObligation(
            event_id="event-obligation",
            inquiry_id="inquiry-property",
            occurred_at=BASE_TIME,
            obligation=obligation,
        ),
        RecordStepPlan(
            event_id="event-step-plan",
            inquiry_id="inquiry-property",
            occurred_at=BASE_TIME,
            plan=step_plan,
        ),
        RequestEffect(
            event_id="event-request",
            inquiry_id="inquiry-property",
            occurred_at=BASE_TIME,
            request=EffectRequest(
                id="request-1",
                step_plan_id=step_plan.id,
                effect_kind="probe",
                adapter_id="adapter-1",
                input_artifact=ref("a"),
            ),
        ),
    )
    for command in commands:
        decided = decide(state, command)
        events.extend(decided)
        for event in decided:
            state = evolve(state, event)

    for index in range(attempt_count):
        route = RouteSnapshot(
            id=f"route-{index}",
            definition_id="route-definition",
            definition_version="1.0",
            definition_artifact=ref("b"),
            backend_id="backend-1",
            adapter_id="adapter-1",
            adapter_version="1.0",
            execution_environment_artifact=ref("c"),
            request_or_action_digest=format(index, "064x"),
        )
        plan = EffectAttemptPlan(
            id=f"attempt-{index}",
            request_id="request-1",
            route=route,
        )
        pair = (
            PlanEffectAttempt(
                event_id=f"event-plan-{index}",
                inquiry_id="inquiry-property",
                occurred_at=BASE_TIME + timedelta(seconds=index + 1),
                plan=plan,
            ),
            StartEffectAttempt(
                event_id=f"event-start-attempt-{index}",
                inquiry_id="inquiry-property",
                occurred_at=BASE_TIME + timedelta(seconds=index + 1),
                attempt_id=plan.id,
            ),
            RecordAttemptOutcome(
                event_id=f"event-outcome-{index}",
                inquiry_id="inquiry-property",
                occurred_at=BASE_TIME + timedelta(seconds=index + 1),
                request_id="request-1",
                outcome=CancelledOutcome(
                    attempt_id=plan.id,
                    route_id=route.id,
                    reason_kind=CancellationReason.CALLER_CANCELLED,
                ),
            ),
        )
        for command in pair:
            decided = decide(state, command)
            events.extend(decided)
            for event in decided:
                state = evolve(state, event)

    assert replay(events) == state
    assert replay(tuple(events)) == replay(tuple(events))
    assert tuple(encode_event(event) for event in events) == tuple(
        encode_event(event) for event in events
    )
