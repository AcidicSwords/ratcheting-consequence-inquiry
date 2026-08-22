from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rci.claims import (
    Claim,
    ClaimAssessment,
    ClaimRole,
    Obligation,
    ObligationDisposition,
    ObligationKind,
    ObligationStatus,
    Provenance,
)
from rci.cli import app
from rci.core import (
    AdmitClaim,
    AdmitProbe,
    EvaluateWarrant,
    OpenObligation,
    RecordCheckerVerdict,
    RecordEvidence,
    RecordObligationDisposition,
    RecordProbeObservation,
)
from rci.core.errors import InvalidCommandError
from rci.learning import (
    CandidateSupportBoundary,
    ConsolidationCandidate,
    LearnedProbeCandidate,
    ProbeAdmissionDecision,
    ProbeAdmissionOutcome,
    ProbeEvaluationProtocol,
    ProbeSample,
    RepresentationGap,
    RepresentationGapKind,
    build_probe_evaluation,
)
from rci.probes import ProbeEvent, ProbeIdentity
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


def _record_check(
    sdk: RCI,
    inquiry_id: str,
    *,
    suffix: str,
    proposition_id: str,
    proposition_kind: PropositionKind,
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


def test_g2b_consolidation_field_and_checked_probe_admission(tmp_path: Path) -> None:
    sdk = RCI(tmp_path, clock=lambda: NOW)
    inquiry_id = "inquiry:g2b-circuit"
    started = sdk.start(inquiry_id)
    assert started.context is not None
    context = started.context
    scope = sdk._scope_from_context(context)
    base_probe = ProbeIdentity(
        question_contract_key="necessity-counterexample@1.0.0",
        relational_role="counterexample",
        binding_schema_id=context.carrier_schema_ids[0],
        binding_revision=context.binding_revision,
        scope_fingerprint=context.scope_fingerprint,
        comparison_semantics_id="exact-circuit-v1",
        applicability_guard_id="always",
        protected_horizon_id=context.protected_horizon_id,
    )
    sdk.dispatch(
        AdmitProbe(
            event_id="event:base-probe",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            probe=base_probe,
        )
    )

    exception_claim = Claim(
        id="claim:older-backup-exception",
        role=ClaimRole.OBSERVATION,
        bound_args=(),
        payload="backup power supplies the lit lamp while main power is absent",
        scope=scope,
        provenance=Provenance(kind="finite_fixture", source_id="circuit:backup-route"),
        assessment=ClaimAssessment.CONTESTED,
    )
    sdk.dispatch(
        AdmitClaim(
            event_id="event:exception-claim",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            claim=exception_claim,
        )
    )
    observation_ids: list[str] = []
    for index in range(6):
        observation_id = f"episode:circuit:{index}"
        observation_ids.append(observation_id)
        sdk.dispatch(
            RecordProbeObservation(
                event_id=f"event:{observation_id}",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                observation=ProbeEvent(
                    id=observation_id,
                    probe_identity=base_probe,
                    bound_referents=(),
                    binding_revision=context.binding_revision,
                    state_revision=sdk.inspect(inquiry_id).sequence,
                    semantic_field_id="field:circuit",
                    interpretation_claim_ids=(exception_claim.id,) if index == 0 else (),
                    sequence_index=index,
                ),
            )
        )

    checkpoint = sdk.consolidation_checkpoint(
        inquiry_id, checkpoint_id="checkpoint:circuit-interleaved"
    )
    assert {item.reference.record_id for item in checkpoint.sources} >= {
        observation_ids[0],
        *observation_ids[-4:],
    }
    assert checkpoint.status.value == "ready"

    generalization_claim = Claim(
        id="claim:circuit-generalization",
        role=ClaimRole.GENERALIZATION,
        bound_args=(),
        payload="switch closure is retained as a candidate invariant",
        scope=scope,
        provenance=Provenance(kind="consolidation", source_id=checkpoint.id),
    )
    generalization_attack = Obligation(
        id="obligation:attack-generalization",
        kind=ObligationKind.CHARACTERIZE_RESIDUAL,
        carrier_id=generalization_claim.id,
        args=(),
        scope=scope,
        binding_revision=context.binding_revision,
    )
    consolidation_candidate = ConsolidationCandidate(
        id="consolidation-candidate:circuit",
        checkpoint_id=checkpoint.id,
        generalization_claim_id=generalization_claim.id,
        boundary=CandidateSupportBoundary(
            scope=scope,
            applicability_guard_id="always",
            open_dependency_obligation_ids=(generalization_attack.id,),
        ),
        challenge_obligation_ids=(generalization_attack.id,),
    )
    proposed = sdk.propose_consolidation(
        inquiry_id,
        claim=generalization_claim,
        challenge_obligations=(generalization_attack,),
        candidate=consolidation_candidate,
    )
    assert proposed.claim_by_id(generalization_claim.id) == generalization_claim
    assert proposed.current_obligation_status(generalization_attack.id) is ObligationStatus.OPEN
    assert proposed.lemma_versions == ()

    field_evaluation = sdk.evaluate_semantic_field(
        inquiry_id,
        evaluation_id="field-evaluation:circuit",
        probe_fingerprint=base_probe.fingerprint,
        safety_structure_ids=tuple(f"safety:{index:02}" for index in range(40)),
    )
    assert len(field_evaluation.included_structure_ids) == 32
    assert len(field_evaluation.overflow_structure_ids) == 8
    assert field_evaluation.status.value == "incomplete"
    assert field_evaluation.irrelevant_structure_ids == ()
    assert any(
        item.carrier_id == field_evaluation.field_id for item in sdk.inspect(inquiry_id).residuals
    )

    challenge = Obligation(
        id="obligation:attack-backup-probe",
        kind=ObligationKind.SEPARATE_CONSEQUENCE_CLASSES,
        carrier_id="proposition:backup-probe-admissible",
        args=(),
        scope=scope,
        binding_revision=context.binding_revision,
    )
    sdk.dispatch(
        OpenObligation(
            event_id="event:open-probe-attack",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            obligation=challenge,
        )
    )
    gap = RepresentationGap(
        id="gap:backup-power",
        obligation_id=started.obligations[0].id,
        state_or_claim_ids=(exception_claim.id,),
        protected_consequence_difference_id="difference:lamp-on",
        failed_probe_fingerprints=(base_probe.fingerprint,),
        kind=RepresentationGapKind.PROBE_BASIS_INADEQUATE,
        scope_fingerprint=context.scope_fingerprint,
        binding_revision=context.binding_revision,
        protected_horizon_id=context.protected_horizon_id,
    )
    sdk.record_representation_gap(inquiry_id, gap)
    learned_identity = base_probe.model_copy(
        update={
            "question_contract_key": "learned-recurrent-probe@1.0.0",
            "relational_role": "backup-power-separator",
        }
    )
    candidate = LearnedProbeCandidate(
        id="probe-candidate:backup-power",
        representation_gap_id=gap.id,
        probe_identity=learned_identity,
        generated_payload={"field": "backup_power", "comparison": "exact_boolean"},
        challenge_obligation_ids=(challenge.id,),
    )
    sdk.record_learned_probe_candidate(inquiry_id, candidate)

    with pytest.raises(InvalidCommandError, match="controller admission"):
        sdk.dispatch(
            AdmitProbe(
                event_id="event:forged-generic-admission",
                inquiry_id=inquiry_id,
                occurred_at=NOW,
                probe=learned_identity,
            )
        )

    samples = tuple(
        ProbeSample(
            observation_id=observation_ids[index],
            protected_consequence_class_id="lamp:off" if index < 2 else "lamp:on",
            existing_basis_class_id="base:same",
            candidate_value_id="backup:off" if index < 2 else "backup:on",
        )
        for index in range(4)
    )
    provisional_evaluation = build_probe_evaluation(
        evaluation_id="probe-evaluation:backup-power",
        candidate_probe_id=candidate.id,
        samples=samples,
        protocol=ProbeEvaluationProtocol(),
        redundancy_check=CheckReference(
            evidence_id="pending:redundancy", checker_verdict_id="pending:redundancy"
        ),
        protected_behavior_check=CheckReference(
            evidence_id="pending:behavior", checker_verdict_id="pending:behavior"
        ),
    )
    evaluation_proposition = provisional_evaluation.evaluation_proposition_id
    redundancy_check = _record_check(
        sdk,
        inquiry_id,
        suffix="redundancy",
        proposition_id=evaluation_proposition,
        proposition_kind=PropositionKind.RELATION,
    )
    behavior_check = _record_check(
        sdk,
        inquiry_id,
        suffix="protected-behavior",
        proposition_id=evaluation_proposition,
        proposition_kind=PropositionKind.RELATION,
    )
    evaluation = build_probe_evaluation(
        evaluation_id="probe-evaluation:backup-power",
        candidate_probe_id=candidate.id,
        samples=samples,
        protocol=ProbeEvaluationProtocol(),
        redundancy_check=redundancy_check,
        protected_behavior_check=behavior_check,
    )
    with pytest.raises(InvalidCommandError, match="exact deterministic result"):
        sdk.record_probe_evaluation(
            inquiry_id,
            evaluation.model_copy(
                update={"training_discrimination_gain": evaluation.training_discrimination_gain + 1}
            ),
        )
    sdk.record_probe_evaluation(inquiry_id, evaluation)

    discharge_check = _record_check(
        sdk,
        inquiry_id,
        suffix="challenge-discharge",
        proposition_id=challenge.carrier_id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        evidence_kind=EvidenceKind.INDEPENDENT_WITNESS,
    )
    sdk.dispatch(
        EvaluateWarrant(
            event_id="event:warrant-challenge",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            decision_id="decision:challenge-hard",
            evidence_id=discharge_check.evidence_id,
            checker_verdict_id=discharge_check.checker_verdict_id,
            proposition_id=challenge.carrier_id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope=scope,
        )
    )
    sdk.dispatch(
        RecordObligationDisposition(
            event_id="event:close-probe-attack",
            inquiry_id=inquiry_id,
            occurred_at=NOW,
            disposition=ObligationDisposition(
                id="disposition:probe-attack-satisfied",
                obligation_id=challenge.id,
                status=ObligationStatus.SATISFIED,
                reason="exact independently checked attack discharge",
                evidence_refs=("decision:challenge-hard",),
            ),
        )
    )
    final = sdk.record_probe_admission(
        inquiry_id,
        ProbeAdmissionDecision(
            id="probe-admission:backup-power",
            candidate_probe_id=candidate.id,
            evaluation_id=evaluation.id,
            outcome=ProbeAdmissionOutcome.ADMIT,
            controller_id="controller:g2b-reference",
        ),
    )
    assert learned_identity in final.admitted_probes
    assert final.lemma_versions == ()
    assert final.recovery_licenses == ()
    assert final.retained_state_views == ()
    assert sdk.replay(inquiry_id) == final
    assert sdk.export(inquiry_id) == sdk.export(inquiry_id)

    runner = CliRunner()
    consolidate = runner.invoke(
        app,
        [
            "memory",
            "consolidate",
            inquiry_id,
            "--checkpoint-id",
            "checkpoint:cli",
            "--root",
            str(tmp_path),
        ],
    )
    assert consolidate.exit_code == 0, consolidate.output
    assert json.loads(consolidate.stdout)["status"] == "ready"
    field = runner.invoke(
        app,
        [
            "field",
            "evaluate",
            inquiry_id,
            "--evaluation-id",
            "field-evaluation:cli",
            "--probe-fingerprint",
            base_probe.fingerprint,
            "--safety",
            "lamp_on",
            "--root",
            str(tmp_path),
        ],
    )
    assert field.exit_code == 0, field.output
    assert json.loads(field.stdout)["status"] == "valid"
