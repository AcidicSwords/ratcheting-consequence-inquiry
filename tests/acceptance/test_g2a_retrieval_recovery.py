from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rci.bindings.circuit import circuit_demonstration, circuit_universe
from rci.claims import BoundArgument, ObligationStatus, Scope
from rci.cli import app
from rci.core import (
    AdmitProbe,
    InquiryContext,
    LinkReacquisitionInquiry,
    RecordCheckerVerdict,
    RecordEvidence,
    RecordProbeObservation,
    RecordRecoveryComparison,
    RequestReacquisition,
)
from rci.core.errors import IdentityConflictError, InvalidCommandError
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.memory import (
    ConsequenceEvaluationRoute,
    CostAxis,
    CostCoordinate,
    CostVector,
    DirectUseRoute,
    MemoryOwner,
    OwnedRecordType,
    ReacquisitionInquiryLink,
    ReacquisitionRequest,
    ReacquisitionRoute,
    ReacquisitionScaffold,
    ReconstructionRoute,
    RecoveryBranch,
    RecoveryComparisonOutcome,
    RecoveryObservation,
    RecoveryProtocol,
    RetentionPackage,
    RetentionRegistration,
    make_owned_memory_ref,
)
from rci.persistence import SagaIntegrityError
from rci.probes import ProbeEvent, ProbeIdentity
from rci.questions.catalog import CATALOG_V0_3
from rci.sdk import RCI
from rci.warrant import (
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    EvidenceKind,
    PropositionKind,
)

NOW = datetime(2026, 8, 22, tzinfo=UTC)


def circuit_context() -> InquiryContext:
    universe = circuit_universe()
    scope = Scope(
        id="scope:circuit-recovery",
        binding_revision="binding:circuit-v1",
        finite_universe_hash=universe.fingerprint,
        closed_world=True,
    )
    return InquiryContext(
        binding_revision=scope.binding_revision,
        carrier_schema_ids=("rci.circuit-state.v1",),
        relation_schema_ids=("rci.circuit-consequence.v1",),
        consequence_profile_id="competence:derive-switch-necessity",
        protected_horizon_id="horizon:circuit-v1",
        admissible_operation_ids=("question.ask-v1", "answer.bind-l0-v1"),
        discharge_mechanism_ids=("finite-exhaustive-v1",),
        scope_id=scope.id,
        scope_fingerprint=scope.fingerprint,
        finite_universe_hash=universe.fingerprint,
        closed_world=True,
        catalog_manifest_digest=CATALOG_V0_3.digest,
        scheduler_policy_version="deterministic-scheduler-v1",
        warrant_policy_version="g2a-recovery-v1",
        provenance_refs=("reference-circuit-v1",),
    )


def probe_identity(context: InquiryContext) -> ProbeIdentity:
    return ProbeIdentity(
        question_contract_key="necessity-counterexample@1.0.0",
        relational_role="counterexample",
        binding_schema_id=context.carrier_schema_ids[0],
        binding_revision=context.binding_revision,
        scope_fingerprint=context.scope_fingerprint,
        comparison_semantics_id="exact-circuit-probe-order-v1",
        applicability_guard_id="always",
        protected_horizon_id=context.protected_horizon_id,
    )


def cost_vector(*, effects: int, probes: int, budget: bool = False) -> CostVector:
    bound = 10 if budget else None
    return CostVector(
        coordinates=(
            CostCoordinate(
                axis=CostAxis(id="effects", unit_id="count"),
                numerator=bound if bound is not None else effects,
            ),
            CostCoordinate(
                axis=CostAxis(id="logical_probes", unit_id="count"),
                numerator=bound if bound is not None else probes,
            ),
        )
    )


