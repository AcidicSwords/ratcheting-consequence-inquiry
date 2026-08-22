"""Versioned immutable event vocabulary for the Foundation aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator

from rci.backlog.models import BacklogEffect
from rci.claims.models import (
    Candidate,
    Claim,
    Conflict,
    Correction,
    GuardChange,
    Obligation,
    ObligationDisposition,
    Residual,
    Scope,
)
from rci.compression.models import (
    BindingCarrierManifest,
    CompressionApplication,
    CompressionContract,
    CompressionValidation,
    ExactCompressionLicense,
    PathResidue,
    RealizedHistoryDerivation,
    RecoveryLicense,
    RepresentationReopening,
    RepresentationSuccessorDecision,
    RetentionCapabilityLink,
)
from rci.core.effects import (
    AttemptOutcome,
    DecodeOutcome,
    EffectAttemptPlan,
    EffectRequest,
    NoAttemptDisposition,
)
from rci.core.model import ArtifactRef, FrozenModel, Identifier, InquiryContext, require_utc
from rci.core.planning import StepPlan
from rci.learning.models import (
    ConsolidationCandidate,
    ConsolidationCheckpoint,
    LearnedProbeCandidate,
    MemoryPatchCandidate,
    ProbeAdmissionDecision,
    ProbeEvaluation,
    ReconsolidationLink,
    RepresentationGap,
    SemanticFieldEvaluation,
)
from rci.memory.models import (
    ReacquisitionInquiryLink,
    ReacquisitionRequest,
    RecoveryComparison,
    RecoveryObservation,
    RetentionRegistration,
    RetrievalQuery,
    RetrievalResult,
    StructuralRetrievalPolicy,
)
from rci.probes.models import (
    CognitiveAttemptPlan,
    Mismatch,
    PredictionSeal,
    ProbeEvent,
    ProbeIdentity,
    Reconstruction,
    SemanticDelta,
)
from rci.warrant.models import (
    CheckerVerdictRecord,
    Evidence,
    LemmaSupport,
    LemmaVersion,
    Nogood,
    NogoodStandingChange,
    PromotionLink,
    SupportRouteStandingChange,
    WarrantDecisionRecord,
)


class EventBase(FrozenModel):
    event_id: Identifier
    inquiry_id: Identifier
    occurred_at: datetime
    schema_version: Literal[1] = 1

    _validate_occurred_at = field_validator("occurred_at")(require_utc)


class InquiryStarted(EventBase):
    kind: Literal["inquiry_started"] = "inquiry_started"
    manifest_artifact: ArtifactRef
    policy_version: Identifier
    context: InquiryContext


class BacklogEffectRecorded(EventBase):
    kind: Literal["backlog_effect_recorded"] = "backlog_effect_recorded"
    effect: BacklogEffect


class StepPlanRecorded(EventBase):
    kind: Literal["step_plan_recorded"] = "step_plan_recorded"
    plan: StepPlan


class EffectRequested(EventBase):
    kind: Literal["effect_requested"] = "effect_requested"
    request: EffectRequest


class EffectAttemptPlanned(EventBase):
    kind: Literal["effect_attempt_planned"] = "effect_attempt_planned"
    plan: EffectAttemptPlan


class EffectAttemptStarted(EventBase):
    kind: Literal["effect_attempt_started"] = "effect_attempt_started"
    attempt_id: Identifier


class EffectNoAttemptDispositionRecorded(EventBase):
    kind: Literal["effect_no_attempt_disposition_recorded"] = (
        "effect_no_attempt_disposition_recorded"
    )
    disposition: NoAttemptDisposition


class EffectAttemptOutcomeRecorded(EventBase):
    kind: Literal["effect_attempt_outcome_recorded"] = "effect_attempt_outcome_recorded"
    request_id: Identifier
    outcome: AttemptOutcome


class EffectDecodeOutcomeRecorded(EventBase):
    kind: Literal["effect_decode_outcome_recorded"] = "effect_decode_outcome_recorded"
    request_id: Identifier
    outcome: DecodeOutcome


class EffectResultAccepted(EventBase):
    kind: Literal["effect_result_accepted"] = "effect_result_accepted"
    request_id: Identifier
    decoded_outcome_id: Identifier


class ClaimAdmitted(EventBase):
    kind: Literal["claim_admitted"] = "claim_admitted"
    claim: Claim
    derived_conflicts: tuple[Conflict, ...] = ()
    derived_obligations: tuple[Obligation, ...] = ()


class ObligationOpened(EventBase):
    kind: Literal["obligation_opened"] = "obligation_opened"
    obligation: Obligation


class ObligationDispositionRecorded(EventBase):
    kind: Literal["obligation_disposition_recorded"] = "obligation_disposition_recorded"
    disposition: ObligationDisposition


class CandidateRecorded(EventBase):
    kind: Literal["candidate_recorded"] = "candidate_recorded"
    candidate: Candidate


class ResidualRecorded(EventBase):
    kind: Literal["residual_recorded"] = "residual_recorded"
    residual: Residual


class CorrectionAppended(EventBase):
    kind: Literal["correction_appended"] = "correction_appended"
    correction: Correction


class GuardStandingChanged(EventBase):
    kind: Literal["guard_standing_changed"] = "guard_standing_changed"
    change: GuardChange


class NogoodRecorded(EventBase):
    kind: Literal["nogood_recorded"] = "nogood_recorded"
    nogood: Nogood


class SupportRouteStandingChanged(EventBase):
    kind: Literal["support_route_standing_changed"] = "support_route_standing_changed"
    change: SupportRouteStandingChange


class NogoodStandingChanged(EventBase):
    kind: Literal["nogood_standing_changed"] = "nogood_standing_changed"
    change: NogoodStandingChange


class EvidenceRecorded(EventBase):
    kind: Literal["evidence_recorded"] = "evidence_recorded"
    evidence: Evidence


class CheckerVerdictRecorded(EventBase):
    kind: Literal["checker_verdict_recorded"] = "checker_verdict_recorded"
    checker_verdict: CheckerVerdictRecord


class WarrantDecisionRecorded(EventBase):
    kind: Literal["warrant_decision_recorded"] = "warrant_decision_recorded"
    scope: Scope
    decision: WarrantDecisionRecord


class LemmaPromoted(EventBase):
    kind: Literal["lemma_promoted"] = "lemma_promoted"
    version: LemmaVersion
    support: LemmaSupport
    link: PromotionLink


class ProbeAdmitted(EventBase):
    kind: Literal["probe_admitted"] = "probe_admitted"
    probe: ProbeIdentity


class CognitivePlanRecorded(EventBase):
    kind: Literal["cognitive_plan_recorded"] = "cognitive_plan_recorded"
    plan: CognitiveAttemptPlan


class PredictionSealed(EventBase):
    kind: Literal["prediction_sealed"] = "prediction_sealed"
    prediction: PredictionSeal


class ProbeObservationRecorded(EventBase):
    kind: Literal["probe_observation_recorded"] = "probe_observation_recorded"
    observation: ProbeEvent


class ReconstructionRecorded(EventBase):
    kind: Literal["reconstruction_recorded"] = "reconstruction_recorded"
    reconstruction: Reconstruction


class MismatchRecorded(EventBase):
    kind: Literal["mismatch_recorded"] = "mismatch_recorded"
    mismatch: Mismatch


class SemanticDeltaCommitted(EventBase):
    kind: Literal["semantic_delta_committed"] = "semantic_delta_committed"
    delta: SemanticDelta


class RetentionPackageRegistered(EventBase):
    kind: Literal["retention_package_registered"] = "retention_package_registered"
    registration: RetentionRegistration


class RetrievalCompleted(EventBase):
    kind: Literal["retrieval_completed"] = "retrieval_completed"
    policy: StructuralRetrievalPolicy
    query: RetrievalQuery
    result: RetrievalResult


class ReacquisitionRequested(EventBase):
    kind: Literal["reacquisition_requested"] = "reacquisition_requested"
    request: ReacquisitionRequest


class ReacquisitionInquiryLinked(EventBase):
    kind: Literal["reacquisition_inquiry_linked"] = "reacquisition_inquiry_linked"
    link: ReacquisitionInquiryLink


class RecoveryObservationRecorded(EventBase):
    kind: Literal["recovery_observation_recorded"] = "recovery_observation_recorded"
    observation: RecoveryObservation


class RecoveryComparisonRecorded(EventBase):
    kind: Literal["recovery_comparison_recorded"] = "recovery_comparison_recorded"
    comparison: RecoveryComparison


class ConsolidationCheckpointRecorded(EventBase):
    kind: Literal["consolidation_checkpoint_recorded"] = "consolidation_checkpoint_recorded"
    checkpoint: ConsolidationCheckpoint


class ConsolidationCandidateRecorded(EventBase):
    kind: Literal["consolidation_candidate_recorded"] = "consolidation_candidate_recorded"
    candidate: ConsolidationCandidate


class MemoryPatchCandidateRecorded(EventBase):
    kind: Literal["memory_patch_candidate_recorded"] = "memory_patch_candidate_recorded"
    candidate: MemoryPatchCandidate


class ReconsolidationLinked(EventBase):
    kind: Literal["reconsolidation_linked"] = "reconsolidation_linked"
    link: ReconsolidationLink


class SemanticFieldEvaluationRecorded(EventBase):
    kind: Literal["semantic_field_evaluation_recorded"] = "semantic_field_evaluation_recorded"
    evaluation: SemanticFieldEvaluation
    overflow_residual: Residual | None = None


class RepresentationGapRecorded(EventBase):
    kind: Literal["representation_gap_recorded"] = "representation_gap_recorded"
    gap: RepresentationGap


class LearnedProbeCandidateRecorded(EventBase):
    kind: Literal["learned_probe_candidate_recorded"] = "learned_probe_candidate_recorded"
    candidate: LearnedProbeCandidate


class ProbeEvaluationRecorded(EventBase):
    kind: Literal["probe_evaluation_recorded"] = "probe_evaluation_recorded"
    evaluation: ProbeEvaluation


class ProbeAdmissionDecisionRecorded(EventBase):
    kind: Literal["probe_admission_decision_recorded"] = "probe_admission_decision_recorded"
    decision: ProbeAdmissionDecision


class BindingCarrierManifestRegistered(EventBase):
    kind: Literal["binding_carrier_manifest_registered"] = "binding_carrier_manifest_registered"
    manifest: BindingCarrierManifest


class RealizedHistoryDerivationRecorded(EventBase):
    kind: Literal["realized_history_derivation_recorded"] = "realized_history_derivation_recorded"
    derivation: RealizedHistoryDerivation


class CompressionContractRegistered(EventBase):
    kind: Literal["compression_contract_registered"] = "compression_contract_registered"
    contract: CompressionContract


class CompressionValidationRecorded(EventBase):
    kind: Literal["compression_validation_recorded"] = "compression_validation_recorded"
    validation: CompressionValidation


class ExactCompressionLicenseGranted(EventBase):
    kind: Literal["exact_compression_license_granted"] = "exact_compression_license_granted"
    license: ExactCompressionLicense


class CompressionApplicationRecorded(EventBase):
    kind: Literal["compression_application_recorded"] = "compression_application_recorded"
    application: CompressionApplication
    path_residues: tuple[PathResidue, ...] = ()


class RecoveryLicenseGranted(EventBase):
    kind: Literal["recovery_license_granted"] = "recovery_license_granted"
    license: RecoveryLicense


class RetentionCapabilityLinked(EventBase):
    kind: Literal["retention_capability_linked"] = "retention_capability_linked"
    link: RetentionCapabilityLink


class RepresentationSuccessorDecided(EventBase):
    kind: Literal["representation_successor_decided"] = "representation_successor_decided"
    decision: RepresentationSuccessorDecision


class RepresentationReopened(EventBase):
    kind: Literal["representation_reopened"] = "representation_reopened"
    reopening: RepresentationReopening


DomainEvent = Annotated[
    InquiryStarted
    | BacklogEffectRecorded
    | StepPlanRecorded
    | EffectRequested
    | EffectAttemptPlanned
    | EffectAttemptStarted
    | EffectNoAttemptDispositionRecorded
    | EffectAttemptOutcomeRecorded
    | EffectDecodeOutcomeRecorded
    | EffectResultAccepted
    | ClaimAdmitted
    | ObligationOpened
    | ObligationDispositionRecorded
    | CandidateRecorded
    | ResidualRecorded
    | CorrectionAppended
    | GuardStandingChanged
    | NogoodRecorded
    | SupportRouteStandingChanged
    | NogoodStandingChanged
    | EvidenceRecorded
    | CheckerVerdictRecorded
    | WarrantDecisionRecorded
    | LemmaPromoted
    | ProbeAdmitted
    | CognitivePlanRecorded
    | PredictionSealed
    | ProbeObservationRecorded
    | ReconstructionRecorded
    | MismatchRecorded
    | SemanticDeltaCommitted
    | RetentionPackageRegistered
    | RetrievalCompleted
    | ReacquisitionRequested
    | ReacquisitionInquiryLinked
    | RecoveryObservationRecorded
    | RecoveryComparisonRecorded
    | ConsolidationCheckpointRecorded
    | ConsolidationCandidateRecorded
    | MemoryPatchCandidateRecorded
    | ReconsolidationLinked
    | SemanticFieldEvaluationRecorded
    | RepresentationGapRecorded
    | LearnedProbeCandidateRecorded
    | ProbeEvaluationRecorded
    | ProbeAdmissionDecisionRecorded
    | BindingCarrierManifestRegistered
    | RealizedHistoryDerivationRecorded
    | CompressionContractRegistered
    | CompressionValidationRecorded
    | ExactCompressionLicenseGranted
    | CompressionApplicationRecorded
    | RecoveryLicenseGranted
    | RetentionCapabilityLinked
    | RepresentationSuccessorDecided
    | RepresentationReopened,
    Field(discriminator="kind"),
]
