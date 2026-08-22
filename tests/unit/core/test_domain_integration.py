from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from rci.claims import (
    BoundArgument,
    Claim,
    ClaimRole,
    Correction,
    CorrectionKind,
    GuardChange,
    GuardStanding,
    ObligationDisposition,
    ObligationStatus,
    Polarity,
    Provenance,
    Scope,
)
from rci.core import (
    AcceptEffectResult,
    AdmitClaim,
    AdmitProbe,
    AppendCorrection,
    ArtifactRef,
    AttemptKey,
    CapturedPayload,
    ChangeGuardStanding,
    ChangeNogoodStanding,
    ChangeSupportRouteStanding,
    CommitSemanticDelta,
    Decoded,
    DomainCommand,
    DomainEvent,
    EffectAttemptPlan,
    EffectRequest,
    EvaluateWarrant,
    ExternalReturn,
    InquiryContext,
    InquiryState,
    PlanEffectAttempt,
    PlanReason,
    PlanStatus,
    PromoteClaim,
    RecordAttemptOutcome,
    RecordCheckerVerdict,
    RecordCognitivePlan,
    RecordDecodeOutcome,
    RecordEvidence,
    RecordMismatch,
    RecordNogood,
    RecordObligationDisposition,
    RecordProbeObservation,
    RecordReconstruction,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
    RouteSnapshot,
    SealPrediction,
    StartEffectAttempt,
    StartInquiry,
    StepPlan,
    SuccessResult,
    build_step_plan,
    decide,
    evolve,
    initial_state,
)
from rci.core.errors import EffectLifecycleError, InvalidCommandError, InvalidTransitionError
from rci.core.events import LemmaPromoted
from rci.core.serialization import decode_event, encode_event
from rci.persistence import SQLiteEventStore
from rci.probes import (
    CognitiveAttemptPlan,
    ComparabilityBridge,
    Mismatch,
    PredictionSeal,
    ProbeEvent,
    ProbeIdentity,
    Reconstruction,
    SemanticChangeOperation,
    SemanticDelta,
    WarrantedChange,
)
from rci.warrant import (
    Applicability,
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    EvidenceKind,
    Nogood,
    NogoodStandingChange,
    PropositionKind,
    SupportEnvironment,
    SupportRoute,
    SupportRouteStandingChange,
    SupportStanding,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def ref(character: str, *, size: int = 1) -> ArtifactRef:
    return ArtifactRef(digest=character * 64, size=size)


def scope() -> Scope:
    return Scope(
        id="scope-1",
        binding_revision="binding-1",
        assumption_ids=("assumption:a", "assumption:b"),
        applicability_guard_id="guard-1",
    )


def context(current_scope: Scope) -> InquiryContext:
    return InquiryContext(
        binding_revision=current_scope.binding_revision,
        carrier_schema_ids=("carrier-1",),
        relation_schema_ids=("relation-1",),
        consequence_profile_id="consequence-1",
        protected_horizon_id="horizon-1",
        admissible_operation_ids=("observe",),
        discharge_mechanism_ids=("independent-witness",),
        scope_id=current_scope.id,
        scope_fingerprint=current_scope.fingerprint,
        assumption_ids=current_scope.assumption_ids,
        guard_condition_id="guard-1",
        guard_ast=ref("a"),
        catalog_manifest_digest="b" * 64,
        scheduler_policy_version="scheduler-1",
        warrant_policy_version="warrant-1",
        provenance_refs=("test",),
    )


def apply(
    state: InquiryState,
    command: DomainCommand,
    recorded_events: list[DomainEvent] | None = None,
) -> tuple[InquiryState, DomainEvent]:
    events = decide(state, command)
    assert len(events) == 1
    if recorded_events is not None:
        recorded_events.extend(events)
    return evolve(state, events[0]), events[0]


def started(recorded_events: list[DomainEvent] | None = None) -> InquiryState:
    current_scope = scope()
    state, _ = apply(
        initial_state(),
        StartInquiry(
            event_id="event-start",
            inquiry_id="inquiry-1",
            occurred_at=NOW,
            manifest_artifact=ref("0"),
            policy_version="policy-1",
            context=context(current_scope),
        ),
        recorded_events,
    )
    return state


def claim(
    identifier: str,
    *,
    role: ClaimRole = ClaimRole.OBSERVATION,
    polarity: Polarity = Polarity.UNSPECIFIED,
    proposition_id: str | None = None,
    payload: object = "opaque",
) -> Claim:
    return Claim(
        id=identifier,
        role=role,
        bound_args=(BoundArgument(name="subject", value="lamp"),),
        payload=payload,  # type: ignore[arg-type]
        scope=scope(),
        provenance=Provenance(kind="test", source_id="fixture"),
        proposition_id=proposition_id,
        polarity=polarity,
    )


def command_metadata(identifier: str) -> dict[str, object]:
    return {
        "event_id": identifier,
        "inquiry_id": "inquiry-1",
        "occurred_at": NOW,
    }


def record_scheduler_plan(
    state: InquiryState,
    obligation_id: str,
    *,
    label: str,
) -> tuple[InquiryState, StepPlan]:
    obligation = state.obligation_by_id(obligation_id)
    assert obligation is not None
    plan = build_step_plan(
        input_fingerprint=sha256(label.encode()).hexdigest(),
        policy_version="scheduler-1",
        status=PlanStatus.READY,
        selected_obligation_id=obligation.id,
        selected_attempt_key=AttemptKey(
            obligation_fingerprint=obligation.fingerprint,
            contract_id="test-contract",
            contract_version="1",
            binding_revision=obligation.binding_revision,
        ),
        reason=PlanReason.DETERMINISTIC_PRIORITY,
        remaining_budget=99,
    )
    state, _ = apply(
        state,
        RecordStepPlan(
            **command_metadata(f"event-step-plan-{label}"),  # type: ignore[arg-type]
            plan=plan,
        ),
    )
    return state, plan


def stand_guard(
    state: InquiryState, recorded_events: list[DomainEvent] | None = None
) -> InquiryState:
    state, _ = apply(
        state,
        ChangeGuardStanding(
            **command_metadata("event-guard-standing"),  # type: ignore[arg-type]
            change=GuardChange(
                id="guard-change-1",
                condition_id="guard-1",
                scope_fingerprint=scope().fingerprint,
                standing=GuardStanding.STANDING,
                reason="checked fixture context",
            ),
        ),
        recorded_events,
    )
    return state


def promote_semantic_change(
    state: InquiryState,
    source_claim: Claim,
    recorded_events: list[DomainEvent] | None = None,
) -> InquiryState:
    relation_id = "relation-semantic-change"
    evidence = Evidence(
        id="evidence-1",
        kind=EvidenceKind.INDEPENDENT_WITNESS,
        proposition_id=relation_id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=scope().fingerprint,
        artifact=ref("1"),
    )
    checker_verdict = CheckerVerdictRecord(
        id="checker-verdict-1",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=relation_id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=scope().fingerprint,
        checker_id="independent-witness",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=ref("2"),
        certificate_artifact=ref("3"),
    )
    environment_evidence = Evidence(
        id="evidence-environment-1",
        kind=EvidenceKind.INDEPENDENT_WITNESS,
        proposition_id="environment-1",
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=scope().fingerprint,
        artifact=ref("4"),
    )
    environment_verdict = CheckerVerdictRecord(
        id="checker-verdict-environment-1",
        evidence_id=environment_evidence.id,
        evidence_artifact=environment_evidence.artifact,
        proposition_id=environment_evidence.proposition_id,
        proposition_kind=environment_evidence.proposition_kind,
        scope_fingerprint=environment_evidence.scope_fingerprint,
        checker_id="independent-witness",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=ref("5"),
        certificate_artifact=ref("6"),
    )
    alternate_environment_evidence = environment_evidence.model_copy(
        update={
            "id": "evidence-environment-2",
            "proposition_id": "environment-2",
            "artifact": ref("7"),
        }
    )
    alternate_environment_verdict = environment_verdict.model_copy(
        update={
            "id": "checker-verdict-environment-2",
            "evidence_id": alternate_environment_evidence.id,
            "evidence_artifact": alternate_environment_evidence.artifact,
            "proposition_id": alternate_environment_evidence.proposition_id,
            "verdict_artifact": ref("8"),
            "certificate_artifact": ref("9"),
        }
    )
    for index, evidence_record in enumerate(
        (evidence, environment_evidence, alternate_environment_evidence), start=1
    ):
        state, _ = apply(
            state,
            RecordEvidence(
                **command_metadata(f"event-evidence-{index}"),  # type: ignore[arg-type]
                evidence=evidence_record,
            ),
            recorded_events,
        )
    for index, verdict_record in enumerate(
        (checker_verdict, environment_verdict, alternate_environment_verdict), start=1
    ):
        state, _ = apply(
            state,
            RecordCheckerVerdict(
                **command_metadata(f"event-checker-verdict-{index}"),  # type: ignore[arg-type]
                checker_verdict=verdict_record,
            ),
            recorded_events,
        )
    state, _ = apply(
        state,
        EvaluateWarrant(
            **command_metadata("event-warrant"),  # type: ignore[arg-type]
            decision_id="warrant-decision-1",
            evidence_id=evidence.id,
            checker_verdict_id=checker_verdict.id,
            proposition_id=relation_id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope=scope(),
        ),
        recorded_events,
    )
    route = SupportRoute(
        id="support-route-1",
        conclusion_id="lemma-1",
        environment=SupportEnvironment(
            id="environment-1",
            scope_fingerprint=scope().fingerprint,
            binding_revision=scope().binding_revision,
            assumption_ids=("assumption:a",),
            finite_universe_hash=None,
            realizability_check=CheckReference(
                evidence_id=environment_evidence.id,
                checker_verdict_id=environment_verdict.id,
            ),
        ),
        required_dependency_ids=(),
        open_dependency_ids=(),
        certificate_check=CheckReference(
            evidence_id=evidence.id,
            checker_verdict_id=checker_verdict.id,
        ),
        warrant_refs=("warrant-decision-1",),
        provenance_refs=("test",),
    )
    alternate_route = route.model_copy(
        update={
            "id": "support-route-2",
            "environment": route.environment.model_copy(
                update={
                    "id": "environment-2",
                    "assumption_ids": ("assumption:b",),
                    "realizability_check": CheckReference(
                        evidence_id=alternate_environment_evidence.id,
                        checker_verdict_id=alternate_environment_verdict.id,
                    ),
                }
            ),
        }
    )
    state, _ = apply(
        state,
        PromoteClaim(
            **command_metadata("event-promote"),  # type: ignore[arg-type]
            promotion_id="promotion-1",
            lemma_id="lemma-1",
            relation_id=relation_id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope=scope(),
            applicability=Applicability(condition_id="guard-1"),
            support_routes=(route, alternate_route),
            warrant_decision_id="warrant-decision-1",
            provenance_refs=("test",),
            source_claim_ids=(source_claim.id,),
        ),
        recorded_events,
    )
    return state


def test_claim_admission_atomically_opens_attacks_and_localized_conflict() -> None:
    state = started()
    positive = claim(
        "claim-positive",
        role=ClaimRole.NECESSITY,
        polarity=Polarity.POSITIVE,
        proposition_id="lamp-on",
    )
    state, first_event = apply(
        state,
        AdmitClaim(**command_metadata("event-claim-positive"), claim=positive),  # type: ignore[arg-type]
    )
    assert len(first_event.derived_obligations) == 1  # type: ignore[union-attr]

    negative = claim(
        "claim-negative",
        role=ClaimRole.NECESSITY,
        polarity=Polarity.NEGATIVE,
        proposition_id="lamp-on",
    )
    state_before = state
    state, second_event = apply(
        state,
        AdmitClaim(**command_metadata("event-claim-negative"), claim=negative),  # type: ignore[arg-type]
    )
    assert {item.id for item in state.claims} == {positive.id, negative.id}
    assert len(state.conflicts) == 1
    assert {item.kind.value for item in state.obligations} == {
        "necessity_counterexample",
        "localize_conflict",
    }
    assert len(state.obligations) == 2

    malformed = second_event.model_copy(update={"derived_obligations": ()})
    with pytest.raises(InvalidTransitionError, match="lawful command consequence"):
        evolve(state_before, malformed)


def test_nested_payloads_are_snapshot_immutable() -> None:
    original = {"outer": [1, {"answer": False}]}
    record = claim("claim-json", payload=original)
    fingerprint = record.model_dump_json()
    original["outer"].append("later")
    assert record.model_dump_json() == fingerprint
    assert isinstance(record.payload, dict)
    nested = record.payload["outer"]
    assert isinstance(nested, list)
    with pytest.raises(TypeError, match="frozen JSON"):
        nested.append("forbidden")
    event = decide(
        started(),
        AdmitClaim(
            **command_metadata("event-json-roundtrip"),  # type: ignore[arg-type]
            claim=record,
        ),
    )[0]
    decoded_event = decode_event(encode_event(event))
    assert decoded_event == event
    decoded_payload = decoded_event.claim.payload  # type: ignore[union-attr]
    assert isinstance(decoded_payload, dict)
    with pytest.raises(TypeError, match="frozen JSON"):
        decoded_payload["late"] = True


def test_every_correction_kind_appends_succession_without_erasing_predecessors() -> None:
    state = started()
    predecessors = (
        claim("claim-predecessor"),
        claim("claim-successor"),
        claim("claim-other-source"),
    )
    for index, predecessor in enumerate(predecessors):
        state, _ = apply(
            state,
            AdmitClaim(
                **command_metadata(f"event-correction-source-{index}"),  # type: ignore[arg-type]
                claim=predecessor,
            ),
        )
    original_claims = state.claims

    recorded: list[Correction] = []
    for index, kind in enumerate(CorrectionKind):
        related_ids = (
            ("claim-successor", "claim-other-source")
            if kind is CorrectionKind.MERGES_FROM
            else ("claim-successor",)
        )
        correction = Correction(
            id=f"correction-{kind.value}",
            kind=kind,
            target_id="claim-predecessor",
            related_ids=related_ids,
            scope=scope(),
            provenance=Provenance(kind="test-correction", source_id=f"fixture-{index}"),
        )
        state, event = apply(
            state,
            AppendCorrection(
                **command_metadata(f"event-correction-{index}"),  # type: ignore[arg-type]
                correction=correction,
            ),
        )
        assert decode_event(encode_event(event)) == event
        recorded.append(correction)

    assert state.claims == original_claims
    assert state.corrections == tuple(recorded)
    assert state.claim_by_id("claim-predecessor") == predecessors[0]
    assert all(
        state.claim_by_id(reference) is not None
        for correction in state.corrections
        for reference in (correction.target_id, *correction.related_ids)
    )


def test_same_binding_but_different_scope_cannot_enter_the_aggregate() -> None:
    state = started()
    out_of_scope = claim("claim-out-of-scope").model_copy(
        update={"scope": scope().model_copy(update={"id": "scope-2"})}
    )
    with pytest.raises(InvalidCommandError, match="scope does not match"):
        decide(
            state,
            AdmitClaim(
                **command_metadata("event-out-of-scope"),  # type: ignore[arg-type]
                claim=out_of_scope,
            ),
        )


def test_evidence_check_warrant_and_promotion_are_separate_owned_stages() -> None:
    state = started()
    evidence = Evidence(
        id="evidence-stage",
        kind=EvidenceKind.INDEPENDENT_WITNESS,
        proposition_id="relation-stage",
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=scope().fingerprint,
        artifact=ref("1"),
    )
    with pytest.raises(InvalidCommandError, match="recorded evidence and check"):
        decide(
            state,
            EvaluateWarrant(
                **command_metadata("event-warrant-too-early"),  # type: ignore[arg-type]
                decision_id="decision-too-early",
                evidence_id=evidence.id,
                checker_verdict_id="check-missing",
                proposition_id=evidence.proposition_id,
                proposition_kind=evidence.proposition_kind,
                scope=scope(),
            ),
        )

    state, evidence_event = apply(
        state,
        RecordEvidence(
            **command_metadata("event-evidence-stage"),  # type: ignore[arg-type]
            evidence=evidence,
        ),
    )
    assert decode_event(encode_event(evidence_event)) == evidence_event
    forged = CheckerVerdictRecord(
        id="check-forged-artifact",
        evidence_id=evidence.id,
        evidence_artifact=ref("2"),
        proposition_id=evidence.proposition_id,
        proposition_kind=evidence.proposition_kind,
        scope_fingerprint=evidence.scope_fingerprint,
        checker_id="independent-witness",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=ref("3"),
        certificate_artifact=ref("4"),
    )
    with pytest.raises(InvalidCommandError, match="exact evidence"):
        decide(
            state,
            RecordCheckerVerdict(
                **command_metadata("event-forged-check"),  # type: ignore[arg-type]
                checker_verdict=forged,
            ),
        )

    unauthorized = forged.model_copy(
        update={
            "id": "check-unauthorized",
            "evidence_artifact": evidence.artifact,
            "checker_id": "self-reported-adapter",
        }
    )
    state, checker_event = apply(
        state,
        RecordCheckerVerdict(
            **command_metadata("event-check-unauthorized"),  # type: ignore[arg-type]
            checker_verdict=unauthorized,
        ),
    )
    assert decode_event(encode_event(checker_event)) == checker_event
    state, decision_event = apply(
        state,
        EvaluateWarrant(
            **command_metadata("event-decision-unauthorized"),  # type: ignore[arg-type]
            decision_id="decision-unauthorized",
            evidence_id=evidence.id,
            checker_verdict_id=unauthorized.id,
            proposition_id=evidence.proposition_id,
            proposition_kind=evidence.proposition_kind,
            scope=scope(),
        ),
    )
    assert state.warrant_decisions[-1].warrant_class.value == "none"
    assert "not authorized" in state.warrant_decisions[-1].reason
    assert decode_event(encode_event(decision_event)) == decision_event

    valid = unauthorized.model_copy(
        update={"id": "check-authorized", "checker_id": "independent-witness"}
    )
    state, _ = apply(
        state,
        RecordCheckerVerdict(
            **command_metadata("event-check-authorized"),  # type: ignore[arg-type]
            checker_verdict=valid,
        ),
    )
    state, _ = apply(
        state,
        EvaluateWarrant(
            **command_metadata("event-decision-authorized"),  # type: ignore[arg-type]
            decision_id="decision-authorized",
            evidence_id=evidence.id,
            checker_verdict_id=valid.id,
            proposition_id=evidence.proposition_id,
            proposition_kind=evidence.proposition_kind,
            scope=scope(),
        ),
    )
    assert state.warrant_decisions[-1].warrant_class.value == "hard"


def test_guard_invalidation_deactivates_without_erasing_promotion_history() -> None:
    state = stand_guard(started())
    source = claim("claim-source", proposition_id="relation-semantic-change")
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-source"), claim=source),  # type: ignore[arg-type]
    )
    state = promote_semantic_change(state, source)
    active = state.active_theory
    assert tuple(item.lemma_version_id for item in active) == ("lemma-1",)
    assert state.claim_by_id(source.id) == source

    state, _ = apply(
        state,
        ChangeGuardStanding(
            **command_metadata("event-guard-invalid"),  # type: ignore[arg-type]
            change=GuardChange(
                id="guard-change-2",
                condition_id="guard-1",
                scope_fingerprint=scope().fingerprint,
                standing=GuardStanding.INVALIDATED,
                reason="guard no longer holds",
                predecessor_id="guard-change-1",
            ),
        ),
    )
    assert not state.active_theory
    assert len(state.lemma_versions) == len(state.lemma_supports) == 1
    assert len(state.guard_changes) == 2

    state, _ = apply(
        state,
        ChangeGuardStanding(
            **command_metadata("event-guard-reopen"),  # type: ignore[arg-type]
            change=GuardChange(
                id="guard-change-3",
                condition_id="guard-1",
                scope_fingerprint=scope().fingerprint,
                standing=GuardStanding.STANDING,
                reason="guard independently re-established",
                predecessor_id="guard-change-2",
            ),
        ),
    )
    assert _active_ids(state) == {"lemma-1"}
    assert len(state.guard_changes) == 3