def build_registration(
    sdk: RCI,
    inquiry_id: str,
    context: InquiryContext,
) -> RetentionRegistration:
    probe = probe_identity(context)
    sdk.dispatch(
        AdmitProbe(
            event_id="event:parent-probe-admitted",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            probe=probe,
        )
    )
    probe_ref = make_owned_memory_ref(
        owner=MemoryOwner.PROCEDURAL,
        record_type=OwnedRecordType.PROBE_IDENTITY,
        record_id=probe.fingerprint,
        record_schema_version=1,
        record=probe,
    )
    direct = DirectUseRoute(
        id="route:circuit-direct",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        source_refs=(probe_ref,),
        provenance_refs=("reference-circuit-v1",),
        present_use_contract_id="contract:circuit-direct-v1",
    )
    reconstruction = ReconstructionRoute(
        id="route:circuit-reconstruction",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        source_refs=(probe_ref,),
        provenance_refs=("reference-circuit-v1",),
        reconstruction_policy_id="candidate-reconstruction-v1",
    )
    consequence = ConsequenceEvaluationRoute(
        id="route:circuit-consequence",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        source_refs=(probe_ref,),
        provenance_refs=("reference-circuit-v1",),
        consequence_evaluator_id="evaluator:circuit-exhaustive",
    )
    scaffold = ReacquisitionScaffold(
        id="scaffold:circuit-recovery",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        cue_refs=(probe_ref,),
        ordered_probe_ids=(probe.fingerprint,),
        boundary_refs=(probe_ref,),
        failure_refs=(probe_ref,),
        provenance_refs=("reference-circuit-v1",),
    )
    protocol = RecoveryProtocol(
        id="protocol:circuit-recovery",
        version="1",
        scope_fingerprint=context.scope_fingerprint,
        target_competence_id=context.consequence_profile_id,
        finite_universe_hash=context.finite_universe_hash or "",
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        evaluator_id="evaluator:circuit-exhaustive",
        evaluator_version="1",
        evidence_access_id="evidence:circuit-eight-state-table",
        evidence_access_version="1",
        budget_id="budget:circuit-recovery",
        budget_version="1",
        budget=cost_vector(effects=10, probes=10, budget=True),
        comparison_policy_id="pareto-frontier-coverage-v1",
        comparison_policy_version="1",
        cost_axes=(
            CostAxis(id="effects", unit_id="count"),
            CostAxis(id="logical_probes", unit_id="count"),
        ),
    )
    reacquisition = ReacquisitionRoute(
        id="route:circuit-reacquisition",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        source_refs=(probe_ref,),
        provenance_refs=("reference-circuit-v1",),
        recovery_protocol_id=protocol.id,
        reacquisition_scaffold_id=scaffold.id,
    )
    package = RetentionPackage(
        id="retention:circuit-scaffold",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        owned_refs=(probe_ref,),
        cue_ids=("cue:circuit-switch",),
        tag_ids=("tag:necessity",),
        direct_use_route_ids=(direct.id,),
        reconstruction_route_ids=(reconstruction.id,),
        consequence_evaluation_route_ids=(consequence.id,),
        reacquisition_route_ids=(reacquisition.id,),
        scaffold_ids=(scaffold.id,),
        recovery_protocol_ids=(protocol.id,),
        provenance_refs=("reference-circuit-v1",),
    )
    return RetentionRegistration(
        package=package,
        direct_use_routes=(direct,),
        reconstruction_routes=(reconstruction,),
        consequence_evaluation_routes=(consequence,),
        reacquisition_routes=(reacquisition,),
        scaffolds=(scaffold,),
        recovery_protocols=(protocol,),
    )


def record_probe_work(sdk: RCI, inquiry_id: str, count: int) -> tuple[str, ...]:
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    probe = probe_identity(state.context)
    sdk.dispatch(
        AdmitProbe(
            event_id=f"event:{inquiry_id}:probe-admitted",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            probe=probe,
        )
    )
    identifiers: list[str] = []
    for index in range(count):
        current = sdk.inspect(inquiry_id)
        identifier = f"probe-run:{inquiry_id}:{index + 1}"
        identifiers.append(identifier)
        sdk.dispatch(
            RecordProbeObservation(
                event_id=f"event:{identifier}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                observation=ProbeEvent(
                    id=identifier,
                    probe_identity=probe,
                    bound_referents=(BoundArgument(name="circuit", value="reference"),),
                    binding_revision=state.context.binding_revision,
                    state_revision=current.sequence,
                    semantic_field_id="semantic-field:circuit",
                    sequence_index=index,
                ),
            )
        )
    return tuple(identifiers)


