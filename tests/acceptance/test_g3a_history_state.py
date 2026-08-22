"""Blocking G3A-H acceptance: exact history-state without aggregate collapse."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rci.claims.models import Scope
from rci.compression import (
    BindingCarrierManifest,
    CarrierContract,
    CarrierRole,
    CompressionApplication,
    CompressionContract,
    CompressionValidation,
    ExactClaimKind,
    ExactCompressionLicense,
    ExactFixtureVerdict,
    ExactPropertyValidation,
    HistoryDerivationStatus,
    PathResidue,
    RealizedHistoryDerivation,
    RecoveryLicense,
    ReopeningOutcome,
    RepresentationGainKind,
    RepresentationReopening,
    RepresentationSuccessorDecision,
    RetentionCapabilityLink,
    SuccessorDisposition,
    ValidationOutcome,
    ValidationProperty,
    validate_order_sensitive_count,
    validate_present_answer_without_continuation,
    validate_unary_parity,
)
from rci.core import (
    AdmitProbe,
    ArtifactRef,
    EvaluateWarrant,
    InquiryContext,
    RecordCheckerVerdict,
    RecordEvidence,
)
from rci.core.errors import InvalidCommandError
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.memory import (
    DirectUseRoute,
    MemoryOwner,
    OwnedRecordType,
    RetentionPackage,
    RetentionRegistration,
    make_owned_memory_ref,
)
from rci.persistence import IntegrityError
from rci.probes import ProbeIdentity
from rci.sdk import RCI
from rci.warrant import (
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    EvidenceKind,
    PropositionKind,
    WarrantClass,
)

NOW = datetime(2026, 8, 22, tzinfo=UTC)


def _context() -> InquiryContext:
    base = RCI.default_context()
    return base.model_copy(
        update={
            "carrier_schema_ids": (
                "fixture.configuration.singleton.v1",
                "fixture.history.unary.v1",
            ),
            "protected_horizon_id": "fixture.parity-h1",
        }
    )


def _record_check(
    sdk: RCI,
    inquiry_id: str,
    *,
    suffix: str,
    proposition_id: str,
    proposition_kind: PropositionKind = PropositionKind.RELATION,
    evidence_kind: EvidenceKind = EvidenceKind.OBSERVATION,
) -> CheckReference:
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    evidence_artifact = sdk.artifacts.put_bytes(
        f"evidence:{suffix}".encode(), media_type="text/plain", encoding="utf-8"
    )
    verdict_artifact = sdk.artifacts.put_bytes(
        f"valid:{suffix}".encode(), media_type="text/plain", encoding="utf-8"
    )
    evidence = Evidence(
        id=f"evidence:{suffix}",
        kind=evidence_kind,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=state.context.scope_fingerprint,
        artifact=evidence_artifact,
    )
    verdict = CheckerVerdictRecord(
        id=f"check:{suffix}",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=state.context.scope_fingerprint,
        checker_id="finite-exhaustive-v1",
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=verdict_artifact,
        certificate_artifact=verdict_artifact,
    )
    sdk.dispatch(
        RecordEvidence(
            event_id=f"event:evidence:{suffix}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            evidence=evidence,
        )
    )
    sdk.dispatch(
        RecordCheckerVerdict(
            event_id=f"event:check:{suffix}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            checker_verdict=verdict,
        )
    )
    return CheckReference(evidence_id=evidence.id, checker_verdict_id=verdict.id)


def _record_hard_warrant(sdk: RCI, inquiry_id: str, *, suffix: str, proposition_id: str) -> str:
    reference = _record_check(
        sdk,
        inquiry_id,
        suffix=suffix,
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        evidence_kind=EvidenceKind.INDEPENDENT_WITNESS,
    )
    state = sdk.inspect(inquiry_id)
    assert state.context is not None
    decision_id = f"decision:{suffix}"
    sdk.dispatch(
        EvaluateWarrant(
            event_id=f"event:warrant:{suffix}",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            decision_id=decision_id,
            evidence_id=reference.evidence_id,
            checker_verdict_id=reference.checker_verdict_id,
            proposition_id=proposition_id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope=Scope(
                id=state.context.scope_id,
                binding_revision=state.context.binding_revision,
            ),
        )
    )
    decision = sdk.inspect(inquiry_id).warrant_decision_by_id(decision_id)
    assert decision is not None
    assert decision.warrant_class is WarrantClass.HARD
    return decision_id


def test_exact_history_state_is_licensed_without_replacing_authoritative_state(
    tmp_path: Path,
) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    inquiry_id = "inquiry:g3a-parity"
    started = sdk.start(inquiry_id, context=_context())
    assert started.context is not None
    context = started.context

    manifest_artifact = sdk.artifacts.put_bytes(
        b'{"binding":"unary-parity"}', media_type="application/json", encoding="utf-8"
    )
    configuration = CarrierContract(
        id="carrier:configuration-singleton",
        role=CarrierRole.CONFIGURATION,
        schema_id="fixture.configuration.singleton.v1",
        binding_revision=context.binding_revision,
    )
    history = CarrierContract(
        id="carrier:unary-history",
        role=CarrierRole.REALIZED_HISTORY,
        schema_id="fixture.history.unary.v1",
        binding_revision=context.binding_revision,
    )
    target = CarrierContract(
        id="carrier:parity-state",
        role=CarrierRole.PRIOR_RETAINED_STATE,
        schema_id="fixture.parity-state.v1",
        binding_revision=context.binding_revision,
    )
    manifest = BindingCarrierManifest(
        id="carrier-manifest:unary-parity",
        binding_revision=context.binding_revision,
        configuration_carrier=configuration,
        realized_history_carrier=history,
        history_derivation_policy_id="derive.accepted-unary-actions.v1",
        configuration_projection_policy_id="project.singleton.v1",
        manifest_artifact=manifest_artifact,
        provenance_refs=("fixture:unary-parity",),
    )
    state = sdk.register_binding_carriers(inquiry_id, manifest)
    history_check = _record_check(
        sdk,
        inquiry_id,
        suffix="history-five-actions",
        proposition_id="history-derivation:history:five-actions",
    )
    state = sdk.inspect(inquiry_id)
    history_artifact = sdk.artifacts.put_bytes(
        b"aaaaa", media_type="application/vnd.rci.unary-history", encoding="ascii"
    )
    derivation = RealizedHistoryDerivation(
        id="history:five-actions",
        carrier_manifest_id=manifest.id,
        source_ledger_sequence=state.sequence,
        source_prefix_digest=sdk.events.stream_prefix_digest(inquiry_id),
        status=HistoryDerivationStatus.DERIVED,
        history_artifact=history_artifact,
        realized_extension_ids=tuple(f"action:{index}" for index in range(5)),
        derivation_check=history_check,
    )
    before_tamper = sdk.export(inquiry_id)
    with pytest.raises(IntegrityError, match="prefix digest"):
        sdk.record_realized_history(
            inquiry_id,
            derivation.model_copy(update={"source_prefix_digest": "0" * 64}),
        )
    assert sdk.export(inquiry_id) == before_tamper
    sdk.record_realized_history(inquiry_id, derivation)

    contract = CompressionContract(
        id="compression-contract:unary-parity",
        carrier_manifest_id=manifest.id,
        source_carrier_id=history.id,
        target_carrier=target,
        binding_revision=context.binding_revision,
        scope_fingerprint=context.scope_fingerprint,
        protected_horizon_id=context.protected_horizon_id,
        continuation_operation_ids=("append:a",),
        consequence_query_ids=("consequence:parity",),
        equality_semantics_id="exact.boolean.v1",
        recovery_semantics_ids=("path-residue-or-reacquire.v1",),
        claim_kinds=(
            ExactClaimKind.COARSEST_EXACT_QUOTIENT,
            ExactClaimKind.CONSEQUENCE_SUFFICIENT,
            ExactClaimKind.EXECUTABLE_RETAINED_STATE,
        ),
        representation_policy_id="unary-parity.base-step.v1",
        provenance_refs=("fixture:unary-parity",),
    )
    sdk.register_compression_contract(inquiry_id, contract)

    checks: dict[ValidationProperty, CheckReference] = {}
    for property_kind in ValidationProperty:
        checks[property_kind] = _record_check(
            sdk,
            inquiry_id,
            suffix=f"validation-{property_kind.value}",
            proposition_id=f"compression-property:{contract.id}:{property_kind.value}",
        )
    validation_artifact = sdk.artifacts.put_bytes(
        canonical_json_bytes(
            validate_unary_parity(protect_parity=True, singleton_representation=False).__dict__
        ),
        media_type="application/json",
        encoding="utf-8",
    )
    validation = CompressionValidation(
        id="compression-validation:unary-parity",
        contract_id=contract.id,
        contract_fingerprint=sha256_digest(canonical_json_bytes(contract)),
        properties=tuple(
            ExactPropertyValidation(
                property=property_kind,
                outcome=ValidationOutcome.VALID,
                proposition_id=f"compression-property:{contract.id}:{property_kind.value}",
                check=checks[property_kind],
            )
            for property_kind in ValidationProperty
        ),
        validator_id="checker:finite-transition-congruence",
        validator_version="1",
        validation_artifact=validation_artifact,
    )
    sdk.record_compression_validation(inquiry_id, validation)

    with pytest.raises(InvalidCommandError, match="hard warrant"):
        sdk.grant_exact_compression_license(
            inquiry_id,
            ExactCompressionLicense(
                id="compression-license:forged",
                contract_id=contract.id,
                validation_id=validation.id,
                warrant_decision_id="decision:self-asserted",
                policy_version=context.warrant_policy_version,
                granted_capability_ids=("capability:parity-evaluate",),
            ),
        )

    license_warrant = _record_hard_warrant(
        sdk,
        inquiry_id,
        suffix="parity-license",
        proposition_id=f"compression-license:{validation.id}",
    )
    license_record = ExactCompressionLicense(
        id="compression-license:parity",
        contract_id=contract.id,
        validation_id=validation.id,
        warrant_decision_id=license_warrant,
        policy_version=context.warrant_policy_version,
        granted_capability_ids=("capability:parity-evaluate", "capability:parity-update"),
    )
    sdk.grant_exact_compression_license(inquiry_id, license_record)
    retained = sdk.artifacts.put_bytes(
        b"1", media_type="application/vnd.rci.parity-state", encoding="ascii"
    )
    residue = PathResidue(
        id="path-residue:exact-unary-history",
        contract_id=contract.id,
        source_history_derivation_id=derivation.id,
        residue_artifact=history_artifact,
        distinction_ids=("distinction:exact-length",),
        provenance_refs=("fixture:unary-parity",),
    )
    application = CompressionApplication(
        id="compression-application:five-actions",
        license_id=license_record.id,
        source_history_derivation_id=derivation.id,
        source_artifact=history_artifact,
        retained_state_artifact=retained,
        retained_state_fingerprint=retained.digest,
        path_residue_ids=(residue.id,),
        applied_representation_id="q:unary-parity",
        provenance_refs=("fixture:unary-parity",),
    )
    state = sdk.record_compression_application(inquiry_id, application, path_residues=(residue,))
    assert state.status == "active"
    assert state.inquiry_id == inquiry_id
    assert state.compression_applications == (application,)
    assert application.source_artifact.size == 5
    assert application.retained_state_artifact.size == 1
    assert state.retained_state_views[0].retained_state_artifact == retained
    assert state.retained_state_views[0].capability_ids == ()
    assert sdk.replay(inquiry_id) == state
    assert sdk.export(inquiry_id) == sdk.events.export_stream(inquiry_id)

    probe = ProbeIdentity(
        question_contract_key="obligation-characterization@1.0.0",
        relational_role="fixture-cue",
        binding_schema_id=history.schema_id,
        binding_revision=context.binding_revision,
        scope_fingerprint=context.scope_fingerprint,
        comparison_semantics_id="exact-unary-v1",
        applicability_guard_id="always",
        protected_horizon_id=context.protected_horizon_id,
    )
    sdk.dispatch(
        AdmitProbe(
            event_id="event:admit-parity-cue",
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
    route = DirectUseRoute(
        id="route:parity-direct",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        source_refs=(probe_ref,),
        provenance_refs=("fixture:unary-parity",),
        present_use_contract_id="present-use:parity-v1",
    )
    package = RetentionPackage(
        id="retention:parity",
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
        owned_refs=(probe_ref,),
        direct_use_route_ids=(route.id,),
        provenance_refs=("fixture:unary-parity",),
    )
    sdk.register_retention_package(
        inquiry_id,
        RetentionRegistration(package=package, direct_use_routes=(route,)),
    )
    assert sdk.inspect(inquiry_id).retained_state_views[0].capability_ids == ()
    recovery_warrant = _record_hard_warrant(
        sdk,
        inquiry_id,
        suffix="parity-recovery",
        proposition_id="recovery-license:parity",
    )
    recovery_license = RecoveryLicense(
        id="parity",
        compression_application_id=application.id,
        retention_package_id=package.id,
        route_id=route.id,
        recovery_semantics_id="present-use:parity-v1",
        warrant_decision_id=recovery_warrant,
        policy_version=context.warrant_policy_version,
    )
    sdk.grant_recovery_license(inquiry_id, recovery_license)
    assert sdk.inspect(inquiry_id).retained_state_views[0].capability_ids == ()
    capability_link = RetentionCapabilityLink(
        id="capability-link:parity",
        retention_package_id=package.id,
        route_id=route.id,
        compression_application_id=application.id,
        recovery_license_id=recovery_license.id,
    )
    linked = sdk.link_retention_capability(inquiry_id, capability_link)
    assert linked.retention_packages == (package,)
    assert linked.retained_state_views[0].capability_ids == license_record.granted_capability_ids

    candidate_license = ExactCompressionLicense(
        id="compression-license:parity-successor",
        contract_id=contract.id,
        validation_id=validation.id,
        warrant_decision_id=license_warrant,
        policy_version=context.warrant_policy_version,
        granted_capability_ids=(
            "capability:parity-evaluate",
            "capability:parity-separator",
            "capability:parity-update",
        ),
        predecessor_license_id=license_record.id,
    )
    sdk.grant_exact_compression_license(inquiry_id, candidate_license)
    successor_warrant = _record_hard_warrant(
        sdk,
        inquiry_id,
        suffix="parity-successor",
        proposition_id="representation-successor:successor:parity-v2",
    )
    successor = RepresentationSuccessorDecision(
        id="successor:parity-v2",
        incumbent_license_id=license_record.id,
        candidate_license_id=candidate_license.id,
        disposition=SuccessorDisposition.REPLACE,
        preserved_capability_ids=license_record.granted_capability_ids,
        gain_kinds=(RepresentationGainKind.SEPARATOR,),
        warrant_decision_id=successor_warrant,
        reason="independently checked separator while preserving predecessor capabilities",
    )
    with pytest.raises(InvalidCommandError, match="every predecessor capability"):
        sdk.decide_representation_successor(
            inquiry_id,
            successor.model_copy(
                update={
                    "id": "successor:forged-loss",
                    "preserved_capability_ids": ("capability:parity-evaluate",),
                    "warrant_decision_id": successor_warrant,
                }
            ),
        )
    sdk.decide_representation_successor(inquiry_id, successor)

    reopening_check = _record_check(
        sdk,
        inquiry_id,
        suffix="parity-reopening",
        proposition_id="representation-reopening:reopening:parity-h2",
    )
    reopening = RepresentationReopening(
        id="reopening:parity-h2",
        license_id=candidate_license.id,
        prior_horizon_id=context.protected_horizon_id,
        expanded_horizon_id="fixture.parity-plus-order-h2",
        factorization_failure_check=reopening_check,
        counterexample_artifact=sdk.artifacts.put_bytes(
            b'{"left":"ab","right":"ba"}',
            media_type="application/json",
            encoding="utf-8",
        ),
        outcome=ReopeningOutcome.RECOVERABLE,
        path_residue_id=residue.id,
    )
    reopened_state = sdk.reopen_representation(inquiry_id, reopening)
    assert reopened_state.representation_successor_decisions == (successor,)
    assert reopened_state.representation_reopenings == (reopening,)
    assert sdk.replay(inquiry_id) == reopened_state


def test_fixtures_reopening_unknown_and_successor_ratchet_are_fail_closed() -> None:
    assert (
        validate_unary_parity(protect_parity=True, singleton_representation=False).verdict
        is ExactFixtureVerdict.VALID
    )
    reopened = validate_unary_parity(protect_parity=True, singleton_representation=True)
    assert reopened.verdict is ExactFixtureVerdict.INVALID
    assert reopened.counterexample == ("", "a")
    assert reopened.configuration_equal
    order = validate_order_sensitive_count()
    assert order.verdict is ExactFixtureVerdict.INVALID
    assert order.counterexample == ("ab", "ba")
    assert order.configuration_equal and order.event_count_equal
    present_only = validate_present_answer_without_continuation()
    assert present_only.factorization
    assert not present_only.continuation_compatible
    assert present_only.verdict is ExactFixtureVerdict.INVALID

    target = CarrierContract(
        id="carrier:narrow-answer",
        role=CarrierRole.OTHER_DECLARED,
        schema_id="fixture.answer.v1",
        binding_revision="binding-v1",
    )
    narrow_contract = CompressionContract(
        id="compression-contract:answer-only",
        carrier_manifest_id="carrier-manifest:fixture",
        source_carrier_id="carrier:history",
        target_carrier=target,
        binding_revision="binding-v1",
        scope_fingerprint="0" * 64,
        protected_horizon_id="h0",
        continuation_operation_ids=(),
        consequence_query_ids=("query:present",),
        equality_semantics_id="exact.v1",
        recovery_semantics_ids=(),
        claim_kinds=(ExactClaimKind.CONSEQUENCE_SUFFICIENT,),
        representation_policy_id="answer-only.v1",
        provenance_refs=("fixture:continuation-narrowing",),
    )
    assert ExactClaimKind.EXECUTABLE_RETAINED_STATE not in narrow_contract.claim_kinds
    with pytest.raises(ValueError, match="continuation family"):
        CompressionContract.model_validate(
            {
                **narrow_contract.model_dump(),
                "claim_kinds": (
                    ExactClaimKind.CONSEQUENCE_SUFFICIENT,
                    ExactClaimKind.EXECUTABLE_RETAINED_STATE,
                ),
            },
            strict=True,
        )

    incomparable = RepresentationSuccessorDecision(
        id="successor:frontier",
        incumbent_license_id="license:old",
        candidate_license_id="license:new",
        disposition=SuccessorDisposition.INCOMPARABLE,
        preserved_capability_ids=(),
        reason="neither representation preserves and strictly improves the other",
    )
    assert incomparable.disposition is SuccessorDisposition.INCOMPARABLE

    with pytest.raises(ValueError, match="typed gain and independent warrant"):
        RepresentationSuccessorDecision(
            id="successor:forged",
            incumbent_license_id="license:old",
            candidate_license_id="license:new",
            disposition=SuccessorDisposition.REPLACE,
            preserved_capability_ids=("capability:a",),
            reason="newer is not evidence",
        )
    unknown = RepresentationReopening(
        id="reopening:unknown",
        license_id="license:old",
        prior_horizon_id="h0",
        expanded_horizon_id="h1",
        factorization_failure_check=CheckReference(
            evidence_id="evidence:gap", checker_verdict_id="check:gap"
        ),
        counterexample_artifact=ArtifactRef(
            digest="0" * 64,
            size=0,
            media_type="application/json",
            encoding="utf-8",
        ),
        outcome=ReopeningOutcome.UNKNOWN,
    )
    assert unknown.outcome is ReopeningOutcome.UNKNOWN
    assert RepresentationGainKind.SEPARATOR.value == "separator"