def test_owned_nogood_and_route_standing_histories_deactivate_and_reopen() -> None:
    state = stand_guard(started())
    source = claim("claim-standing-source", proposition_id="relation-semantic-change")
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-standing-source"), claim=source),  # type: ignore[arg-type]
    )
    state = promote_semantic_change(state, source)
    assert state.active_theory[0].standing_support_route_id == "support-route-1"

    nogood_evidence = Evidence(
        id="evidence-nogood-a",
        kind=EvidenceKind.INDEPENDENT_WITNESS,
        proposition_id="nogood:a",
        proposition_kind=PropositionKind.EXISTENTIAL,
        scope_fingerprint=scope().fingerprint,
        artifact=ref("e"),
    )
    nogood_verdict = CheckerVerdictRecord(
        id="checker-nogood-a",
        evidence_id=nogood_evidence.id,
        evidence_artifact=nogood_evidence.artifact,
        proposition_id=nogood_evidence.proposition_id,
        proposition_kind=nogood_evidence.proposition_kind,
        scope_fingerprint=nogood_evidence.scope_fingerprint,
        checker_id="independent-witness",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=ref("f"),
        certificate_artifact=ref("d"),
    )
    state, _ = apply(
        state,
        RecordEvidence(
            **command_metadata("event-evidence-nogood-a"),  # type: ignore[arg-type]
            evidence=nogood_evidence,
        ),
    )
    state, _ = apply(
        state,
        RecordCheckerVerdict(
            **command_metadata("event-check-nogood-a"),  # type: ignore[arg-type]
            checker_verdict=nogood_verdict,
        ),
    )
    state, _ = apply(
        state,
        EvaluateWarrant(
            **command_metadata("event-warrant-nogood-a"),  # type: ignore[arg-type]
            decision_id="warrant-nogood-a",
            evidence_id=nogood_evidence.id,
            checker_verdict_id=nogood_verdict.id,
            proposition_id="nogood:a",
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope=scope(),
        ),
    )
    nogood = Nogood(
        id="nogood:a",
        scope_fingerprint=scope().fingerprint,
        binding_revision=scope().binding_revision,
        finite_universe_hash=scope().finite_universe_hash,
        policy_version="warrant-1",
        incompatible_assumption_ids=("assumption:a",),
        check=CheckReference(
            evidence_id=nogood_evidence.id,
            checker_verdict_id=nogood_verdict.id,
        ),
        warrant_decision_id="warrant-nogood-a",
        reason="checked witness shows assumption:a cannot stand in this environment",
    )
    state, _ = apply(
        state,
        RecordNogood(
            **command_metadata("event-nogood-a"),  # type: ignore[arg-type]
            nogood=nogood,
        ),
    )
    assert state.active_theory[0].standing_support_route_id == "support-route-2"

    state_before_bad_tail = state
    with pytest.raises(InvalidCommandError, match="exact tail"):
        decide(
            state,
            ChangeSupportRouteStanding(
                **command_metadata("event-route-bad-tail"),  # type: ignore[arg-type]
                change=SupportRouteStandingChange(
                    id="route-change-bad-tail",
                    support_route_id="support-route-2",
                    standing=SupportStanding.WITHDRAWN,
                    reason="bad predecessor must fail",
                    predecessor_id="missing-change",
                ),
            ),
        )
    assert state == state_before_bad_tail

    route_withdrawal = SupportRouteStandingChange(
        id="route-change-1",
        support_route_id="support-route-2",
        standing=SupportStanding.WITHDRAWN,
        reason="route certificate was independently suspended",
    )
    state, route_event = apply(
        state,
        ChangeSupportRouteStanding(
            **command_metadata("event-route-withdraw"),  # type: ignore[arg-type]
            change=route_withdrawal,
        ),
    )
    assert decode_event(encode_event(route_event)) == route_event
    assert not state.active_theory

    nogood_withdrawal = NogoodStandingChange(
        id="nogood-change-1",
        nogood_id=nogood.id,
        standing=SupportStanding.WITHDRAWN,
        reason="nogood witness was superseded by a checked rebinding",
    )
    state, _ = apply(
        state,
        ChangeNogoodStanding(
            **command_metadata("event-nogood-withdraw"),  # type: ignore[arg-type]
            change=nogood_withdrawal,
        ),
    )
    assert state.active_theory[0].standing_support_route_id == "support-route-1"

    state, _ = apply(
        state,
        ChangeSupportRouteStanding(
            **command_metadata("event-route-restore"),  # type: ignore[arg-type]
            change=SupportRouteStandingChange(
                id="route-change-2",
                support_route_id="support-route-2",
                standing=SupportStanding.STANDING,
                reason="route certificate was independently restored",
                predecessor_id=route_withdrawal.id,
            ),
        ),
    )
    state, _ = apply(
        state,
        ChangeNogoodStanding(
            **command_metadata("event-nogood-restore"),  # type: ignore[arg-type]
            change=NogoodStandingChange(
                id="nogood-change-2",
                nogood_id=nogood.id,
                standing=SupportStanding.STANDING,
                reason="nogood was independently re-established",
                predecessor_id=nogood_withdrawal.id,
            ),
        ),
    )
    assert state.active_theory[0].standing_support_route_id == "support-route-2"
    assert len(state.lemma_supports[0].support_routes) == 2
    assert len(state.support_route_standing_changes) == 2
    assert len(state.nogood_standing_changes) == 2
    assert state.claim_by_id(source.id) == source