def complete_child(sdk: RCI, inquiry_id: str, probe_count: int) -> tuple[tuple[str, ...], str]:
    probes = record_probe_work(sdk, inquiry_id, probe_count)
    sdk.submit_answer(inquiry_id, "finite circuit consequence reacquired")
    child = sdk.inspect(inquiry_id)
    accepted = tuple(
        item.request.id for item in child.effect_requests if item.accepted_result is not None
    )
    assert len(accepted) == 1
    assert all(
        child.current_obligation_status(item.id) is ObligationStatus.SATISFIED
        for item in child.obligations
    )
    return probes, accepted[0]


def add_valid_check(
    sdk: RCI,
    inquiry_id: str,
    *,
    seed: str,
    proposition_id: str,
) -> CheckReference:
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    evidence_artifact = sdk.artifacts.put_bytes(f"evidence:{seed}".encode())
    verdict_artifact = sdk.artifacts.put_bytes(f"valid:{seed}".encode())
    certificate_artifact = sdk.artifacts.put_bytes(f"certificate:{seed}".encode())
    evidence = Evidence(
        id=f"evidence:{seed}",
        kind=EvidenceKind.OBSERVATION,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=state.context.scope_fingerprint,
        artifact=evidence_artifact,
    )
    verdict = CheckerVerdictRecord(
        id=f"checker:{seed}",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=state.context.scope_fingerprint,
        checker_id="finite-exhaustive-v1",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=verdict_artifact,
        certificate_artifact=certificate_artifact,
    )
    sdk.dispatch_batch(
        inquiry_id,
        (
            RecordEvidence(
                event_id=f"event:{evidence.id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                evidence=evidence,
            ),
            RecordCheckerVerdict(
                event_id=f"event:{verdict.id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                checker_verdict=verdict,
            ),
        ),
    )
    return CheckReference(evidence_id=evidence.id, checker_verdict_id=verdict.id)


def make_observation(
    sdk: RCI,
    parent_id: str,
    *,
    request_id: str,
    probes: tuple[str, ...],
    effect_id: str,
) -> RecoveryObservation:
    parent = sdk.inspect(parent_id)
    request = next(item for item in parent.reacquisition_requests if item.id == request_id)
    child = sdk.inspect(request.child_inquiry_id)
    measurement_ref = CheckReference(
        evidence_id=f"evidence:measurement:{request_id}",
        checker_verdict_id=f"checker:measurement:{request_id}",
    )
    competence_ref = add_valid_check(
        sdk,
        parent_id,
        seed=f"competence:{request_id}",
        proposition_id=request.pins.target_competence_id,
    )
    observation = RecoveryObservation(
        id=f"observation:{request.branch.value}",
        branch=request.branch,
        reacquisition_request_id=request.id,
        child_inquiry_id=request.child_inquiry_id,
        child_prefix_sequence=child.sequence,
        child_prefix_digest=sdk.events.stream_prefix_digest(request.child_inquiry_id),
        retention_package_id=request.retention_package_id,
        pins=request.pins,
        costs=cost_vector(effects=1, probes=len(probes)),
        logical_probe_ids=probes,
        effect_request_ids=(effect_id,),
        measurement_check=measurement_ref,
        competence_established=True,
        competence_check=competence_ref,
    )
    add_valid_check(
        sdk,
        parent_id,
        seed=f"measurement:{request_id}",
        proposition_id=observation.measurement_proposition_id,
    )
    return observation


