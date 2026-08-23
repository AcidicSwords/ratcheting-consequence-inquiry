"""Blocking G3FO acceptance over ledger-owned capability-evaluation lifecycles."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from rci.bindings import circuit_demonstration, route_demonstration
from rci.claims import Claim, ClaimRole, Provenance
from rci.claims.models import BoundArgument
from rci.cli import app
from rci.core import (
    AcceptEffectResult,
    AdmitClaim,
    NoAttemptDisposition,
    NoAttemptReason,
    PlanEffectAttempt,
    PresentationUnknownOutcome,
    PresentationUnknownReason,
    RecordAttemptOutcome,
    RecordCheckerVerdict,
    RecordCognitivePlan,
    RecordDecodeOutcome,
    RecordEvidence,
    RecordMismatch,
    RecordNoAttemptDisposition,
    RecordStepPlan,
    RequestEffect,
    ReturnedOutcome,
    SealPrediction,
    StartEffectAttempt,
)
from rci.core.effects import (
    Decoded,
    EffectAttemptPlan,
    EffectRequest,
    ExternalReturn,
    MalformedDecode,
    RouteSnapshot,
    SuccessResult,
)
from rci.core.model import ArtifactRef, CapturedPayload
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.evaluation import (
    CapabilityEvaluationBundle,
    CapabilityEvaluationProtocol,
    CapabilityTaskEnvelope,
    CheckIndeterminateObserved,
    ConsequenceObservation,
    DecodeIndeterminateObserved,
    EvaluationPassed,
    EvaluationProtocolInvalid,
    HandoffStatus,
    OperationalUnknownObserved,
    OperationalUnknownReason,
    ProtectedExpectation,
    ProtectedMismatchObserved,
    build_capability_consequence_report,
    build_capability_evaluation_protocol,
    build_capability_task_envelope,
    capability_protocol_artifact,
    capability_report_artifact,
    cognitive_handoff_artifact,
)
from rci.orchestration import AttemptKey, ObligationEntry, plan_next
from rci.probes import CognitiveAttemptPlan, Mismatch, PredictionSeal
from rci.project import (
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    ImplementationGoalContract,
    LimitationKind,
    ProjectAnchor,
    ProjectCost,
    ProjectGainKind,
    SuccessorKind,
    derive_capability_frontier,
)
from rci.sdk import RCI
from rci.warrant import (
    CheckerVerdict,
    CheckerVerdictRecord,
    Evidence,
    EvidenceKind,
    PropositionKind,
)

NOW = datetime(2026, 8, 22, tzinfo=UTC)
HEAD = "a" * 40
INCUMBENT_GATE = "1" * 64
GATE = "2" * 64
ACTOR = "scripted-weak-reasoner"
ACTOR_REVISION = "1"
ROUTE = "weak-reasoner-route"
CHECKER = "deterministic-report-checker"


def _stored(sdk: RCI, value: bytes, media_type: str = "application/octet-stream") -> ArtifactRef:
    return sdk.artifacts.put_bytes(value, media_type=media_type, encoding="utf-8")


def _project_setup(
    sdk: RCI, inquiry_id: str, *, record: bool = True
) -> tuple[ProjectAnchor, ImplementationGoalContract]:
    sdk.start(inquiry_id)
    anchor = ProjectAnchor(
        id=f"anchor-{inquiry_id}",
        repository="AcidicSwords/ratcheting-consequence-inquiry",
        protected_branch="main",
        commit_sha=HEAD,
        tree_digest="3" * 64,
        authority_digest="4" * 64,
        gate_digest=INCUMBENT_GATE,
        clean=True,
    )
    if record:
        sdk.record_project_anchor(inquiry_id, anchor)
    limitation = CapabilityLimitation(
        id=f"limitation-{inquiry_id}",
        anchor_id=anchor.id,
        kind=LimitationKind.EVIDENCE,
        current_capability="Preserve operational returns without typed task evaluation.",
        missing_capability="Derive exact protected-consequence failure from owned evidence.",
        consequential_boundary=(
            "Wrong semantic answers and unavailable execution route differently."
        ),
        protected_consequence_ids=("failure-classification",),
        observed_evidence=(_stored(sdk, b"manual observation-to-limitation join"),),
    )
    if record:
        sdk.record_capability_limitation(inquiry_id, limitation)
    successor = CapabilitySuccessorCandidate(
        id=f"successor-{inquiry_id}",
        anchor_id=anchor.id,
        limitation_id=limitation.id,
        kind=SuccessorKind.IMPLEMENTATION,
        current_state=limitation.current_capability,
        desired_state=limitation.missing_capability,
        preserved_capability_ids=("g1", "g2a", "g2b", "g3ah", "g3g", "g3q", "g3r"),
        gain_kinds=(ProjectGainKind.NEW_SEPARATOR,),
        discriminator_id="capability-failure-observation",
        evidence_mechanism_ids=("acceptance", "independent-check", "ledger"),
        estimated_costs=(ProjectCost(axis="implementation_steps", value=1),),
        reversible=True,
    )
    if record:
        sdk.record_capability_successor_candidate(inquiry_id, successor)
    frontier = derive_capability_frontier(
        frontier_id=f"frontier-{inquiry_id}", candidates=(successor,)
    )
    if record:
        sdk.record_capability_frontier(inquiry_id, frontier)
    goal = ImplementationGoalContract(
        id=f"goal-{inquiry_id}",
        cycle_id=f"cycle-{inquiry_id}",
        anchor_id=anchor.id,
        frontier_id=frontier.id,
        candidate_id=successor.id,
        current=successor.current_state,
        desired=successor.desired_state,
        separator="Six pinned task returns produce six lawful evaluation outcomes.",
        expected_incumbent_return="A human manually classifies the episode.",
        expected_candidate_return="The owned lifecycle derives a typed result and handoff.",
        preserve_capability_ids=successor.preserved_capability_ids,
        acceptance_commands=(
            "uv run pytest -q tests/acceptance/test_capability_failure_observation.py",
        ),
        allowed_mutation_roots=("src/rci/evaluation", "src/rci/sdk.py", "tests/acceptance"),
        forbidden_authority_roots=(".git", ".github", "AGENTS.md", "PLAN.md"),
        assumption_ids=("existing-effect-lifecycle-is-authoritative",),
        incumbent_gate_digest=anchor.gate_digest,
        proposed_gate_digest=GATE,
        rollback_condition="Any predecessor gate fails.",
        reopening_condition="A new failure class is independently observed.",
    )
    if record:
        sdk.seal_implementation_goal(inquiry_id, goal)
    return anchor, goal


def _record_check(
    sdk: RCI,
    inquiry_id: str,
    *,
    suffix: str,
    proposition_id: str,
    artifact: ArtifactRef,
    checker_id: str = CHECKER,
    verdict: CheckerVerdict = CheckerVerdict.VALID,
) -> CheckerVerdictRecord:
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    evidence = Evidence(
        id=f"evidence-{suffix}",
        kind=EvidenceKind.OBSERVATION,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=state.context.scope_fingerprint,
        artifact=artifact,
    )
    verdict_artifact = _stored(sdk, f"verdict:{verdict.value}:{suffix}".encode())
    checker = CheckerVerdictRecord(
        id=f"checker-{suffix}",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=evidence.proposition_id,
        proposition_kind=evidence.proposition_kind,
        scope_fingerprint=evidence.scope_fingerprint,
        checker_id=checker_id,
        checker_version="1",
        verdict=verdict,
        verdict_artifact=verdict_artifact,
        certificate_artifact=(verdict_artifact if verdict is CheckerVerdict.VALID else None),
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordEvidence(
                event_id=f"event-evidence-{suffix}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                evidence=evidence,
            ),
            RecordCheckerVerdict(
                event_id=f"event-checker-{suffix}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                checker_verdict=checker,
            ),
        ),
    )
    return checker


def _prepare_owned_request(
    sdk: RCI,
    inquiry_id: str,
    consequence_id: str,
    *,
    outcome: str,
    route_id: str = ROUTE,
    actor_id: str = ACTOR,
    protocol_actor_id: str = ACTOR,
    evidence_access_bytes: bytes = b"finite evidence universe",
    budget_bytes: bytes = b'{"attempts":1,"checks":2}',
    checker_verdict: CheckerVerdict = CheckerVerdict.VALID,
    recorded_checker_id: str = CHECKER,
    actual_size_delta: int = 0,
    binding_override: str | None = None,
    scope_override: str | None = None,
    horizon_override: str | None = None,
    request_timeout_delta: int = 0,
    late_competing: bool = False,
    authority_after_return: bool = False,
) -> tuple[CapabilityEvaluationProtocol, str]:
    anchor, goal = _project_setup(sdk, inquiry_id, record=not authority_after_return)
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    obligation = state.obligations[0]
    attempt_key = AttemptKey(
        obligation_fingerprint=obligation.fingerprint,
        contract_id="obligation-characterization",
        contract_version="1.0.0",
        binding_revision=obligation.binding_revision,
    )
    step_plan = plan_next(
        (ObligationEntry(obligation=obligation, attempt_key=attempt_key, creation_sequence=1),),
        steps_used=state.sequence,
        policy_version=state.context.scheduler_policy_version,
    )
    expected = _stored(sdk, f"expected:{consequence_id}".encode())
    context_artifact = _stored(sdk, b"bounded task context")
    evidence_access_artifact = _stored(sdk, evidence_access_bytes)
    budget_artifact = _stored(sdk, budget_bytes)
    task = build_capability_task_envelope(
        anchor_id=anchor.id,
        goal_id=goal.id,
        obligation_id=obligation.id,
        competence_id="competence-reason-over-finite-relations",
        binding_revision=binding_override or state.context.binding_revision,
        scope_fingerprint=scope_override or state.context.scope_fingerprint,
        protected_horizon_id=horizon_override or state.context.protected_horizon_id,
        operation_id="answer-finite-relation-task",
        actor_id=protocol_actor_id,
        actor_revision=ACTOR_REVISION,
        adapter_id="scripted-reasoner-adapter",
        route_definition_id=ROUTE,
        route_definition_version="1",
        context_artifact=context_artifact,
        evidence_access_artifact=evidence_access_artifact,
        budget_artifact=budget_artifact,
        timeout_seconds=30,
        protected_consequence_ids=(consequence_id,),
    )
    task_artifact = sdk.publish_capability_task(task)
    protocol = build_capability_evaluation_protocol(
        anchor_id=anchor.id,
        anchor_fingerprint=sha256_digest(canonical_json_bytes(anchor)),
        goal_id=goal.id,
        goal_fingerprint=sha256_digest(canonical_json_bytes(goal)),
        obligation_id=obligation.id,
        step_plan_id=step_plan.id,
        competence_id="competence-reason-over-finite-relations",
        project_head_sha=anchor.commit_sha,
        gate_digest=goal.proposed_gate_digest,
        binding_revision=binding_override or state.context.binding_revision,
        scope_fingerprint=scope_override or state.context.scope_fingerprint,
        protected_horizon_id=horizon_override or state.context.protected_horizon_id,
        operation_id="answer-finite-relation-task",
        effect_kind="capability-evaluation",
        actor_id=protocol_actor_id,
        actor_revision=ACTOR_REVISION,
        adapter_id="scripted-reasoner-adapter",
        route_definition_id=ROUTE,
        route_definition_version="1",
        actor_task_artifact=task_artifact,
        context_artifact=context_artifact,
        evidence_access_artifact=evidence_access_artifact,
        budget_artifact=budget_artifact,
        timeout_seconds=30,
        comparison_policy_id="exact-artifact-equality",
        comparison_policy_version="1",
        decoder_id="capability-report-decoder",
        decoder_version="1",
        checker_id=CHECKER,
        checker_version="1",
        expectations=(
            ProtectedExpectation(
                consequence_id=consequence_id,
                expected_artifact=expected,
                attack_id=f"attack-{consequence_id}",
                downstream_question_id=f"question-{consequence_id}",
            ),
        ),
        discriminator_route_ids=("counterexample-check-route",),
        protected_capability_ids=("g1-authority", "g3r-stage-separation"),
        stopping_condition_ids=("no-lawful-discriminator", "protocol-invalid"),
        reopening_condition_ids=("new-independent-evidence",),
    )
    protocol_artifact = sdk.publish_capability_evaluation_protocol(protocol)
    request = EffectRequest(
        id=f"request-{inquiry_id}",
        step_plan_id=step_plan.id,
        effect_kind=protocol.effect_kind,
        adapter_id=protocol.adapter_id,
        input_artifact=task_artifact,
        timeout_seconds=protocol.timeout_seconds + request_timeout_delta,
    )
    attempt = EffectAttemptPlan(
        id=f"attempt-{inquiry_id}",
        request_id=request.id,
        route=RouteSnapshot(
            id=f"route-{inquiry_id}",
            definition_id=route_id,
            definition_version=protocol.route_definition_version,
            definition_artifact=_stored(sdk, b"route definition"),
            backend_id="scripted-backend",
            adapter_id=protocol.adapter_id,
            adapter_version="1",
            endpoint_or_channel="in-process",
            transport="pure",
            execution_environment_artifact=_stored(sdk, b"redacted environment"),
            request_or_action_digest=sha256_digest(canonical_json_bytes(request)),
        ),
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordStepPlan(
                event_id=f"event-step-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=step_plan,
            ),
            RequestEffect(
                event_id=f"event-request-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request=request,
            ),
        ),
    )
    competing_attempt = attempt.model_copy(
        update={
            "id": f"attempt-competing-{inquiry_id}",
            "route": attempt.route.model_copy(update={"id": f"route-competing-{inquiry_id}"}),
        }
    )
    if late_competing:
        sdk.dispatch_batch(
            inquiry_id,
            (
                PlanEffectAttempt(
                    event_id=f"event-plan-competing-{inquiry_id}",
                    inquiry_id=inquiry_id,
                    occurred_at=NOW,
                    plan=competing_attempt,
                ),
                StartEffectAttempt(
                    event_id=f"event-start-competing-{inquiry_id}",
                    inquiry_id=inquiry_id,
                    occurred_at=NOW,
                    attempt_id=competing_attempt.id,
                ),
            ),
        )
    state = sdk.inspect(inquiry_id)
    cognitive_plan = CognitiveAttemptPlan(
        id=f"cognitive-{inquiry_id}",
        obligation_id=obligation.id,
        probe_or_action_id=protocol.operation_id,
        effect_request_id=request.id,
        effect_attempt_plan_id=(None if outcome in {"pending", "unsupported"} else attempt.id),
        source_state_revision=state.sequence,
        scope_fingerprint=obligation.scope.fingerprint,
        planned_sequence=state.sequence + 1,
    )
    sdk.dispatch(
        RecordCognitivePlan(
            event_id=f"event-cognitive-{inquiry_id}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            plan=cognitive_plan,
        )
    )
    state = sdk.inspect(inquiry_id)
    prediction = PredictionSeal(
        id=f"prediction-{inquiry_id}",
        cognitive_plan_id=cognitive_plan.id,
        probe_or_action_id=protocol.operation_id,
        predicted_return_class="capability-consequence-report",
        predicted_consequence={
            "comparison_policy_id": protocol.comparison_policy_id,
            "comparison_policy_version": protocol.comparison_policy_version,
            "expectations": [
                {
                    "consequence_id": consequence_id,
                    "expected_artifact_digest": expected.digest,
                }
            ],
            "protocol_id": protocol.id,
            "protocol_artifact": protocol_artifact.model_dump(mode="json"),
        },
        acceptable_variation={
            "comparison_policy_id": protocol.comparison_policy_id,
            "comparison_policy_version": protocol.comparison_policy_version,
        },
        scope_fingerprint=obligation.scope.fingerprint,
        basis_claim_ids=(),
        sealed_sequence=state.sequence + 1,
    )
    sdk.dispatch(
        SealPrediction(
            event_id=f"event-prediction-{inquiry_id}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            prediction=prediction,
        )
    )
    if outcome == "pending":
        return protocol, request.id
    if outcome == "unsupported":
        sdk.dispatch(
            RecordNoAttemptDisposition(
                event_id=f"event-unsupported-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                disposition=NoAttemptDisposition(
                    id=f"no-attempt-{inquiry_id}",
                    request_id=request.id,
                    step_plan_id=step_plan.id,
                    reason_kind=NoAttemptReason.UNSUPPORTED,
                    diagnostics=_stored(sdk, b"route unsupported"),
                ),
            )
        )
        return protocol, request.id
    sdk.dispatch_batch(
        inquiry_id,
        (
            PlanEffectAttempt(
                event_id=f"event-plan-attempt-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=attempt,
            ),
            StartEffectAttempt(
                event_id=f"event-start-attempt-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                attempt_id=attempt.id,
            ),
        ),
    )
    if outcome == "timeout":
        sdk.dispatch(
            RecordAttemptOutcome(
                event_id=f"event-timeout-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                outcome=PresentationUnknownOutcome(
                    attempt_id=attempt.id,
                    route_id=attempt.route.id,
                    reason_kind=PresentationUnknownReason.TIMEOUT,
                    diagnostics=_stored(sdk, b"deadline elapsed; presentation unknown"),
                ),
            )
        )
        return protocol, request.id
    external_return = ExternalReturn(
        id=f"return-{inquiry_id}",
        attempt_id=attempt.id,
        route_id=attempt.route.id,
        source_id=actor_id,
        source_revision=ACTOR_REVISION,
        capture_boundary="scripted-stdout",
        capture_encoding="binary",
        captured_at=NOW,
        raw_payload=CapturedPayload(
            kind="bytes", artifact=_stored(sdk, f"raw:{outcome}:{consequence_id}".encode())
        ),
    )
    sdk.dispatch(
        RecordAttemptOutcome(
            event_id=f"event-return-{inquiry_id}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            request_id=request.id,
            outcome=ReturnedOutcome(
                attempt_id=attempt.id,
                route_id=attempt.route.id,
                external_return=external_return,
            ),
        )
    )
    if outcome == "malformed":
        sdk.dispatch(
            RecordDecodeOutcome(
                event_id=f"event-malformed-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                outcome=MalformedDecode(
                    id=f"decode-{inquiry_id}",
                    external_return_id=external_return.id,
                    decoder_id=protocol.decoder_id,
                    decoder_version=protocol.decoder_version,
                    diagnostics=_stored(sdk, b"json syntax error"),
                ),
            )
        )
        return protocol, request.id
    actual = expected if outcome == "pass" else _stored(sdk, f"wrong:{consequence_id}".encode())
    if actual_size_delta:
        actual = actual.model_copy(update={"size": actual.size + actual_size_delta})
    report = build_capability_consequence_report(
        protocol_id=protocol.id,
        observations=(
            ConsequenceObservation(
                consequence_id=consequence_id,
                actual_artifact=actual,
                evidence_artifacts=(_stored(sdk, f"evidence:{consequence_id}".encode()),),
            ),
        ),
    )
    report_ref = sdk.artifacts.put_bytes(
        canonical_json_bytes(report),
        media_type="application/vnd.rci.capability-consequence-report+json",
        encoding="utf-8",
    )
    assert report_ref == capability_report_artifact(report)
    decoded = Decoded(
        id=f"decode-{inquiry_id}",
        external_return_id=external_return.id,
        decoder_id=protocol.decoder_id,
        decoder_version=protocol.decoder_version,
        result=SuccessResult(
            id=f"result-{inquiry_id}",
            semantic_artifact=report_ref,
            operation_id=protocol.operation_id,
        ),
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordDecodeOutcome(
                event_id=f"event-decode-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                outcome=decoded,
            ),
            AcceptEffectResult(
                event_id=f"event-accept-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                decoded_outcome_id=decoded.id,
            ),
        ),
    )
    _record_check(
        sdk,
        inquiry_id,
        suffix=f"report-{inquiry_id}",
        proposition_id=f"capability-report:{report.id}",
        artifact=report_ref,
        checker_id=recorded_checker_id,
        verdict=checker_verdict,
    )
    if outcome == "mismatch":
        difference = Claim(
            id=f"difference-{inquiry_id}",
            role=ClaimRole.CHARACTERIZATION,
            bound_args=(BoundArgument(name="consequence", value=consequence_id),),
            payload=actual,
            scope=obligation.scope,
            provenance=Provenance(kind="checked-mismatch", source_id=decoded.id),
        )
        sdk.dispatch(
            AdmitClaim(
                event_id=f"event-difference-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                claim=difference,
            )
        )
        sdk.dispatch(
            RecordMismatch(
                event_id=f"event-mismatch-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                mismatch=Mismatch(
                    id=f"mismatch-{inquiry_id}",
                    prediction_id=prediction.id,
                    external_return_id=external_return.id,
                    decode_outcome_id=decoded.id,
                    difference_claim_id=difference.id,
                    scope_fingerprint=obligation.scope.fingerprint,
                    protected_consequence_changed=True,
                    classification=f"capability:{consequence_id}",
                ),
            )
        )
    if late_competing:
        late_return = ExternalReturn(
            id=f"return-competing-{inquiry_id}",
            attempt_id=competing_attempt.id,
            route_id=competing_attempt.route.id,
            source_id=actor_id,
            source_revision=ACTOR_REVISION,
            capture_boundary="scripted-stdout",
            capture_encoding="binary",
            captured_at=NOW,
            raw_payload=CapturedPayload(
                kind="bytes", artifact=_stored(sdk, f"late:{outcome}:{consequence_id}".encode())
            ),
        )
        sdk.dispatch(
            RecordAttemptOutcome(
                event_id=f"event-return-competing-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                outcome=ReturnedOutcome(
                    attempt_id=competing_attempt.id,
                    route_id=competing_attempt.route.id,
                    external_return=late_return,
                ),
            )
        )
        sdk.dispatch(
            RecordDecodeOutcome(
                event_id=f"event-decode-competing-{inquiry_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request_id=request.id,
                outcome=Decoded(
                    id=f"decode-competing-{inquiry_id}",
                    external_return_id=late_return.id,
                    decoder_id=protocol.decoder_id,
                    decoder_version=protocol.decoder_version,
                    result=SuccessResult(
                        id=f"result-competing-{inquiry_id}",
                        semantic_artifact=report_ref,
                        operation_id=protocol.operation_id,
                    ),
                ),
            )
        )
    if authority_after_return:
        recorded_anchor, recorded_goal = _project_setup(sdk, inquiry_id)
        assert recorded_anchor == anchor
        assert recorded_goal == goal
    return protocol, request.id


def test_owned_lifecycle_keeps_six_consequential_outcomes_distinct(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    cases = {
        "passed": ("answer-valid", "pass"),
        "necessity": ("false-necessity", "mismatch"),
        "may_must": ("may-must-collapse", "mismatch"),
        "malformed": ("answer-malformed", "malformed"),
        "timeout": ("answer-timeout", "timeout"),
        "unsupported": ("answer-unsupported", "unsupported"),
    }
    results: dict[str, CapabilityEvaluationBundle] = {}
    for name, (consequence, outcome) in cases.items():
        inquiry = f"case-{name}"
        _, request_id = _prepare_owned_request(sdk, inquiry, consequence, outcome=outcome)
        results[name] = sdk.evaluate_capability_request(inquiry, request_id)

    assert isinstance(results["passed"].result, EvaluationPassed)
    necessity = results["necessity"]
    may_must = results["may_must"]
    assert isinstance(necessity.result, ProtectedMismatchObserved)
    assert isinstance(may_must.result, ProtectedMismatchObserved)
    assert necessity.result.violations[0].consequence_id == "false-necessity"
    assert may_must.result.violations[0].consequence_id == "may-must-collapse"
    assert necessity.result.violations[0].attack_id != may_must.result.violations[0].attack_id
    assert (
        necessity.result.violations[0].downstream_question_id
        != may_must.result.violations[0].downstream_question_id
    )
    assert (
        necessity.result.violations[0].evidence_artifacts
        != may_must.result.violations[0].evidence_artifacts
    )
    assert necessity.limitation_candidate is not None
    assert may_must.limitation_candidate is not None
    assert necessity.localization_frame is not None
    assert necessity.localization_frame.selected_limitation_kind is None
    assert necessity.localization_frame.status == "unresolved"
    assert results["passed"].limitation_candidate is None
    assert isinstance(results["malformed"].result, DecodeIndeterminateObserved)
    assert results["malformed"].limitation_candidate is None
    assert isinstance(results["timeout"].result, OperationalUnknownObserved)
    assert results["timeout"].result.reason_kind is OperationalUnknownReason.TIMEOUT
    assert isinstance(results["unsupported"].result, OperationalUnknownObserved)
    assert (
        results["unsupported"].result.reason_kind is OperationalUnknownReason.NO_ATTEMPT_UNSUPPORTED
    )
    assert results["timeout"].limitation_candidate is None
    assert results["unsupported"].limitation_candidate is None
    assert results["malformed"].handoff.failed_decoder_ids == ("capability-report-decoder",)
    assert results["malformed"].handoff.failed_route_ids == ()
    assert results["timeout"].handoff.failed_route_ids == (ROUTE,)


def test_unattempted_request_and_checker_outcomes_do_not_collapse(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, pending_request = _prepare_owned_request(sdk, "pending", "answer-pending", outcome="pending")
    pending = sdk.evaluate_capability_request("pending", pending_request)
    assert isinstance(pending.result, OperationalUnknownObserved)
    assert pending.result.reason_kind is OperationalUnknownReason.PENDING
    assert pending.handoff.failed_route_ids == ()

    for verdict in (
        CheckerVerdict.INVALID,
        CheckerVerdict.INDETERMINATE,
        CheckerVerdict.TIMEOUT,
        CheckerVerdict.UNSUPPORTED,
        CheckerVerdict.FAILED,
    ):
        inquiry = f"check-{verdict.value}"
        _, request_id = _prepare_owned_request(
            sdk,
            inquiry,
            "answer-valid",
            outcome="pass",
            checker_verdict=verdict,
        )
        observed = sdk.evaluate_capability_request(inquiry, request_id)
        assert isinstance(observed.result, CheckIndeterminateObserved)
        assert observed.result.reason_kind == verdict.value
        assert observed.limitation_candidate is None
        assert observed.handoff.failed_decoder_ids == ()


def test_comparison_policy_is_closed_and_duplicate_mismatch_fails_closed(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    protocol, request_id = _prepare_owned_request(
        sdk, "duplicates", "false-necessity", outcome="mismatch"
    )
    with pytest.raises(ValidationError):
        CapabilityEvaluationProtocol.model_validate(
            protocol.model_dump(mode="python") | {"comparison_policy_id": "unregistered-policy"},
            strict=True,
        )
    state = sdk.inspect("duplicates")
    first = state.mismatches[0]
    duplicate_claim = state.claim_by_id(first.difference_claim_id)
    assert duplicate_claim is not None
    second_claim = duplicate_claim.model_copy(update={"id": "difference-duplicate"})
    sdk.dispatch(
        AdmitClaim(
            event_id="event-difference-duplicate",
            inquiry_id="duplicates",
            occurred_at=NOW,
            claim=second_claim,
        )
    )
    sdk.dispatch(
        RecordMismatch(
            event_id="event-mismatch-duplicate",
            inquiry_id="duplicates",
            occurred_at=NOW,
            mismatch=first.model_copy(
                update={"id": "mismatch-duplicate", "difference_claim_id": second_claim.id}
            ),
        )
    )
    observed = sdk.evaluate_capability_request("duplicates", request_id)
    assert isinstance(observed.result, EvaluationProtocolInvalid)
    assert observed.result.issue_codes == ("duplicate_mismatch_classification",)


def test_foreign_route_and_actor_fail_closed(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, route_request = _prepare_owned_request(
        sdk,
        "foreign-route",
        "answer-valid",
        outcome="pass",
        route_id="foreign-route-definition",
        actor_id="foreign-actor",
    )
    foreign = sdk.evaluate_capability_request("foreign-route", route_request)
    assert isinstance(foreign.result, EvaluationProtocolInvalid)
    assert {"foreign_actor", "foreign_route"} <= set(foreign.result.issue_codes)


def test_context_budget_checker_and_post_return_expectation_fail_closed(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)

    def issue_for(inquiry: str, request_id: str) -> tuple[str, ...]:
        observed = sdk.evaluate_capability_request(inquiry, request_id)
        assert isinstance(observed.result, EvaluationProtocolInvalid)
        return observed.result.issue_codes

    _, request_id = _prepare_owned_request(
        sdk,
        "foreign-binding",
        "answer-valid",
        outcome="pass",
        binding_override="other-binding",
    )
    assert "foreign_binding" in issue_for("foreign-binding", request_id)
    _, request_id = _prepare_owned_request(
        sdk, "foreign-scope", "answer-valid", outcome="pass", scope_override="f" * 64
    )
    assert "foreign_scope" in issue_for("foreign-scope", request_id)
    _, request_id = _prepare_owned_request(
        sdk,
        "foreign-horizon",
        "answer-valid",
        outcome="pass",
        horizon_override="other-horizon",
    )
    assert "foreign_horizon" in issue_for("foreign-horizon", request_id)
    _, request_id = _prepare_owned_request(
        sdk, "foreign-budget", "answer-valid", outcome="pass", request_timeout_delta=1
    )
    assert "foreign_budget" in issue_for("foreign-budget", request_id)
    _, request_id = _prepare_owned_request(
        sdk,
        "foreign-checker",
        "answer-valid",
        outcome="pass",
        recorded_checker_id="other-checker",
    )
    assert "checker_missing" in issue_for("foreign-checker", request_id)

    protocol, request_id = _prepare_owned_request(
        sdk, "immutable-expectation", "answer-valid", outcome="pass"
    )
    first = sdk.evaluate_capability_request("immutable-expectation", request_id)
    replacement = protocol.expectations[0].model_copy(
        update={"expected_artifact": _stored(sdk, b"rewritten after return")}
    )
    with pytest.raises(ValidationError):
        CapabilityEvaluationProtocol.model_validate(
            protocol.model_dump(mode="python") | {"expectations": (replacement,)},
            strict=True,
        )
    fields = protocol.model_dump(mode="python", exclude={"id", "schema_version", "policy_version"})
    fields["expectations"] = (replacement,)
    rewritten = build_capability_evaluation_protocol(**fields)
    assert rewritten.id != protocol.id
    assert sdk.publish_capability_evaluation_protocol(rewritten) != first.handoff.protocol_artifact
    second = sdk.evaluate_capability_request("immutable-expectation", request_id)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)


def test_actor_task_never_contains_evaluator_only_expected_material(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    protocol, request_id = _prepare_owned_request(
        sdk, "answer-key-isolation", "answer-valid", outcome="pass"
    )
    request = sdk.inspect("answer-key-isolation").request_by_id(request_id)
    assert request is not None
    task_bytes = sdk.artifacts.get_bytes(request.request.input_artifact)
    expected = protocol.expectations[0].expected_artifact
    assert request.request.input_artifact == protocol.actor_task_artifact
    assert task_bytes != sdk.artifacts.get_bytes(capability_protocol_artifact(protocol))
    assert expected.digest.encode() not in task_bytes
    assert b"expected_artifact" not in task_bytes
    assert b"comparison_policy" not in task_bytes


def test_conflicting_cas_sizes_fail_at_the_owned_projection(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, request_id = _prepare_owned_request(
        sdk,
        "cas-size",
        "answer-valid",
        outcome="pass",
        actual_size_delta=1,
    )
    observed = sdk.evaluate_capability_request("cas-size", request_id)
    assert isinstance(observed.result, EvaluationProtocolInvalid)
    assert observed.result.issue_codes == ("artifact_missing_tampered_or_malformed",)


def test_late_competing_return_and_unaccepted_decode_never_replace_acceptance(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, request_id = _prepare_owned_request(
        sdk,
        "late-competing",
        "answer-valid",
        outcome="pass",
        late_competing=True,
    )
    state = sdk.inspect("late-competing")
    request = state.request_by_id(request_id)
    assert request is not None
    assert len(request.attempts) == len(request.decode_outcomes) == 2
    assert request.accepted_decoded_outcome_id == "decode-late-competing"
    observed = sdk.evaluate_capability_request("late-competing", request_id)
    assert isinstance(observed.result, EvaluationPassed)
    assert observed.result.decode_outcome_id == "decode-late-competing"


def test_project_authority_appended_after_return_cannot_validate_retroactively(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, request_id = _prepare_owned_request(
        sdk,
        "retroactive-authority",
        "answer-valid",
        outcome="pass",
        authority_after_return=True,
    )
    observed = sdk.evaluate_capability_request("retroactive-authority", request_id)
    assert isinstance(observed.result, EvaluationProtocolInvalid)
    assert observed.result.issue_codes == ("authority_not_antecedent_to_request",)


def test_handoff_is_resolvable_and_enforces_route_reopening(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    protocol, request_id = _prepare_owned_request(
        sdk, "handoff", "false-necessity", outcome="mismatch"
    )
    first = sdk.evaluate_capability_request("handoff", request_id)
    handoff = first.handoff
    assert handoff.source_inquiry_id == "handoff"
    assert handoff.source_sequence == sdk.inspect("handoff").sequence
    assert handoff.effect_request_id == request_id
    assert sdk.artifacts.get_bytes(handoff.protocol_artifact)
    assert sdk.artifacts.get_bytes(handoff.evaluation_result_artifact)
    assert handoff.localization_frame_artifact is not None
    assert sdk.artifacts.get_bytes(handoff.localization_frame_artifact)
    assert handoff.status is HandoffStatus.CONTINUE
    assert ROUTE in handoff.forbidden_route_ids_until_reopen

    fields = protocol.model_dump(mode="python", exclude={"id", "schema_version", "policy_version"})
    fields["predecessor_handoff_artifact"] = cognitive_handoff_artifact(handoff)
    fields["continuity_kind"] = "continue"
    repeated = build_capability_evaluation_protocol(**fields)
    with pytest.raises(ValueError, match="without checked reopening"):
        sdk.publish_capability_evaluation_protocol(repeated)

    arbitrary = _stored(sdk, b"self-authored reopening assertion")
    fields["reopening_evidence_artifacts"] = (arbitrary,)
    fields["reopening_checker_verdict_ids"] = ("missing-check",)
    unchecked = build_capability_evaluation_protocol(**fields)
    with pytest.raises(ValueError, match="not uniquely owned and checked"):
        sdk.publish_capability_evaluation_protocol(unchecked)

    reopening_artifact = _stored(sdk, b"independent route reopening evidence")
    reopening_check = _record_check(
        sdk,
        "handoff",
        suffix="route-reopening",
        proposition_id=f"reopen-route:{ROUTE}",
        artifact=reopening_artifact,
        checker_id="finite-exhaustive-v1",
    )
    fields["reopening_evidence_artifacts"] = (reopening_artifact,)
    fields["reopening_checker_verdict_ids"] = (reopening_check.id,)
    checked_reopening = build_capability_evaluation_protocol(**fields)
    sdk.publish_capability_evaluation_protocol(checked_reopening)

    fields["reopening_evidence_artifacts"] = ()
    fields["reopening_checker_verdict_ids"] = ()
    fields["route_definition_id"] = "counterexample-check-route"
    fields["discriminator_route_ids"] = ("alternate-independent-route",)
    original_task = CapabilityTaskEnvelope.model_validate_json(
        sdk.artifacts.get_bytes(protocol.actor_task_artifact), strict=True
    )
    task_fields = original_task.model_dump(mode="python", exclude={"id", "schema_version"})
    task_fields["route_definition_id"] = "counterexample-check-route"
    successor_task = build_capability_task_envelope(**task_fields)
    fields["actor_task_artifact"] = sdk.publish_capability_task(successor_task)
    lawful = build_capability_evaluation_protocol(**fields)
    sdk.publish_capability_evaluation_protocol(lawful)


def test_direct_cas_dispatch_cannot_omit_or_self_authorize_continuity(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)

    def append_pending(
        inquiry_id: str,
        protocol: CapabilityEvaluationProtocol,
        suffix: str,
    ) -> str:
        protocol_ref = sdk.artifacts.put_bytes(
            canonical_json_bytes(protocol),
            media_type="application/vnd.rci.capability-evaluation+json",
            encoding="utf-8",
        )
        request = EffectRequest(
            id=f"request-{suffix}",
            step_plan_id=protocol.step_plan_id,
            effect_kind=protocol.effect_kind,
            adapter_id=protocol.adapter_id,
            input_artifact=protocol.actor_task_artifact,
            timeout_seconds=protocol.timeout_seconds,
        )
        sdk.dispatch(
            RequestEffect(
                event_id=f"event-request-{suffix}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                request=request,
            )
        )
        state = sdk.inspect(inquiry_id)
        plan = CognitiveAttemptPlan(
            id=f"cognitive-{suffix}",
            obligation_id=protocol.obligation_id,
            probe_or_action_id=protocol.operation_id,
            effect_request_id=request.id,
            effect_attempt_plan_id=None,
            source_state_revision=state.sequence,
            scope_fingerprint=protocol.scope_fingerprint,
            planned_sequence=state.sequence + 1,
        )
        sdk.dispatch(
            RecordCognitivePlan(
                event_id=f"event-cognitive-{suffix}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                plan=plan,
            )
        )
        state = sdk.inspect(inquiry_id)
        sdk.dispatch(
            SealPrediction(
                event_id=f"event-prediction-{suffix}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                prediction=PredictionSeal(
                    id=f"prediction-{suffix}",
                    cognitive_plan_id=plan.id,
                    probe_or_action_id=protocol.operation_id,
                    predicted_return_class="capability-consequence-report",
                    predicted_consequence={
                        "comparison_policy_id": protocol.comparison_policy_id,
                        "comparison_policy_version": protocol.comparison_policy_version,
                        "expectations": [
                            {
                                "consequence_id": item.consequence_id,
                                "expected_artifact_digest": item.expected_artifact.digest,
                            }
                            for item in protocol.expectations
                        ],
                        "protocol_id": protocol.id,
                        "protocol_artifact": protocol_ref.model_dump(mode="json"),
                    },
                    acceptable_variation={
                        "comparison_policy_id": protocol.comparison_policy_id,
                        "comparison_policy_version": protocol.comparison_policy_version,
                    },
                    scope_fingerprint=protocol.scope_fingerprint,
                    basis_claim_ids=(),
                    sealed_sequence=state.sequence + 1,
                ),
            )
        )
        return request.id

    original, first_request = _prepare_owned_request(
        sdk, "continuity-omitted", "false-necessity", outcome="mismatch"
    )
    sdk.evaluate_capability_request("continuity-omitted", first_request)
    omitted_request = append_pending("continuity-omitted", original, "omitted")
    omitted = sdk.evaluate_capability_request("continuity-omitted", omitted_request)
    assert isinstance(omitted.result, EvaluationProtocolInvalid)
    assert "continuity_predecessor_omitted" in omitted.result.issue_codes

    original, first_request = _prepare_owned_request(
        sdk, "continuity-unchecked", "false-necessity", outcome="mismatch"
    )
    first = sdk.evaluate_capability_request("continuity-unchecked", first_request)
    arbitrary = _stored(sdk, b"self-authored reopening assertion")
    fields = original.model_dump(mode="python", exclude={"id", "schema_version", "policy_version"})
    fields.update(
        continuity_kind="continue",
        predecessor_handoff_artifact=cognitive_handoff_artifact(first.handoff),
        reopening_evidence_artifacts=(arbitrary,),
        reopening_checker_verdict_ids=("missing-check",),
    )
    unchecked = build_capability_evaluation_protocol(**fields)
    unchecked_request = append_pending("continuity-unchecked", unchecked, "unchecked")
    observed = sdk.evaluate_capability_request("continuity-unchecked", unchecked_request)
    assert isinstance(observed.result, EvaluationProtocolInvalid)
    assert "continuity_invalid" in observed.result.issue_codes


def test_replay_cli_sdk_and_model_prose_are_inert(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, request_id = _prepare_owned_request(sdk, "parity", "false-necessity", outcome="mismatch")
    first = sdk.evaluate_capability_request("parity", request_id)
    exported = sdk.export("parity")
    assert sdk.replay("parity") == sdk.inspect("parity")
    assert sdk.export("parity") == exported
    second = sdk.evaluate_capability_request("parity", request_id)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)

    runner = CliRunner()
    evaluated = runner.invoke(
        app,
        ["project", "evaluate", "parity", "--request-id", request_id, "--root", str(tmp_path)],
    )
    handed = runner.invoke(
        app,
        ["project", "handoff", "parity", "--request-id", request_id, "--root", str(tmp_path)],
    )
    assert evaluated.exit_code == handed.exit_code == 0
    assert json.loads(evaluated.stdout) == first.model_dump(mode="json")
    assert json.loads(handed.stdout) == first.handoff.model_dump(mode="json")
    assert "model prose" not in evaluated.stdout


def test_public_boundary_requires_an_owned_stream_request(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    _, first_request = _prepare_owned_request(sdk, "owned-first", "answer-valid", outcome="pass")
    _, second_request = _prepare_owned_request(sdk, "owned-second", "answer-valid", outcome="pass")
    assert first_request != second_request
    with pytest.raises(ValueError, match="not owned"):
        sdk.evaluate_capability_request("owned-first", second_request)

    free_episode = tmp_path / "forged-episode.json"
    free_episode.write_text('{"caller":"authored"}', encoding="utf-8")
    rejected = CliRunner().invoke(
        app,
        [
            "project",
            "evaluate",
            "owned-first",
            "--request-id",
            first_request,
            "--record",
            str(free_episode),
            "--root",
            str(tmp_path),
        ],
    )
    assert rejected.exit_code != 0


def test_weak_reasoner_fixture_is_derived_from_two_owned_branches(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    tasks = ("main-power-not-necessary", "may-reach-does-not-imply-must-reach")
    baseline_sources: list[tuple[str, str]] = []
    assisted_sources: list[tuple[str, str]] = []
    circuit = circuit_demonstration()
    routes = route_demonstration()
    assert circuit.expected_findings_hold
    assert circuit.main_power_necessity_attack.witness is not None
    assert routes.expected_findings_hold

    def scripted_actor(task: str, *, assisted: bool) -> str:
        if not assisted:
            return "mismatch"
        if task == "main-power-not-necessary":
            return "pass" if circuit.main_power_necessity_attack.witness is not None else "mismatch"
        if task == "may-reach-does-not-imply-must-reach":
            return "pass" if routes.expected_findings_hold else "mismatch"
        raise ValueError("scripted weak reasoner received an unknown task")

    for branch, sources in (
        ("baseline", baseline_sources),
        ("assisted", assisted_sources),
    ):
        for index, task in enumerate(tasks):
            inquiry = f"{branch}-{index}"
            outcome = scripted_actor(task, assisted=branch == "assisted")
            _, request_id = _prepare_owned_request(sdk, inquiry, task, outcome=outcome)
            if branch == "assisted":
                _record_check(
                    sdk,
                    inquiry,
                    suffix=f"native-{inquiry}",
                    proposition_id=f"native-check:{task}",
                    artifact=_stored(sdk, f"checked:{task}".encode()),
                    checker_id="finite-exhaustive-v1",
                )
            sources.append((inquiry, request_id))

    fixture = sdk.evaluate_weak_reasoner_fixture(
        baseline_sources=tuple(baseline_sources),
        assisted_sources=tuple(assisted_sources),
    )
    permuted = sdk.evaluate_weak_reasoner_fixture(
        baseline_sources=tuple(reversed(baseline_sources)),
        assisted_sources=tuple(reversed(assisted_sources)),
    )
    assert canonical_json_bytes(fixture) == canonical_json_bytes(permuted)
    _, forged_request = _prepare_owned_request(
        sdk,
        "assisted-forged",
        tasks[0],
        outcome="pass",
        protocol_actor_id="different-actor",
        actor_id="different-actor",
        evidence_access_bytes=b"different evidence universe",
        budget_bytes=b"different budget",
    )
    with pytest.raises(ValueError, match="actor/context/evidence/budget"):
        sdk.evaluate_weak_reasoner_fixture(
            baseline_sources=tuple(baseline_sources),
            assisted_sources=(("assisted-forged", forged_request), assisted_sources[1]),
        )
    assert [item.correct for item in fixture.baseline.conclusions] == [False, False]
    assert [item.correct for item in fixture.assisted.conclusions] == [True, True]
    assert fixture.baseline.cost.attempts == fixture.assisted.cost.attempts == 2
    assert fixture.assisted.cost.checks > fixture.baseline.cost.checks
    assert fixture.baseline.cost.retries == fixture.assisted.cost.retries == 0
    assert fixture.baseline.cost.context_bytes == fixture.assisted.cost.context_bytes