def test_aggregate_rejects_support_and_ancestry_cycle_routes_without_events() -> None:
    state = stand_guard(started())
    source = claim("claim-cycle-source", proposition_id="relation-semantic-change")
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-cycle-source"), claim=source),  # type: ignore[arg-type]
    )
    state = promote_semantic_change(state, source)
    state_before = state
    existing_route = state.lemma_supports[0].support_routes[0]
    self_cycle_route = existing_route.model_copy(
        update={
            "id": "support-route-self-cycle",
            "conclusion_id": "lemma-self-cycle",
            "required_dependency_ids": ("lemma-self-cycle",),
            "open_dependency_ids": (),
        }
    )
    with pytest.raises(InvalidCommandError, match="cycle"):
        decide(
            state,
            PromoteClaim(
                **command_metadata("event-promote-self-cycle"),  # type: ignore[arg-type]
                promotion_id="promotion-self-cycle",
                lemma_id="lemma-self-cycle",
                relation_id="relation-semantic-change",
                proposition_kind=PropositionKind.EXISTENTIAL,
                scope=scope(),
                applicability=Applicability(condition_id="guard-1"),
                support_routes=(self_cycle_route,),
                warrant_decision_id="warrant-decision-1",
                provenance_refs=("test",),
                source_claim_ids=(source.id,),
            ),
        )
    assert state == state_before

    lawful_route = self_cycle_route.model_copy(
        update={"required_dependency_ids": (), "open_dependency_ids": ()}
    )
    with pytest.raises(InvalidCommandError, match="unknown lemma version"):
        decide(
            state,
            PromoteClaim(
                **command_metadata("event-promote-forward-ancestry"),  # type: ignore[arg-type]
                promotion_id="promotion-forward-ancestry",
                lemma_id="lemma-forward-ancestry",
                relation_id="relation-semantic-change",
                proposition_kind=PropositionKind.EXISTENTIAL,
                scope=scope(),
                applicability=Applicability(condition_id="guard-1"),
                support_routes=(lawful_route,),
                warrant_decision_id="warrant-decision-1",
                provenance_refs=("test",),
                source_claim_ids=(source.id,),
                predecessor_refs=("lemma-future",),
            ),
        )
    assert state == state_before