def prepare_parent(tmp_path: Path) -> tuple[RCI, str, RetentionRegistration]:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    parent_id = "inquiry:recovery-parent"
    context = circuit_context()
    sdk.start(parent_id, context=context)
    registration = build_registration(sdk, parent_id, context)
    sdk.register_retention_package(parent_id, registration)
    return sdk, parent_id, registration


def test_g2a_structural_retrieval_and_recovery_advantage(tmp_path: Path) -> None:
    sdk, parent_id, registration = prepare_parent(tmp_path)
    runner = CliRunner()
    retrieval_run = runner.invoke(
        app,
        [
            "memory",
            "retrieve",
            parent_id,
            "--query-id",
            "query:circuit-switch",
            "--result-id",
            "result:circuit-switch",
            "--cue",
            "cue:circuit-switch",
            "--tag",
            "tag:necessity",
            "--root",
            str(tmp_path),
        ],
    )
    assert retrieval_run.exit_code == 0, retrieval_run.output
    result = sdk.inspect(parent_id).retrieval_results[0]
    assert tuple(item.package_id for item in result.hits) == (registration.package.id,)

    for args in (
        [
            "--child-inquiry-id",
            "inquiry:recovery-baseline",
            "--request-id",
            "request:baseline",
            "--branch",
            "baseline",
            "--protocol-id",
            "protocol:circuit-recovery",
        ],
        [
            "--child-inquiry-id",
            "inquiry:recovery-retained",
            "--request-id",
            "request:retained",
            "--branch",
            "retained",
            "--protocol-id",
            "protocol:circuit-recovery",
            "--retention-package-id",
            registration.package.id,
            "--scaffold-id",
            "scaffold:circuit-recovery",
        ],
    ):
        started = runner.invoke(
            app,
            ["recovery", "start", parent_id, *args, "--root", str(tmp_path)],
        )
        assert started.exit_code == 0, started.output
    baseline_probes, baseline_effect = complete_child(
        sdk,
        "inquiry:recovery-baseline",
        3,
    )
    retained_probes, retained_effect = complete_child(
        sdk,
        "inquiry:recovery-retained",
        2,
    )
    baseline_observation = make_observation(
        sdk,
        parent_id,
        request_id="request:baseline",
        probes=baseline_probes,
        effect_id=baseline_effect,
    )
    retained_observation = make_observation(
        sdk,
        parent_id,
        request_id="request:retained",
        probes=retained_probes,
        effect_id=retained_effect,
    )
    sdk.record_recovery_observation(parent_id, baseline_observation)
    sdk.record_recovery_observation(parent_id, retained_observation)

    placeholder = CheckReference(
        evidence_id="evidence:comparison:circuit",
        checker_verdict_id="checker:comparison:circuit",
    )
    candidate = sdk.compare_recovery_frontiers_for_check(
        parent_id,
        comparison_id="comparison:circuit",
        baseline_observation_ids=(baseline_observation.id,),
        retained_observation_ids=(retained_observation.id,),
        comparison_check=placeholder,
    )
    add_valid_check(
        sdk,
        parent_id,
        seed="comparison:circuit",
        proposition_id=candidate.comparison_proposition_id,
    )
    compared = runner.invoke(
        app,
        [
            "recovery",
            "compare",
            parent_id,
            "--comparison-id",
            candidate.id,
            "--baseline-observation",
            baseline_observation.id,
            "--retained-observation",
            retained_observation.id,
            "--evidence-id",
            placeholder.evidence_id,
            "--checker-verdict-id",
            placeholder.checker_verdict_id,
            "--root",
            str(tmp_path),
        ],
    )
    assert compared.exit_code == 0, compared.output
    comparison = sdk.inspect(parent_id).recovery_comparisons[0]
    assert comparison.outcome is RecoveryComparisonOutcome.STRICT_ADVANTAGE
    assert comparison.standing == "provisional_soft"
    state = sdk.inspect(parent_id)
    assert not state.lemma_versions
    assert not hasattr(comparison, "license")
    assert circuit_demonstration().expected_findings_hold
    reused_check = comparison.model_copy(update={"id": "comparison:mutated"})
    with pytest.raises(InvalidCommandError, match="independent valid check"):
        sdk.dispatch(
            RecordRecoveryComparison(
                event_id="event:comparison-mutated",
                inquiry_id=parent_id,
                occurred_at=NOW,
                comparison=reused_check,
            )
        )
    inspected = runner.invoke(
        app,
        ["recovery", "inspect", parent_id, "--root", str(tmp_path)],
    )
    assert inspected.exit_code == 0, inspected.output
    assert '"standing":"provisional_soft"' in inspected.stdout


