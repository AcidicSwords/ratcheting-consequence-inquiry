from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from rci.claims import (
    BoundArgument,
    Obligation,
    ObligationDisposition,
    ObligationKind,
    ObligationStatus,
    Scope,
)
from rci.core import (
    AcceptEffectResult,
    ArtifactRef,
    AttemptKey,
    CapturedPayload,
    Decoded,
    DomainCommand,
    DomainEvent,
    EffectAttemptPlan,
    EffectRequest,
    ExternalReturn,
    InquiryContext,
    InquiryState,
    NoAttemptDisposition,
    OpenObligation,
    PlanEffectAttempt,
    PlanReason,
    PlanStatus,
    RecordAttemptOutcome,
    RecordDecodeOutcome,
    RecordNoAttemptDisposition,
    RecordObligationDisposition,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
    RouteSnapshot,
    StartEffectAttempt,
    StartInquiry,
    TransformEvidence,
    UnknownResult,
    build_step_plan,
    decide,
    evolve,
    initial_state,
)
from rci.core.effects import NoAttemptReason
from rci.core.errors import EffectLifecycleError, InvalidCommandError
from rci.core.serialization import decode_event, encode_event

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def ref(character: str, size: int = 1) -> ArtifactRef:
    return ArtifactRef(digest=character * 64, size=size)


def route() -> RouteSnapshot:
    return RouteSnapshot(
        id="route-1",
        definition_id="route-definition-1",
        definition_version="1.0",
        definition_artifact=ref("a"),
        backend_id="backend-1",
        adapter_id="adapter-1",
        adapter_version="1.0",
        execution_environment_artifact=ref("b"),
        request_or_action_digest="e" * 64,
        transform_evidence=(
            TransformEvidence(
                id="transform-1",
                version="1.0",
                input_artifact=ref("c"),
                output_artifact=ref("d"),
            ),
        ),
    )


def inquiry_scope() -> Scope:
    return Scope(id="scope-1", binding_revision="binding-1")


def inquiry_context() -> InquiryContext:
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


def apply(
    state: InquiryState,
    command: DomainCommand,
) -> tuple[InquiryState, tuple[DomainEvent, ...]]:
    events = decide(state, command)
    for event in events:
        state = evolve(state, event)
    return state, events


def started_state() -> InquiryState:
    state, _ = apply(
        initial_state(),
        StartInquiry(
            event_id="event-start",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            manifest_artifact=ref("0"),
            policy_version="policy-1",
            context=inquiry_context(),
        ),
    )
    obligation = Obligation(
        id="obligation-1",
        kind=ObligationKind.CHARACTERIZE,
        carrier_id="carrier-1",
        args=(BoundArgument(name="target", value="carrier-1"),),
        scope=inquiry_scope(),
        binding_revision="binding-1",
    )
    state, _ = apply(
        state,
        OpenObligation(
            event_id="event-obligation",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            obligation=obligation,
        ),
    )
    step_plan = build_step_plan(
        input_fingerprint="3" * 64,
        policy_version="scheduler-1",
        status=PlanStatus.READY,
        selected_obligation_id=obligation.id,
        selected_attempt_key=AttemptKey(
            obligation_fingerprint=obligation.fingerprint,
            contract_id="contract-1",
            contract_version="1",
            binding_revision=obligation.binding_revision,
        ),
        reason=PlanReason.DETERMINISTIC_PRIORITY,
        remaining_budget=99,
    )
    state, plan_events = apply(
        state,
        RecordStepPlan(
            event_id="event-step-plan",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            plan=step_plan,
        ),
    )
    assert decode_event(encode_event(plan_events[0])) == plan_events[0]
    return state