def test_sqlite_cycle_rejection_rolls_back_stream_and_export(tmp_path: Path) -> None:
    history: list[DomainEvent] = []
    state = stand_guard(started(history), history)
    source = claim("claim-sqlite-cycle", proposition_id="relation-semantic-change")
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-sqlite-cycle-source"), claim=source),  # type: ignore[arg-type]
        history,
    )
    state = promote_semantic_change(state, source, history)
    store = SQLiteEventStore(tmp_path / "state.sqlite3")
    sequence = store.append("inquiry-1", 0, history)
    exported_before = store.export_stream("inquiry-1")

    version = state.lemma_versions[0].model_copy(
        update={"id": "lemma-sqlite-self-cycle", "predecessor_refs": ()}
    )
    route = (
        state.lemma_supports[0]
        .support_routes[0]
        .model_copy(
            update={
                "id": "support-route-sqlite-self-cycle",
                "conclusion_id": version.id,
                "required_dependency_ids": (version.id,),
                "open_dependency_ids": (),
            }
        )
    )
    support = state.lemma_supports[0].model_copy(
        update={"lemma_version_id": version.id, "support_routes": (route,)}
    )
    link = state.promotion_links[0].model_copy(
        update={"id": "promotion-sqlite-self-cycle", "lemma_version_id": version.id}
    )
    cyclic_event = LemmaPromoted(
        event_id="event-sqlite-self-cycle",
        inquiry_id="inquiry-1",
        occurred_at=NOW,
        version=version,
        support=support,
        link=link,
    )
    with pytest.raises(InvalidTransitionError, match="cycle"):
        store.append("inquiry-1", sequence, (cyclic_event,))
    assert store.stream_version("inquiry-1") == sequence
    assert store.export_stream("inquiry-1") == exported_before

    forward_version = version.model_copy(
        update={"id": "lemma-sqlite-forward", "predecessor_refs": ("lemma-future",)}
    )
    forward_route = route.model_copy(
        update={
            "id": "support-route-sqlite-forward",
            "conclusion_id": forward_version.id,
            "required_dependency_ids": (),
        }
    )
    forward_event = cyclic_event.model_copy(
        update={
            "event_id": "event-sqlite-forward-ancestry",
            "version": forward_version,
            "support": support.model_copy(
                update={
                    "lemma_version_id": forward_version.id,
                    "support_routes": (forward_route,),
                }
            ),
            "link": link.model_copy(
                update={
                    "id": "promotion-sqlite-forward",
                    "lemma_version_id": forward_version.id,
                }
            ),
        }
    )
    with pytest.raises(InvalidTransitionError, match="unknown lemma version"):
        store.append("inquiry-1", sequence, (forward_event,))
    assert store.stream_version("inquiry-1") == sequence
    assert store.export_stream("inquiry-1") == exported_before


