"""Commands accepted by the pure Foundation aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, field_validator

from rci.backlog.models import BacklogEffect
from rci.claims.models import (
    Candidate,
    Claim,
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
from rci.project.models import (
    CandidateEnvironmentManifest,
    CapabilityFrontier,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    DevelopmentEvidence,
    GoalAdmissionDecision,
    ImplementationGoalCandidate,
    ImplementationGoalContract,
    IndependentReview,
    MethodAdmissionDecision,
    MethodBindingCandidate,
    ProjectAnchor,
    ProjectSuccessorDecision,
    PromotionDecision,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
    RecursiveCycleCheckpoint,
    RecursiveStopDisposition,
)
from rci.warrant.models import (
    Applicability,
    CheckerVerdictRecord,
    Evidence,
    Nogood,
    NogoodStandingChange,
    PropositionKind,
    SupportRoute,
    SupportRouteStandingChange,
)


class CommandBase(FrozenModel):
    event_id: Identifier
    inquiry_id: Identifier
    occurred_at: datetime

    _validate_occurred_at = field_validator("occurred_at")(require_utc)


class StartInquiry(CommandBase):
    kind: Literal["start_inquiry"] = "start_inquiry"
    manifest_artifact: ArtifactRef
    policy_version: Identifier
    context: InquiryContext


class RecordBacklogEffect(CommandBase):
    """Append one constitutionally allowlisted, checked local backlog effect."""

    kind: Literal["record_backlog_effect"] = "record_backlog_effect"
    effect: BacklogEffect


class RecordStepPlan(CommandBase):
    kind: Literal["record_step_plan"] = "record_step_plan"
    plan: StepPlan


class RequestEffect(CommandBase):
    kind: Literal["request_effect"] = "request_effect"
    request: EffectRequest


class PlanEffectAttempt(CommandBase):
    kind: Literal["plan_effect_attempt"] = "plan_effect_attempt"
    plan: EffectAttemptPlan


class StartEffectAttempt(CommandBase):
    kind: Literal["start_effect_attempt"] = "start_effect_attempt"
    attempt_id: Identifier


class RecordNoAttemptDisposition(CommandBase):
    kind: Literal["record_no_attempt_disposition"] = "record_no_attempt_disposition"
    disposition: NoAttemptDisposition


class RecordAttemptOutcome(CommandBase):
    kind: Literal["record_attempt_outcome"] = "record_attempt_outcome"
    request_id: Identifier
    outcome: AttemptOutcome


class RecordDecodeOutcome(CommandBase):
    kind: Literal["record_decode_outcome"] = "record_decode_outcome"
    request_id: Identifier
    outcome: DecodeOutcome


class AcceptEffectResult(CommandBase):
    kind: Literal["accept_effect_result"] = "accept_effect_result"
    request_id: Identifier
    decoded_outcome_id: Identifier


class AdmitClaim(CommandBase):
    kind: Literal["admit_claim"] = "admit_claim"
    claim: Claim


class OpenObligation(CommandBase):
    kind: Literal["open_obligation"] = "open_obligation"
    obligation: Obligation


class RecordObligationDisposition(CommandBase):
    kind: Literal["record_obligation_disposition"] = "record_obligation_disposition"
    disposition: ObligationDisposition


class RecordCandidate(CommandBase):
    kind: Literal["record_candidate"] = "record_candidate"
    candidate: Candidate


class RecordResidual(CommandBase):
    kind: Literal["record_residual"] = "record_residual"
    residual: Residual


class AppendCorrection(CommandBase):
    kind: Literal["append_correction"] = "append_correction"
    correction: Correction


class ChangeGuardStanding(CommandBase):
    kind: Literal["change_guard_standing"] = "change_guard_standing"
    change: GuardChange


class RecordNogood(CommandBase):
    kind: Literal["record_nogood"] = "record_nogood"
    nogood: Nogood


class ChangeSupportRouteStanding(CommandBase):
    kind: Literal["change_support_route_standing"] = "change_support_route_standing"
    change: SupportRouteStandingChange


class ChangeNogoodStanding(CommandBase):
    kind: Literal["change_nogood_standing"] = "change_nogood_standing"
    change: NogoodStandingChange


class RecordEvidence(CommandBase):
    kind: Literal["record_evidence"] = "record_evidence"
    evidence: Evidence


class RecordCheckerVerdict(CommandBase):
    kind: Literal["record_checker_verdict"] = "record_checker_verdict"
    checker_verdict: CheckerVerdictRecord


class EvaluateWarrant(CommandBase):
    kind: Literal["evaluate_warrant"] = "evaluate_warrant"
    decision_id: Identifier
    evidence_id: Identifier
    checker_verdict_id: Identifier
    proposition_id: Identifier
    proposition_kind: PropositionKind
    scope: Scope


class PromoteClaim(CommandBase):
    kind: Literal["promote_claim"] = "promote_claim"
    promotion_id: Identifier
    lemma_id: Identifier
    relation_id: Identifier
    proposition_kind: PropositionKind
    scope: Scope
    applicability: Applicability
    support_routes: tuple[SupportRoute, ...]
    warrant_decision_id: Identifier
    provenance_refs: tuple[Identifier, ...]
    source_claim_ids: tuple[Identifier, ...]
    predecessor_refs: tuple[Identifier, ...] = ()


class AdmitProbe(CommandBase):
    kind: Literal["admit_probe"] = "admit_probe"
    probe: ProbeIdentity


class RecordCognitivePlan(CommandBase):
    kind: Literal["record_cognitive_plan"] = "record_cognitive_plan"
    plan: CognitiveAttemptPlan


class SealPrediction(CommandBase):
    kind: Literal["seal_prediction"] = "seal_prediction"
    prediction: PredictionSeal


class RecordProbeObservation(CommandBase):
    kind: Literal["record_probe_observation"] = "record_probe_observation"
    observation: ProbeEvent


class RecordReconstruction(CommandBase):
    kind: Literal["record_reconstruction"] = "record_reconstruction"
    reconstruction: Reconstruction


class RecordMismatch(CommandBase):
    kind: Literal["record_mismatch"] = "record_mismatch"
    mismatch: Mismatch


class CommitSemanticDelta(CommandBase):
    kind: Literal["commit_semantic_delta"] = "commit_semantic_delta"
    delta: SemanticDelta


class RegisterRetentionPackage(CommandBase):
    kind: Literal["register_retention_package"] = "register_retention_package"
    registration: RetentionRegistration


class RunRetrieval(CommandBase):
    kind: Literal["run_retrieval"] = "run_retrieval"
    result_id: Identifier
    query: RetrievalQuery


class RequestReacquisition(CommandBase):
    kind: Literal["request_reacquisition"] = "request_reacquisition"
    request: ReacquisitionRequest


class LinkReacquisitionInquiry(CommandBase):
    kind: Literal["link_reacquisition_inquiry"] = "link_reacquisition_inquiry"
    link: ReacquisitionInquiryLink


class RecordRecoveryObservation(CommandBase):
    kind: Literal["record_recovery_observation"] = "record_recovery_observation"
    observation: RecoveryObservation


class RecordRecoveryComparison(CommandBase):
    kind: Literal["record_recovery_comparison"] = "record_recovery_comparison"
    comparison: RecoveryComparison


class RecordConsolidationCheckpoint(CommandBase):
    kind: Literal["record_consolidation_checkpoint"] = "record_consolidation_checkpoint"
    checkpoint: ConsolidationCheckpoint


class RecordConsolidationCandidate(CommandBase):
    kind: Literal["record_consolidation_candidate"] = "record_consolidation_candidate"
    candidate: ConsolidationCandidate


class RecordMemoryPatchCandidate(CommandBase):
    kind: Literal["record_memory_patch_candidate"] = "record_memory_patch_candidate"
    candidate: MemoryPatchCandidate


class RecordReconsolidationLink(CommandBase):
    kind: Literal["record_reconsolidation_link"] = "record_reconsolidation_link"
    link: ReconsolidationLink


class RecordSemanticFieldEvaluation(CommandBase):
    kind: Literal["record_semantic_field_evaluation"] = "record_semantic_field_evaluation"
    evaluation: SemanticFieldEvaluation
    overflow_residual: Residual | None = None


class RecordRepresentationGap(CommandBase):
    kind: Literal["record_representation_gap"] = "record_representation_gap"
    gap: RepresentationGap


class RecordLearnedProbeCandidate(CommandBase):
    kind: Literal["record_learned_probe_candidate"] = "record_learned_probe_candidate"
    candidate: LearnedProbeCandidate


class RecordProbeEvaluation(CommandBase):
    kind: Literal["record_probe_evaluation"] = "record_probe_evaluation"
    evaluation: ProbeEvaluation


class RecordProbeAdmissionDecision(CommandBase):
    kind: Literal["record_probe_admission_decision"] = "record_probe_admission_decision"
    decision: ProbeAdmissionDecision


class RegisterBindingCarrierManifest(CommandBase):
    kind: Literal["register_binding_carrier_manifest"] = "register_binding_carrier_manifest"
    manifest: BindingCarrierManifest


class RecordRealizedHistoryDerivation(CommandBase):
    kind: Literal["record_realized_history_derivation"] = "record_realized_history_derivation"
    derivation: RealizedHistoryDerivation


class RegisterCompressionContract(CommandBase):
    kind: Literal["register_compression_contract"] = "register_compression_contract"
    contract: CompressionContract


class RecordCompressionValidation(CommandBase):
    kind: Literal["record_compression_validation"] = "record_compression_validation"
    validation: CompressionValidation


class GrantExactCompressionLicense(CommandBase):
    kind: Literal["grant_exact_compression_license"] = "grant_exact_compression_license"
    license: ExactCompressionLicense


class RecordCompressionApplication(CommandBase):
    kind: Literal["record_compression_application"] = "record_compression_application"
    application: CompressionApplication
    path_residues: tuple[PathResidue, ...] = ()


class GrantRecoveryLicense(CommandBase):
    kind: Literal["grant_recovery_license"] = "grant_recovery_license"
    license: RecoveryLicense


class LinkRetentionCapability(CommandBase):
    kind: Literal["link_retention_capability"] = "link_retention_capability"
    link: RetentionCapabilityLink


class DecideRepresentationSuccessor(CommandBase):
    kind: Literal["decide_representation_successor"] = "decide_representation_successor"
    decision: RepresentationSuccessorDecision


class ReopenRepresentation(CommandBase):
    kind: Literal["reopen_representation"] = "reopen_representation"
    reopening: RepresentationReopening


class RecordProjectAnchor(CommandBase):
    kind: Literal["record_project_anchor"] = "record_project_anchor"
    anchor: ProjectAnchor


class RecordCapabilityLimitation(CommandBase):
    kind: Literal["record_capability_limitation"] = "record_capability_limitation"
    limitation: CapabilityLimitation


class RecordQuestionContractCandidate(CommandBase):
    kind: Literal["record_question_contract_candidate"] = "record_question_contract_candidate"
    candidate: QuestionContractCandidate


class DecideQuestionRepertoire(CommandBase):
    kind: Literal["decide_question_repertoire"] = "decide_question_repertoire"
    decision: QuestionRepertoireDecision


class RecordMethodBindingCandidate(CommandBase):
    kind: Literal["record_method_binding_candidate"] = "record_method_binding_candidate"
    candidate: MethodBindingCandidate


class DecideMethodAdmission(CommandBase):
    kind: Literal["decide_method_admission"] = "decide_method_admission"
    decision: MethodAdmissionDecision


class RecordCapabilitySuccessorCandidate(CommandBase):
    kind: Literal["record_capability_successor_candidate"] = "record_capability_successor_candidate"
    candidate: CapabilitySuccessorCandidate


class RecordCapabilityFrontier(CommandBase):
    kind: Literal["record_capability_frontier"] = "record_capability_frontier"
    frontier: CapabilityFrontier


class RecordImplementationGoalCandidate(CommandBase):
    kind: Literal["record_implementation_goal_candidate"] = "record_implementation_goal_candidate"
    candidate: ImplementationGoalCandidate


class DecideGoalAdmission(CommandBase):
    kind: Literal["decide_goal_admission"] = "decide_goal_admission"
    decision: GoalAdmissionDecision


class SealImplementationGoal(CommandBase):
    kind: Literal["seal_implementation_goal"] = "seal_implementation_goal"
    goal: ImplementationGoalContract


class RecordCandidateEnvironment(CommandBase):
    kind: Literal["record_candidate_environment"] = "record_candidate_environment"
    manifest: CandidateEnvironmentManifest


class RecordDevelopmentEvidence(CommandBase):
    kind: Literal["record_development_evidence"] = "record_development_evidence"
    evidence: DevelopmentEvidence


class RecordIndependentReview(CommandBase):
    kind: Literal["record_independent_review"] = "record_independent_review"
    review: IndependentReview


class DecideProjectSuccessor(CommandBase):
    kind: Literal["decide_project_successor"] = "decide_project_successor"
    decision: ProjectSuccessorDecision


class RecordPromotionDecision(CommandBase):
    kind: Literal["record_promotion_decision"] = "record_promotion_decision"
    decision: PromotionDecision


class RecordRecursiveCycleCheckpoint(CommandBase):
    kind: Literal["record_recursive_cycle_checkpoint"] = "record_recursive_cycle_checkpoint"
    checkpoint: RecursiveCycleCheckpoint


class RecordRecursiveStopDisposition(CommandBase):
    kind: Literal["record_recursive_stop_disposition"] = "record_recursive_stop_disposition"
    disposition: RecursiveStopDisposition


DomainCommand = Annotated[
    StartInquiry
    | RecordBacklogEffect
    | RecordStepPlan
    | RequestEffect
    | PlanEffectAttempt
    | StartEffectAttempt
    | RecordNoAttemptDisposition
    | RecordAttemptOutcome
    | RecordDecodeOutcome
    | AcceptEffectResult
    | AdmitClaim
    | OpenObligation
    | RecordObligationDisposition
    | RecordCandidate
    | RecordResidual
    | AppendCorrection
    | ChangeGuardStanding
    | RecordNogood
    | ChangeSupportRouteStanding
    | ChangeNogoodStanding
    | RecordEvidence
    | RecordCheckerVerdict
    | EvaluateWarrant
    | PromoteClaim
    | AdmitProbe
    | RecordCognitivePlan
    | SealPrediction
    | RecordProbeObservation
    | RecordReconstruction
    | RecordMismatch
    | CommitSemanticDelta
    | RegisterRetentionPackage
    | RunRetrieval
    | RequestReacquisition
    | LinkReacquisitionInquiry
    | RecordRecoveryObservation
    | RecordRecoveryComparison
    | RecordConsolidationCheckpoint
    | RecordConsolidationCandidate
    | RecordMemoryPatchCandidate
    | RecordReconsolidationLink
    | RecordSemanticFieldEvaluation
    | RecordRepresentationGap
    | RecordLearnedProbeCandidate
    | RecordProbeEvaluation
    | RecordProbeAdmissionDecision
    | RegisterBindingCarrierManifest
    | RecordRealizedHistoryDerivation
    | RegisterCompressionContract
    | RecordCompressionValidation
    | GrantExactCompressionLicense
    | RecordCompressionApplication
    | GrantRecoveryLicense
    | LinkRetentionCapability
    | DecideRepresentationSuccessor
    | ReopenRepresentation
    | RecordProjectAnchor
    | RecordCapabilityLimitation
    | RecordQuestionContractCandidate
    | DecideQuestionRepertoire
    | RecordMethodBindingCandidate
    | DecideMethodAdmission
    | RecordCapabilitySuccessorCandidate
    | RecordCapabilityFrontier
    | RecordImplementationGoalCandidate
    | DecideGoalAdmission
    | SealImplementationGoal
    | RecordCandidateEnvironment
    | RecordDevelopmentEvidence
    | RecordIndependentReview
    | DecideProjectSuccessor
    | RecordPromotionDecision
    | RecordRecursiveCycleCheckpoint
    | RecordRecursiveStopDisposition,
    Field(discriminator="kind"),
]