def test_reacquisition_saga_prefixes_resume_and_cannot_collapse(tmp_path: Path) -> None:
    sdk, parent_id, _registration = prepare_parent(tmp_path)
    sdk.request_reacquisition(
        parent_id,
        request_id="request:crash",
        child_inquiry_id="inquiry:crash-child",
        branch=RecoveryBranch.BASELINE,
        recovery_protocol_id="protocol:circuit-recovery",
    )
    request_only = sdk.inspect(parent_id)
    assert request_only.reacquisition_requests
    assert not request_only.reacquisition_inquiry_links

    sdk.start_reacquisition_child(parent_id, "request:crash")
    child_started = sdk.inspect(parent_id)
    assert not child_started.reacquisition_inquiry_links
    linked = sdk.link_reacquisition_inquiry(parent_id, "request:crash")
    assert len(linked.reacquisition_inquiry_links) == 1
    resumed = sdk.start_reacquisition(
        parent_id,
        request_id="request:crash",
        child_inquiry_id="inquiry:crash-child",
        branch=RecoveryBranch.BASELINE,
        recovery_protocol_id="protocol:circuit-recovery",
    )
    assert resumed.reacquisition_inquiry_links == linked.reacquisition_inquiry_links

    parent = sdk.inspect(parent_id)
    protocol = parent.recovery_protocols[0]
    context = parent.context
    assert context is not None
    child_id = "inquiry:collapsed-child"
    request_id = "request:collapsed"
    base_manifest = sdk._inquiry_manifest_artifact(context)
    from rci.memory import ReacquisitionChildManifest

    child_manifest = ReacquisitionChildManifest(
        parent_inquiry_id=parent_id,
        request_id=request_id,
        child_inquiry_id=child_id,
        pins=protocol.pins,
        context_digest=sha256_digest(canonical_json_bytes(context)),
        policy_version=context.warrant_policy_version,
        inquiry_manifest_artifact=base_manifest,
    )
    manifest_ref = sdk.artifacts.put_bytes(canonical_json_bytes(child_manifest))
    sdk._start_with_manifest(child_id, context=context, manifest_ref=manifest_ref)
    child_stream = sdk.events.load_stream(child_id)
    request = ReacquisitionRequest(
        id=request_id,
        parent_inquiry_id=parent_id,
        child_inquiry_id=child_id,
        branch=RecoveryBranch.BASELINE,
        pins=protocol.pins,
        child_manifest_artifact=manifest_ref,
        child_inquiry_manifest_artifact=base_manifest,
        child_context_digest=sha256_digest(canonical_json_bytes(context)),
        child_policy_version=context.warrant_policy_version,
    )
    link = ReacquisitionInquiryLink(
        id="link:collapsed",
        request_id=request.id,
        parent_inquiry_id=parent_id,
        child_inquiry_id=child_id,
        child_start_event_id=child_stream.events[0].event.event_id,
        child_start_event_digest=child_stream.events[0].event_digest,
        child_prefix_sequence=child_stream.version,
        child_prefix_digest=sdk.events.stream_prefix_digest(child_id),
        child_manifest_artifact=manifest_ref,
        child_context_digest=request.child_context_digest,
    )
    with pytest.raises(SagaIntegrityError, match="owned parent request"):
        sdk.dispatch_batch(
            parent_id,
            (
                RequestReacquisition(
                    event_id="event:collapsed-request",
                    inquiry_id=parent_id,
                    occurred_at=NOW,
                    request=request,
                ),
                LinkReacquisitionInquiry(
                    event_id="event:collapsed-link",
                    inquiry_id=parent_id,
                    occurred_at=NOW,
                    link=link,
                ),
            ),
        )

    wrong_child_id = "inquiry:wrong-context-child"
    sdk.start(wrong_child_id, context=RCI.default_context())
    sdk.request_reacquisition(
        parent_id,
        request_id="request:wrong-context",
        child_inquiry_id=wrong_child_id,
        branch=RecoveryBranch.BASELINE,
        recovery_protocol_id="protocol:circuit-recovery",
    )
    with pytest.raises(IdentityConflictError, match="identity is already bound"):
        sdk.start_reacquisition_child(parent_id, "request:wrong-context")
    parent_after_wrong_request = sdk.inspect(parent_id)
    wrong_request = next(
        item
        for item in parent_after_wrong_request.reacquisition_requests
        if item.id == "request:wrong-context"
    )
    wrong_stream = sdk.events.load_stream(wrong_child_id)
    forged_wrong_context_link = ReacquisitionInquiryLink(
        id="link:wrong-context",
        request_id=wrong_request.id,
        parent_inquiry_id=parent_id,
        child_inquiry_id=wrong_child_id,
        child_start_event_id=wrong_stream.events[0].event.event_id,
        child_start_event_digest=wrong_stream.events[0].event_digest,
        child_prefix_sequence=wrong_stream.version,
        child_prefix_digest=sdk.events.stream_prefix_digest(wrong_child_id),
        child_manifest_artifact=wrong_request.child_manifest_artifact,
        child_context_digest=wrong_request.child_context_digest,
    )
    with pytest.raises(SagaIntegrityError, match="pinned request and link proof"):
        sdk.dispatch(
            LinkReacquisitionInquiry(
                event_id="event:wrong-context-link",
                inquiry_id=parent_id,
                occurred_at=NOW,
                link=forged_wrong_context_link,
            )
        )
    assert all(
        item.request_id != wrong_request.id
        for item in sdk.inspect(parent_id).reacquisition_inquiry_links
    )