def test_modal_attack_closes_only_for_exact_active_hard_lemma() -> None:
    state = stand_guard(started())
    source = claim("claim-discharge-source", proposition_id="relation-semantic-change")
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-discharge-source"), claim=source),  # type: ignore[arg-type]
    )
    state = promote_semantic_change(state, source)
    exact_modal = claim(
        "claim-modal-exact",
        role=ClaimRole.NECESSITY,
        proposition_id="relation-semantic-change",
    )
    state, exact_event = apply(
        state,
        AdmitClaim(**command_metadata("event-modal-exact"), claim=exact_modal),  # type: ignore[arg-type]
    )
    assert not exact_event.derived_obligations  # type: ignore[union-attr]

    state, _ = apply(
        state,
        ChangeGuardStanding(
            **command_metadata("event-discharge-invalidated"),  # type: ignore[arg-type]
            change=GuardChange(
                id="guard-change-discharge-invalidated",
                condition_id="guard-1",
                scope_fingerprint=scope().fingerprint,
                standing=GuardStanding.INVALIDATED,
                reason="checked support no longer applies",
                predecessor_id="guard-change-1",
            ),
        ),
    )
    inactive_modal = claim(
        "claim-modal-after-invalidation",
        role=ClaimRole.NECESSITY,
        proposition_id="relation-semantic-change",
    )
    state, inactive_event = apply(
        state,
        AdmitClaim(
            **command_metadata("event-modal-after-invalidation"),  # type: ignore[arg-type]
            claim=inactive_modal,
        ),
    )
    assert len(inactive_event.derived_obligations) == 1  # type: ignore[union-attr]
    assert state.obligations[-1].carrier_id == "relation-semantic-change"