def test_models_are_strict_frozen_and_reducers_generate_nothing() -> None:
    command = StartInquiry(
        event_id="event-start",
        inquiry_id="inquiry-1",
        occurred_at=NOW,
        manifest_artifact=ref("0"),
        policy_version="policy-1",
        context=inquiry_context(),
    )
    event = decide(initial_state(), command)[0]
    assert event.event_id == command.event_id
    assert event.occurred_at == command.occurred_at

    state = evolve(initial_state(), event)
    with pytest.raises(ValidationError):
        state.sequence = 99  # type: ignore[misc]
    with pytest.raises(ValidationError):
        EffectRequest(
            id="request-1",
            step_plan_id="step-plan-1",
            effect_kind="probe",
            adapter_id="adapter-1",
            input_artifact=ref("a"),
            timeout_seconds="60",  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        StartInquiry(
            event_id="event-bad-time",
            inquiry_id="inquiry-2",
            occurred_at=datetime(2026, 1, 1),
            manifest_artifact=ref("0"),
            policy_version="policy-1",
            context=inquiry_context(),
        )


def test_effect_attempt_return_decode_and_accept_cardinalities() -> None:
    state = started_state()
    request = EffectRequest(
        id="request-1",
        step_plan_id=state.step_plans[0].id,
        effect_kind="probe",
        adapter_id="adapter-1",
        input_artifact=ref("e"),
    )
    state, _ = apply(
        state,
        RequestEffect(
            event_id="event-request",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            request=request,
        ),
    )
    plan = EffectAttemptPlan(id="attempt-1", request_id=request.id, route=route())
    state, _ = apply(
        state,
        PlanEffectAttempt(
            event_id="event-plan",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            plan=plan,
        ),
    )
    state, _ = apply(
        state,
        StartEffectAttempt(
            event_id="event-start-attempt",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            attempt_id=plan.id,
        ),
    )

    returned = ReturnedOutcome(
        attempt_id=plan.id,
        route_id=plan.route.id,
        external_return=ExternalReturn(
            id="return-1",
            attempt_id=plan.id,
            route_id=plan.route.id,
            capture_boundary="test-native-null",
            capture_encoding="native-null",
            captured_at=NOW,
            raw_payload=CapturedPayload(kind="null"),
        ),
    )
    outcome_command = RecordAttemptOutcome(
        event_id="event-return",
        inquiry_id="inquiry-1",
        occurred_at=NOW,
        request_id=request.id,
        outcome=returned,
    )
    state, _ = apply(state, outcome_command)
    assert decide(state, outcome_command) == ()

    decoded = Decoded(
        id="decode-1",
        external_return_id="return-1",
        decoder_id="decoder-1",
        decoder_version="1.0",
        result=UnknownResult(
            id="result-1",
            semantic_artifact=ref("f"),
            reason_kind="backend_unknown",
        ),
    )
    state, _ = apply(
        state,
        RecordDecodeOutcome(
            event_id="event-decode",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            request_id=request.id,
            outcome=decoded,
        ),
    )
    accept = AcceptEffectResult(
        event_id="event-accept",
        inquiry_id="inquiry-1",
        occurred_at=NOW,
        request_id=request.id,
        decoded_outcome_id=decoded.id,
    )
    state, _ = apply(state, accept)
    persisted = state.request_by_id(request.id)
    assert persisted is not None
    assert persisted.accepted_result == decoded.result
    assert decide(state, accept) == ()

    with pytest.raises(EffectLifecycleError, match="at most one"):
        decide(
            state,
            AcceptEffectResult(
                event_id="event-accept-other",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                request_id=request.id,
                decoded_outcome_id="decode-other",
            ),
        )
    with pytest.raises(EffectLifecycleError, match="resolved"):
        decide(
            state,
            PlanEffectAttempt(
                event_id="event-plan-late",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                plan=EffectAttemptPlan(
                    id="attempt-2",
                    request_id=request.id,
                    route=route().model_copy(update={"id": "route-2"}),
                ),
            ),
        )

    unrelated = Obligation(
        id="obligation-unrelated",
        kind=ObligationKind.CHARACTERIZE,
        carrier_id="carrier-unrelated",
        args=(BoundArgument(name="target", value="carrier-unrelated"),),
        scope=inquiry_scope(),
        binding_revision="binding-1",
    )
    state, _ = apply(
        state,
        OpenObligation(
            event_id="event-obligation-unrelated",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            obligation=unrelated,
        ),
    )
    with pytest.raises(EffectLifecycleError, match="persisted step plan"):
        decide(
            state,
            RequestEffect(
                event_id="event-request-without-owned-plan",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                request=EffectRequest(
                    id="request-without-owned-plan",
                    step_plan_id="step-plan:missing",
                    effect_kind="backlog.local_append",
                    adapter_id="local-ledger",
                    input_artifact=ref("9"),
                ),
            ),
        )
    with pytest.raises(InvalidCommandError, match="exact obligation"):
        decide(
            state,
            RecordObligationDisposition(
                event_id="event-forged-satisfaction",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                disposition=ObligationDisposition(
                    id="disposition-forged-satisfaction",
                    obligation_id=unrelated.id,
                    status=ObligationStatus.SATISFIED,
                    reason="reuse accepted return from another plan",
                    evidence_refs=(decoded.id,),
                ),
            ),
        )
    state, _ = apply(
        state,
        RecordObligationDisposition(
            event_id="event-exact-satisfaction",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            disposition=ObligationDisposition(
                id="disposition-exact-satisfaction",
                obligation_id="obligation-1",
                status=ObligationStatus.SATISFIED,
                reason="accepted return from the selected plan",
                evidence_refs=(decoded.id,),
            ),
        ),
    )
    assert state.current_obligation_status("obligation-1") is ObligationStatus.SATISFIED


def test_no_attempt_disposition_is_distinct_from_returned_null() -> None:
    state = started_state()
    request = EffectRequest(
        id="request-1",
        step_plan_id=state.step_plans[0].id,
        effect_kind="probe",
        adapter_id="adapter-1",
        input_artifact=ref("e"),
    )
    state, _ = apply(
        state,
        RequestEffect(
            event_id="event-request",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            request=request,
        ),
    )
    with pytest.raises(EffectLifecycleError, match="persisted step plan"):
        decide(
            state,
            RecordNoAttemptDisposition(
                event_id="event-forged-plan-disposition",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                disposition=NoAttemptDisposition(
                    id="disposition-forged-plan",
                    request_id=request.id,
                    step_plan_id="step-plan-other",
                    reason_kind=NoAttemptReason.POLICY_DENIED,
                ),
            ),
        )
    state, events = apply(
        state,
        RecordNoAttemptDisposition(
            event_id="event-no-attempt",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            disposition=NoAttemptDisposition(
                id="disposition-1",
                request_id=request.id,
                step_plan_id=request.step_plan_id,
                reason_kind=NoAttemptReason.POLICY_DENIED,
            ),
        ),
    )
    assert events[0].kind == "effect_no_attempt_disposition_recorded"
    persisted = state.request_by_id(request.id)
    assert persisted is not None
    assert len(persisted.no_attempt_dispositions) == 1
    assert persisted.attempts == ()


def test_acceptance_requires_a_recorded_successful_decode() -> None:
    state = started_state()
    request = EffectRequest(
        id="request-1",
        step_plan_id=state.step_plans[0].id,
        effect_kind="probe",
        adapter_id="adapter-1",
        input_artifact=ref("e"),
    )
    state, _ = apply(
        state,
        RequestEffect(
            event_id="event-request",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            request=request,
        ),
    )
    with pytest.raises(EffectLifecycleError, match="successful Decoded"):
        decide(
            state,
            AcceptEffectResult(
                event_id="event-accept",
                inquiry_id="inquiry-1",
                occurred_at=NOW,
                request_id=request.id,
                decoded_outcome_id="decode-missing",
            ),
        )