def test_unfinished_or_mutated_recovery_evidence_fails_closed(tmp_path: Path) -> None:
    sdk, parent_id, _registration = prepare_parent(tmp_path)
    sdk.start_reacquisition(
        parent_id,
        request_id="request:unfinished",
        child_inquiry_id="inquiry:unfinished",
        branch=RecoveryBranch.BASELINE,
        recovery_protocol_id="protocol:circuit-recovery",
    )
    parent = sdk.inspect(parent_id)
    request = next(
        item for item in parent.reacquisition_requests if item.id == "request:unfinished"
    )
    child = sdk.inspect(request.child_inquiry_id)
    placeholder = CheckReference(
        evidence_id="evidence:measurement:unfinished",
        checker_verdict_id="checker:measurement:unfinished",
    )
    observation = RecoveryObservation(
        id="observation:unfinished",
        branch=RecoveryBranch.BASELINE,
        reacquisition_request_id=request.id,
        child_inquiry_id=request.child_inquiry_id,
        child_prefix_sequence=child.sequence,
        child_prefix_digest=sdk.events.stream_prefix_digest(request.child_inquiry_id),
        retention_package_id=None,
        pins=request.pins,
        costs=cost_vector(effects=0, probes=1),
        logical_probe_ids=("probe:invented",),
        measurement_check=placeholder,
        competence_established=False,
    )
    add_valid_check(
        sdk,
        parent_id,
        seed="measurement:unfinished",
        proposition_id=observation.measurement_proposition_id,
    )
    with pytest.raises(SagaIntegrityError, match="absent child probe"):
        sdk.record_recovery_observation(parent_id, observation)

    mutated = observation.model_copy(
        update={"child_prefix_digest": "f" * 64},
    )
    with pytest.raises(InvalidCommandError, match="independent valid check"):
        sdk.record_recovery_observation(parent_id, mutated)