def _active_ids(state: InquiryState) -> set[str]:
    return {item.lemma_version_id for item in state.active_theory}


def test_effect_start_is_required_and_semantic_statuses_fail_closed() -> None:
    state = started()
    source = claim("claim-obligation", role=ClaimRole.NECESSITY)
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-obligation"), claim=source),  # type: ignore[arg-type]
    )
    obligation = state.obligations[0]
    with pytest.raises(InvalidCommandError, match="impossibility"):
        decide(
            state,
            RecordObligationDisposition(
                **command_metadata("event-impossible"),  # type: ignore[arg-type]
                disposition=ObligationDisposition(
                    id="disposition-impossible",
                    obligation_id=obligation.id,
                    status=ObligationStatus.IMPOSSIBLE,
                    reason="search timed out",
                ),
            ),
        )

    state, scheduler_plan = record_scheduler_plan(
        state,
        obligation.id,
        label="effect-start",
    )
    request = EffectRequest(
        id="request-1",
        step_plan_id=scheduler_plan.id,
        effect_kind="probe",
        adapter_id="adapter-1",
        input_artifact=ref("c"),
    )
    state, _ = apply(
        state,
        RequestEffect(**command_metadata("event-request"), request=request),  # type: ignore[arg-type]
    )
    plan = EffectAttemptPlan(
        id="attempt-1",
        request_id=request.id,
        route=RouteSnapshot(
            id="route-1",
            definition_id="route-definition-1",
            definition_version="1",
            definition_artifact=ref("d"),
            backend_id="backend-1",
            adapter_id="adapter-1",
            adapter_version="1",
            execution_environment_artifact=ref("8"),
            request_or_action_digest="7" * 64,
        ),
    )
    state, _ = apply(
        state,
        PlanEffectAttempt(**command_metadata("event-plan"), plan=plan),  # type: ignore[arg-type]
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
    with pytest.raises(EffectLifecycleError, match="must start"):
        decide(
            state,
            RecordAttemptOutcome(
                **command_metadata("event-return-early"),  # type: ignore[arg-type]
                request_id=request.id,
                outcome=returned,
            ),
        )


def test_cognitive_history_reconstruction_mismatch_and_semantics_have_distinct_owners() -> None:
    state = stand_guard(started())
    basis = claim("claim-basis", proposition_id="basis-proposition")
    difference = claim("claim-difference", proposition_id="relation-semantic-change")
    for index, item in enumerate((basis, difference), start=1):
        state, _ = apply(
            state,
            AdmitClaim(
                **command_metadata(f"event-claim-{index}"),  # type: ignore[arg-type]
                claim=item,
            ),
        )
    state = promote_semantic_change(state, difference)

    obligation_source = claim("claim-need", role=ClaimRole.NECESSITY)
    state, _ = apply(
        state,
        AdmitClaim(**command_metadata("event-need"), claim=obligation_source),  # type: ignore[arg-type]
    )
    obligation = next(item for item in state.obligations if item.carrier_id == obligation_source.id)
    state, scheduler_plan = record_scheduler_plan(
        state,
        obligation.id,
        label="cognitive",
    )
    request = EffectRequest(
        id="request-cognitive",
        step_plan_id=scheduler_plan.id,
        effect_kind="probe",
        adapter_id="adapter-scripted",
        input_artifact=ref("e"),
    )
    state, _ = apply(
        state,
        RequestEffect(**command_metadata("event-request-cognitive"), request=request),  # type: ignore[arg-type]
    )
    plan = EffectAttemptPlan(
        id="attempt-cognitive",
        request_id=request.id,
        route=RouteSnapshot(
            id="route-cognitive",
            definition_id="route-definition-cognitive",
            definition_version="1",
            definition_artifact=ref("f"),
            backend_id="backend-scripted",
            adapter_id="adapter-scripted",
            adapter_version="1",
            execution_environment_artifact=ref("8"),
            request_or_action_digest="7" * 64,
        ),
    )
    cognitive_plan = CognitiveAttemptPlan(
        id="cognitive-plan-1",
        obligation_id=obligation.id,
        probe_or_action_id="probe-cognitive",
        effect_request_id=request.id,
        effect_attempt_plan_id=plan.id,
        source_state_revision=state.sequence,
        scope_fingerprint=scope().fingerprint,
        planned_sequence=state.sequence + 1,
    )
    state, _ = apply(
        state,
        RecordCognitivePlan(
            **command_metadata("event-cognitive-plan"),  # type: ignore[arg-type]
            plan=cognitive_plan,
        ),
    )
    prediction = PredictionSeal(
        id="prediction-1",
        cognitive_plan_id=cognitive_plan.id,
        probe_or_action_id=cognitive_plan.probe_or_action_id,
        predicted_return_class="unchanged",
        predicted_consequence={"lamp": False},
        acceptable_variation={"exact": True},
        scope_fingerprint=scope().fingerprint,
        basis_claim_ids=(basis.id,),
        sealed_sequence=state.sequence + 1,
    )
    state, _ = apply(
        state,
        SealPrediction(
            **command_metadata("event-prediction"),  # type: ignore[arg-type]
            prediction=prediction,
        ),
    )
    state, _ = apply(
        state,
        PlanEffectAttempt(**command_metadata("event-plan-cognitive"), plan=plan),  # type: ignore[arg-type]
    )
    state, _ = apply(
        state,
        StartEffectAttempt(
            **command_metadata("event-start-cognitive"),  # type: ignore[arg-type]
            attempt_id=plan.id,
        ),
    )
    external_return = ExternalReturn(
        id="return-cognitive",
        attempt_id=plan.id,
        route_id=plan.route.id,
        capture_boundary="test-native-null",
        capture_encoding="native-null",
        captured_at=NOW,
        raw_payload=CapturedPayload(kind="null"),
    )
    state, _ = apply(
        state,
        RecordAttemptOutcome(
            **command_metadata("event-return-cognitive"),  # type: ignore[arg-type]
            request_id=request.id,
            outcome=ReturnedOutcome(
                attempt_id=plan.id,
                route_id=plan.route.id,
                external_return=external_return,
            ),
        ),
    )
    decoded = Decoded(
        id="decode-cognitive",
        external_return_id=external_return.id,
        decoder_id="decoder-1",
        decoder_version="1",
        result=SuccessResult(
            id="result-cognitive",
            semantic_artifact=ref("9"),
            operation_id="observe",
        ),
    )
    state, _ = apply(
        state,
        RecordDecodeOutcome(
            **command_metadata("event-decode-cognitive"),  # type: ignore[arg-type]
            request_id=request.id,
            outcome=decoded,
        ),
    )
    state, _ = apply(
        state,
        AcceptEffectResult(
            **command_metadata("event-accept-cognitive"),  # type: ignore[arg-type]
            request_id=request.id,
            decoded_outcome_id=decoded.id,
        ),
    )

    probe = ProbeIdentity(
        question_contract_key="probe-cognitive@1",
        relational_role="change",
        binding_schema_id="carrier-1",
        binding_revision="binding-1",
        scope_fingerprint=scope().fingerprint,
        comparison_semantics_id="exact-1",
        applicability_guard_id="guard-1",
        protected_horizon_id="horizon-1",
    )
    state, _ = apply(
        state,
        AdmitProbe(**command_metadata("event-admit-probe"), probe=probe),  # type: ignore[arg-type]
    )
    forged_observation = ProbeEvent(
        id="probe-event-forged",
        probe_identity=probe,
        bound_referents=(BoundArgument(name="subject", value="lamp"),),
        binding_revision="binding-1",
        state_revision=state.sequence,
        semantic_field_id="field-forged",
        generated_answer_claim_id=difference.id,
        external_return_ids=(external_return.id,),
        interpretation_claim_ids=(difference.id,),
        sequence_index=1,
        comparability_bridge=ComparabilityBridge(
            from_probe_fingerprint=probe.fingerprint,
            to_probe_fingerprint=probe.fingerprint,
            comparison_proposition_id="relation-semantic-change",
            scope_fingerprint=scope().fingerprint,
            warrant_lemma_id="lemma-forged-bridge",
        ),
        fresh_observation_required=True,
        prior_answer_exposure="withheld_until_capture",
    )
    with pytest.raises(InvalidCommandError, match="bridge requires an active hard lemma"):
        decide(
            state,
            RecordProbeObservation(
                **command_metadata("event-observation-forged"),  # type: ignore[arg-type]
                observation=forged_observation,
            ),
        )
    wrong_proposition_observation = forged_observation.model_copy(
        update={
            "id": "probe-event-wrong-comparison",
            "comparability_bridge": ComparabilityBridge(
                from_probe_fingerprint=probe.fingerprint,
                to_probe_fingerprint=probe.fingerprint,
                comparison_proposition_id="relation-unrelated",
                scope_fingerprint=scope().fingerprint,
                warrant_lemma_id="lemma-1",
            ),
        }
    )
    with pytest.raises(InvalidCommandError, match="does not match its proposition and scope"):
        decide(
            state,
            RecordProbeObservation(
                **command_metadata("event-observation-wrong-comparison"),  # type: ignore[arg-type]
                observation=wrong_proposition_observation,
            ),
        )
    state, _ = apply(
        state,
        RecordProbeObservation(
            **command_metadata("event-observation"),  # type: ignore[arg-type]
            observation=ProbeEvent(
                id="probe-event-1",
                probe_identity=probe,
                bound_referents=(BoundArgument(name="subject", value="lamp"),),
                binding_revision="binding-1",
                state_revision=state.sequence,
                semantic_field_id="field-1",
                generated_answer_claim_id=difference.id,
                external_return_ids=(external_return.id,),
                interpretation_claim_ids=(difference.id,),
                sequence_index=1,
                fresh_observation_required=True,
                prior_answer_exposure="withheld_until_capture",
            ),
        ),
    )
    reconstruction = Reconstruction(
        id="reconstruction-1",
        prior_state_revision=state.sequence,
        external_return_id=external_return.id,
        decode_outcome_ids=(decoded.id,),
        candidate_claim_ids=(difference.id,),
        generated_detail_ids=("generated-detail-1",),
        reconstructed_sequence=state.sequence + 1,
    )
    state, _ = apply(
        state,
        RecordReconstruction(
            **command_metadata("event-reconstruction"),  # type: ignore[arg-type]
            reconstruction=reconstruction,
        ),
    )
    mismatch = Mismatch(
        id="mismatch-1",
        prediction_id=prediction.id,
        external_return_id=external_return.id,
        decode_outcome_id=decoded.id,
        difference_claim_id=difference.id,
        scope_fingerprint=scope().fingerprint,
        protected_consequence_changed=True,
        classification="actual-change",
    )
    state, _ = apply(
        state,
        RecordMismatch(
            **command_metadata("event-mismatch"),  # type: ignore[arg-type]
            mismatch=mismatch,
        ),
    )
    bad_delta = SemanticDelta(
        id="semantic-delta-bad",
        reconstruction_id=reconstruction.id,
        warranted_changes=(
            WarrantedChange(
                change_id="semantic-change-bad",
                proposition_id="unrelated-proposition",
                scope_fingerprint=scope().fingerprint,
                operation=SemanticChangeOperation.ADD,
                warrant_lemma_id="lemma-1",
            ),
        ),
        committed_sequence=state.sequence + 1,
    )
    with pytest.raises(InvalidCommandError, match="exceeds its exact warrant"):
        decide(
            state,
            CommitSemanticDelta(
                **command_metadata("event-semantic-delta-bad"),  # type: ignore[arg-type]
                delta=bad_delta,
            ),
        )
    delta = SemanticDelta(
        id="semantic-delta-1",
        reconstruction_id=reconstruction.id,
        warranted_changes=(
            WarrantedChange(
                change_id="semantic-change-1",
                proposition_id="relation-semantic-change",
                scope_fingerprint=scope().fingerprint,
                operation=SemanticChangeOperation.ADD,
                warrant_lemma_id="lemma-1",
            ),
        ),
        committed_sequence=state.sequence + 1,
    )
    state, _ = apply(
        state,
        CommitSemanticDelta(
            **command_metadata("event-semantic-delta"),  # type: ignore[arg-type]
            delta=delta,
        ),
    )

    assert state.predictions == (prediction,)
    assert state.captured_external_return_ids == frozenset((external_return.id,))
    assert state.reconstructions == (reconstruction,)
    assert state.mismatches == (mismatch,)
    assert state.semantic_deltas == (delta,)
    assert state.claim_by_id(difference.id) == difference
    assert reconstruction.generated_detail_ids == ("generated-detail-1",)
    assert delta.warranted_changes[0].proposition_id == "relation-semantic-change"
