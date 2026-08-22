"""Pure command decision and event evolution functions."""

from __future__ import annotations

from rci.backlog.models import G1_APPLICABLE_EFFECT_KINDS, BacklogItem
from rci.backlog.reconcile import BacklogPolicy, apply_effects
from rci.claims.logic import (
    conflict_obligation,
    mandatory_attack_obligation,
    structural_conflict,
)
from rci.claims.models import (
    Claim,
    ClaimRole,
    ClaimStatus,
    Conflict,
    Obligation,
    ObligationStatus,
    Scope,
    content_fingerprint,
)
from rci.compression.models import (
    ExactClaimKind,
    HistoryDerivationStatus,
    ReopeningOutcome,
    SuccessorDisposition,
    ValidationOutcome,
    ValidationProperty,
)
from rci.core.commands import (
    AcceptEffectResult,
    AdmitClaim,
    AdmitProbe,
    AppendCorrection,
    ChangeGuardStanding,
    ChangeNogoodStanding,
    ChangeSupportRouteStanding,
    CommitSemanticDelta,
    DecideGoalAdmission,
    DecideMethodAdmission,
    DecideProjectSuccessor,
    DecideQuestionRepertoire,
    DecideRepresentationSuccessor,
    DomainCommand,
    EvaluateWarrant,
    GrantExactCompressionLicense,
    GrantRecoveryLicense,
    LinkReacquisitionInquiry,
    LinkRetentionCapability,
    OpenObligation,
    PlanEffectAttempt,
    PromoteClaim,
    RecordAttemptOutcome,
    RecordBacklogEffect,
    RecordCandidate,
    RecordCandidateEnvironment,
    RecordCapabilityFrontier,
    RecordCapabilityLimitation,
    RecordCapabilitySuccessorCandidate,
    RecordCheckerVerdict,
    RecordCognitivePlan,
    RecordCompressionApplication,
    RecordCompressionValidation,
    RecordConsolidationCandidate,
    RecordConsolidationCheckpoint,
    RecordDecodeOutcome,
    RecordDevelopmentEvidence,
    RecordEvidence,
    RecordImplementationGoalCandidate,
    RecordIndependentReview,
    RecordLearnedProbeCandidate,
    RecordMemoryPatchCandidate,
    RecordMethodBindingCandidate,
    RecordMismatch,
    RecordNoAttemptDisposition,
    RecordNogood,
    RecordObligationDisposition,
    RecordProbeAdmissionDecision,
    RecordProbeEvaluation,
    RecordProbeObservation,
    RecordProjectAnchor,
    RecordPromotionDecision,
    RecordQuestionContractCandidate,
    RecordRealizedHistoryDerivation,
    RecordReconsolidationLink,
    RecordReconstruction,
    RecordRecoveryComparison,
    RecordRecoveryObservation,
    RecordRecursiveCycleCheckpoint,
    RecordRecursiveStopDisposition,
    RecordRepresentationGap,
    RecordResidual,
    RecordSemanticFieldEvaluation,
    RecordStepPlan,
    RegisterBindingCarrierManifest,
    RegisterCompressionContract,
    RegisterRetentionPackage,
    ReopenRepresentation,
    RequestEffect,
    RequestReacquisition,
    RunRetrieval,
    SealImplementationGoal,
    SealPrediction,
    StartEffectAttempt,
    StartInquiry,
)
from rci.core.effects import AttemptState, Decoded, EffectRequestState, ReturnedOutcome
from rci.core.errors import (
    DomainError,
    EffectLifecycleError,
    IdentityConflictError,
    InvalidCommandError,
    InvalidTransitionError,
)
from rci.core.events import (
    BacklogEffectRecorded,
    BindingCarrierManifestRegistered,
    CandidateEnvironmentRecorded,
    CandidateRecorded,
    CapabilityFrontierRecorded,
    CapabilityLimitationRecorded,
    CapabilitySuccessorCandidateRecorded,
    CheckerVerdictRecorded,
    ClaimAdmitted,
    CognitivePlanRecorded,
    CompressionApplicationRecorded,
    CompressionContractRegistered,
    CompressionValidationRecorded,
    ConsolidationCandidateRecorded,
    ConsolidationCheckpointRecorded,
    CorrectionAppended,
    DevelopmentEvidenceRecorded,
    DomainEvent,
    EffectAttemptOutcomeRecorded,
    EffectAttemptPlanned,
    EffectAttemptStarted,
    EffectDecodeOutcomeRecorded,
    EffectNoAttemptDispositionRecorded,
    EffectRequested,
    EffectResultAccepted,
    EvidenceRecorded,
    ExactCompressionLicenseGranted,
    GoalAdmissionDecided,
    GuardStandingChanged,
    ImplementationGoalCandidateRecorded,
    ImplementationGoalSealed,
    IndependentReviewRecorded,
    InquiryStarted,
    LearnedProbeCandidateRecorded,
    LemmaPromoted,
    MemoryPatchCandidateRecorded,
    MethodAdmissionDecided,
    MethodBindingCandidateRecorded,
    MismatchRecorded,
    NogoodRecorded,
    NogoodStandingChanged,
    ObligationDispositionRecorded,
    ObligationOpened,
    PredictionSealed,
    ProbeAdmissionDecisionRecorded,
    ProbeAdmitted,
    ProbeEvaluationRecorded,
    ProbeObservationRecorded,
    ProjectAnchorRecorded,
    ProjectSuccessorDecided,
    PromotionDecisionRecorded,
    QuestionContractCandidateRecorded,
    QuestionRepertoireDecided,
    ReacquisitionInquiryLinked,
    ReacquisitionRequested,
    RealizedHistoryDerivationRecorded,
    ReconsolidationLinked,
    ReconstructionRecorded,
    RecoveryComparisonRecorded,
    RecoveryLicenseGranted,
    RecoveryObservationRecorded,
    RecursiveCycleCheckpointRecorded,
    RecursiveStopDispositionRecorded,
    RepresentationGapRecorded,
    RepresentationReopened,
    RepresentationSuccessorDecided,
    ResidualRecorded,
    RetentionCapabilityLinked,
    RetentionPackageRegistered,
    RetrievalCompleted,
    SemanticDeltaCommitted,
    SemanticFieldEvaluationRecorded,
    StepPlanRecorded,
    SupportRouteStandingChanged,
    WarrantDecisionRecorded,
)
from rci.core.planning import PlanStatus
from rci.core.serialization import canonical_json_bytes, sha256_digest
from rci.core.state import InquiryState
from rci.learning.models import (
    ConsolidationStatus,
    DependencyDispositionKind,
    ProbeAdmissionOutcome,
)
from rci.learning.policies import (
    build_probe_evaluation,
    evaluate_conservative_field,
    select_consolidation_checkpoint,
    semantic_field_overflow_residual,
)
from rci.memory.recovery import (
    RecoveryCompatibilityError,
    compare_recovery_frontiers,
    derive_recovery_frontier,
)
from rci.memory.references import resolve_owned_memory_ref
from rci.memory.retrieval import (
    RetrievalConflictError,
    resolve_structural_retrieval_policy,
    retrieve,
    structural_index_fingerprint,
)
from rci.probes.lifecycle import append_probe_event
from rci.probes.models import ProbeTrace, RelevanceStatus, SemanticChangeOperation
from rci.project.goal_synthesis import (
    GoalSynthesisUnknown,
    compile_implementation_goal_candidate,
    goal_admission_evidence_ids,
)
from rci.project.models import (
    AdmissionOutcome,
    EvidenceOutcome,
    ProjectDisposition,
    ReviewOutcome,
)
from rci.project.models import (
    PromotionOutcome as ProjectPromotionOutcome,
)
from rci.project.selection import derive_capability_frontier
from rci.warrant.checks import checker_verdict_index, evidence_index, resolve_check_reference
from rci.warrant.models import (
    PromotionLink,
    PropositionKind,
    SupportStanding,
    WarrantClass,
    WarrantDecisionRecord,
)
from rci.warrant.policy import (
    PromotionOutcome,
    decide_evidence_warrant,
    decide_promotion,
)


def _require_active(state: InquiryState, inquiry_id: str) -> None:
    if state.status != "active":
        raise InvalidCommandError("the inquiry has not been started")
    if state.inquiry_id != inquiry_id:
        raise InvalidCommandError("the command inquiry id does not match the aggregate")


def _require_request(state: InquiryState, request_id: str) -> EffectRequestState:
    request = state.request_by_id(request_id)
    if request is None:
        raise InvalidCommandError(f"unknown effect request: {request_id}")
    return request


def _derive_claim_consequences(
    state: InquiryState,
    claim: Claim,
) -> tuple[tuple[Conflict, ...], tuple[Obligation, ...]]:
    """Derive the exact atomic conflict/attack bundle for a newly admitted claim."""

    known_conflict_ids = {conflict.id for conflict in state.conflicts}
    conflicts: list[Conflict] = []
    for existing in state.claims:
        conflict = structural_conflict(existing, claim)
        if conflict is not None and conflict.id not in known_conflict_ids:
            known_conflict_ids.add(conflict.id)
            conflicts.append(conflict)
    conflicts.sort(key=lambda item: item.id)

    known_fingerprints = {obligation.fingerprint for obligation in state.obligations}
    obligations: list[Obligation] = []
    attack = mandatory_attack_obligation(claim)
    if attack is not None and _claim_attack_is_exactly_discharged(state, claim):
        attack = None
    candidates = ([attack] if attack is not None else []) + [
        conflict_obligation(conflict) for conflict in conflicts
    ]
    for obligation in candidates:
        if obligation.fingerprint not in known_fingerprints:
            known_fingerprints.add(obligation.fingerprint)
            obligations.append(obligation)
    obligations.sort(key=lambda item: item.id)
    return tuple(conflicts), tuple(obligations)


def _known_entity_ids(state: InquiryState) -> frozenset[str]:
    return frozenset(
        item.id
        for collection in (
            state.claims,
            state.conflicts,
            state.obligations,
            state.candidates,
            state.residuals,
            state.lemma_versions,
            state.reconstructions,
        )
        for item in collection
    )


def _scope_matches_context(state: InquiryState, scope: Scope) -> bool:
    context = state.context
    if context is None:
        return False
    return (
        scope.id == context.scope_id
        and scope.fingerprint == context.scope_fingerprint
        and scope.binding_revision == context.binding_revision
        and scope.assumption_ids == context.assumption_ids
        and scope.applicability_guard_id == context.guard_condition_id
        and scope.finite_universe_hash == context.finite_universe_hash
        and scope.closed_world == context.closed_world
    )


def _current_active_lemma_ids(state: InquiryState) -> frozenset[str]:
    return frozenset(view.lemma_version_id for view in state.active_theory)


def _claim_attack_is_exactly_discharged(state: InquiryState, claim: Claim) -> bool:
    """Only an active hard lemma for the identical proposition and scope closes attack."""

    if claim.proposition_id is None:
        return False
    active_ids = _current_active_lemma_ids(state)
    return any(
        version.id in active_ids
        and version.relation_id == claim.proposition_id
        and version.scope.fingerprint == claim.scope.fingerprint
        for version in state.lemma_versions
    )


def _require_g2a_check(
    state: InquiryState,
    reference: object,
    *,
    proposition_id: str,
    scope_fingerprint: str,
) -> None:
    """Require one exact aggregate-owned, authorized, valid relation check."""

    if state.context is None:
        raise InvalidCommandError("G2A checks require an inquiry context")
    checked, reason = resolve_check_reference(
        reference,  # type: ignore[arg-type]
        evidence_by_id=evidence_index(state.evidence_records),
        checker_verdict_by_id=checker_verdict_index(state.checker_verdicts),
        proposition_id=proposition_id,
        proposition_kind=PropositionKind.RELATION,
        scope_fingerprint=scope_fingerprint,
        authorized_checker_ids=state.context.discharge_mechanism_ids,
    )
    if not checked:
        raise InvalidCommandError(f"G2A record requires an independent valid check: {reason}")


def _require_project_admission_evidence(
    state: InquiryState,
    *,
    evidence_ids: tuple[str, ...],
    limitation_id: str,
    require_valid_review: bool,
) -> None:
    evidence_by_id = {item.id: item for item in state.development_evidence}
    goal_by_id = {item.id: item for item in state.implementation_goals}
    candidate_by_id = {item.id: item for item in state.capability_successor_candidates}
    try:
        evidence = tuple(evidence_by_id[item] for item in evidence_ids)
    except KeyError as error:
        raise InvalidCommandError(
            "repertoire decision requires owned development evidence"
        ) from error
    if any(
        (goal := goal_by_id.get(item.goal_id)) is None
        or (candidate := candidate_by_id.get(goal.candidate_id)) is None
        or candidate.limitation_id != limitation_id
        for item in evidence
    ):
        raise InvalidCommandError("repertoire evidence must address the exact limitation")
    if require_valid_review:
        if any(item.outcome is not EvidenceOutcome.PASS for item in evidence):
            raise InvalidCommandError("repertoire admission requires passing evidence")
        if not any(
            review.outcome is ReviewOutcome.VALID
            and tuple(review.evidence_ids) == tuple(evidence_ids)
            for review in state.independent_reviews
        ):
            raise InvalidCommandError("repertoire admission requires exact independent review")


def decide(state: InquiryState, command: DomainCommand) -> tuple[DomainEvent, ...]:
    """Return events for a command without performing I/O or generating data."""

    if isinstance(command, StartInquiry):
        if state.status == "not_started":
            return (
                InquiryStarted(
                    event_id=command.event_id,
                    inquiry_id=command.inquiry_id,
                    occurred_at=command.occurred_at,
                    manifest_artifact=command.manifest_artifact,
                    policy_version=command.policy_version,
                    context=command.context,
                ),
            )
        if (
            state.inquiry_id == command.inquiry_id
            and state.manifest_artifact == command.manifest_artifact
            and state.policy_version == command.policy_version
            and state.context == command.context
        ):
            return ()
        raise IdentityConflictError("the inquiry identity is already bound to different data")

    _require_active(state, command.inquiry_id)

    if isinstance(command, RecordBacklogEffect):
        if command.effect.kind not in G1_APPLICABLE_EFFECT_KINDS:
            raise InvalidCommandError(
                f"backlog effect {command.effect.kind.value} is proposal-only in G1"
            )
        existing_effect = state.backlog_effect_by_id(command.effect.id)
        if existing_effect is not None:
            if existing_effect == command.effect:
                return ()
            raise IdentityConflictError("backlog effect id was reused for different content")
        try:
            projected_items: tuple[BacklogItem, ...] = ()
            constitutional_policy = BacklogPolicy()
            for historical_effect in state.backlog_effects:
                projected_items = apply_effects(
                    projected_items,
                    (historical_effect,),
                    policy=constitutional_policy,
                )
            apply_effects(
                projected_items,
                (command.effect,),
                policy=constitutional_policy,
            )
        except (PermissionError, ValueError) as error:
            raise InvalidCommandError(f"invalid backlog effect sequence: {error}") from error
        return (
            BacklogEffectRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                effect=command.effect,
            ),
        )

    if isinstance(command, RecordStepPlan):
        existing_plan = state.step_plan_by_id(command.plan.id)
        if existing_plan is not None:
            if existing_plan == command.plan:
                return ()
            raise IdentityConflictError("step plan id was reused")
        if (
            state.context is None
            or command.plan.policy_version != state.context.scheduler_policy_version
        ):
            raise InvalidCommandError("step plan policy does not match the inquiry context")
        if command.plan.status is PlanStatus.READY:
            obligation = state.obligation_by_id(command.plan.selected_obligation_id or "")
            if obligation is None or command.plan.selected_attempt_key is None:
                raise InvalidCommandError("ready step plan must select an owned obligation")
            if state.current_obligation_status(obligation.id) is not ObligationStatus.OPEN:
                raise InvalidCommandError("ready step plan must select an open obligation")
            if (
                command.plan.selected_attempt_key.obligation_fingerprint != obligation.fingerprint
                or command.plan.selected_attempt_key.binding_revision != obligation.binding_revision
            ):
                raise InvalidCommandError(
                    "step plan attempt key does not match the exact obligation"
                )
        return (
            StepPlanRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                plan=command.plan,
            ),
        )

    if isinstance(command, RequestEffect):
        existing = state.request_by_id(command.request.id)
        if existing is not None:
            if existing.request == command.request:
                return ()
            raise IdentityConflictError("effect request id was reused for different content")
        step_plan = state.step_plan_by_id(command.request.step_plan_id)
        if step_plan is None:
            raise EffectLifecycleError("an effect request requires a persisted step plan")
        if step_plan.status is not PlanStatus.READY:
            raise EffectLifecycleError("an effect request requires a ready step plan")
        selected_obligation = state.obligation_by_id(step_plan.selected_obligation_id or "")
        if (
            selected_obligation is None
            or step_plan.selected_attempt_key is None
            or step_plan.selected_attempt_key.obligation_fingerprint
            != selected_obligation.fingerprint
            or step_plan.selected_attempt_key.binding_revision
            != selected_obligation.binding_revision
        ):
            raise EffectLifecycleError(
                "effect request step plan does not own an exact obligation and attempt key"
            )
        return (
            EffectRequested(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                request=command.request,
            ),
        )

    if isinstance(command, PlanEffectAttempt):
        request = _require_request(state, command.plan.request_id)
        existing_attempt = next(
            (
                attempt
                for item in state.effect_requests
                for attempt in item.attempts
                if attempt.plan.id == command.plan.id
            ),
            None,
        )
        if existing_attempt is not None:
            if existing_attempt.plan == command.plan:
                return ()
            raise IdentityConflictError("attempt id was reused for a different plan")
        if request.accepted_decoded_outcome_id is not None:
            raise EffectLifecycleError("a resolved request cannot plan another attempt")
        return (
            EffectAttemptPlanned(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                plan=command.plan,
            ),
        )

    if isinstance(command, StartEffectAttempt):
        containing_request = next(
            (
                request
                for request in state.effect_requests
                if any(attempt.plan.id == command.attempt_id for attempt in request.attempts)
            ),
            None,
        )
        if containing_request is None:
            raise EffectLifecycleError("an attempt start requires a persisted attempt plan")
        start_attempt = next(
            item for item in containing_request.attempts if item.plan.id == command.attempt_id
        )
        if start_attempt.started:
            return ()
        if containing_request.accepted_decoded_outcome_id is not None:
            raise EffectLifecycleError("a resolved request cannot start another attempt")
        if start_attempt.outcome is not None:
            raise EffectLifecycleError("an attempt cannot start after a terminal outcome")
        return (
            EffectAttemptStarted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                attempt_id=command.attempt_id,
            ),
        )

    if isinstance(command, RecordNoAttemptDisposition):
        request = _require_request(state, command.disposition.request_id)
        if command.disposition.step_plan_id != request.request.step_plan_id:
            raise EffectLifecycleError(
                "a no-attempt disposition must reference its request's persisted step plan"
            )
        existing_disposition = next(
            (
                disposition
                for item in state.effect_requests
                for disposition in item.no_attempt_dispositions
                if disposition.id == command.disposition.id
            ),
            None,
        )
        if existing_disposition is not None:
            if existing_disposition == command.disposition:
                return ()
            raise IdentityConflictError("no-attempt disposition id was reused")
        if request.accepted_decoded_outcome_id is not None:
            raise EffectLifecycleError(
                "a resolved request cannot record a new no-attempt disposition"
            )
        return (
            EffectNoAttemptDispositionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                disposition=command.disposition,
            ),
        )

    if isinstance(command, RecordAttemptOutcome):
        request = _require_request(state, command.request_id)
        outcome_attempt = next(
            (item for item in request.attempts if item.plan.id == command.outcome.attempt_id),
            None,
        )
        if outcome_attempt is None:
            raise EffectLifecycleError("an outcome requires a persisted attempt plan")
        if not outcome_attempt.started:
            raise EffectLifecycleError("an attempt must start before a terminal outcome")
        if outcome_attempt.plan.route.id != command.outcome.route_id:
            raise EffectLifecycleError("outcome route does not match the attempt plan")
        if outcome_attempt.outcome is not None:
            if outcome_attempt.outcome == command.outcome:
                return ()
            raise EffectLifecycleError("an attempt can have only one terminal outcome")
        if isinstance(command.outcome, ReturnedOutcome):
            duplicate_return = next(
                (
                    other.outcome.external_return
                    for item in state.effect_requests
                    for other in item.attempts
                    if isinstance(other.outcome, ReturnedOutcome)
                    and other.outcome.external_return.id == command.outcome.external_return.id
                ),
                None,
            )
            if duplicate_return is not None:
                raise IdentityConflictError("external return id was already captured")
        return (
            EffectAttemptOutcomeRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                request_id=command.request_id,
                outcome=command.outcome,
            ),
        )

    if isinstance(command, RecordDecodeOutcome):
        request = _require_request(state, command.request_id)
        existing_decode = next(
            (
                outcome
                for item in state.effect_requests
                for outcome in item.decode_outcomes
                if outcome.id == command.outcome.id
            ),
            None,
        )
        if existing_decode is not None:
            if existing_decode == command.outcome:
                return ()
            raise IdentityConflictError("decode outcome id was reused")
        captured_return_ids = {
            attempt.outcome.external_return.id
            for attempt in request.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        }
        if command.outcome.external_return_id not in captured_return_ids:
            raise EffectLifecycleError("a decode outcome requires this request's captured return")
        return (
            EffectDecodeOutcomeRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                request_id=command.request_id,
                outcome=command.outcome,
            ),
        )

    if isinstance(command, AcceptEffectResult):
        request = _require_request(state, command.request_id)
        if request.accepted_decoded_outcome_id is not None:
            if request.accepted_decoded_outcome_id == command.decoded_outcome_id:
                return ()
            raise EffectLifecycleError("an effect request can accept at most one result")
        decoded = next(
            (
                outcome
                for outcome in request.decode_outcomes
                if outcome.id == command.decoded_outcome_id
            ),
            None,
        )
        if not isinstance(decoded, Decoded):
            raise EffectLifecycleError("only a recorded successful Decoded outcome can be accepted")
        return (
            EffectResultAccepted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                request_id=command.request_id,
                decoded_outcome_id=command.decoded_outcome_id,
            ),
        )

    if isinstance(command, AdmitClaim):
        existing_claim = state.claim_by_id(command.claim.id)
        if existing_claim is not None:
            if existing_claim == command.claim:
                return ()
            raise IdentityConflictError("claim id was reused for different content")
        if command.claim.status is not ClaimStatus.PROVISIONAL:
            raise InvalidCommandError("new question-derived claims must begin provisional")
        if not _scope_matches_context(state, command.claim.scope):
            raise InvalidCommandError("claim scope does not match the inquiry context")
        conflicts, obligations = _derive_claim_consequences(state, command.claim)
        return (
            ClaimAdmitted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                claim=command.claim,
                derived_conflicts=conflicts,
                derived_obligations=obligations,
            ),
        )

    if isinstance(command, OpenObligation):
        existing_obligation = state.obligation_by_id(command.obligation.id)
        if existing_obligation is not None:
            if existing_obligation == command.obligation:
                return ()
            raise IdentityConflictError("obligation id was reused for different content")
        if any(item.fingerprint == command.obligation.fingerprint for item in state.obligations):
            return ()
        if command.obligation.status is not ObligationStatus.OPEN:
            raise InvalidCommandError("new obligations must begin open")
        if not _scope_matches_context(state, command.obligation.scope):
            raise InvalidCommandError("obligation scope does not match the inquiry context")
        if not set(command.obligation.parent_obligation_ids) <= {
            item.id for item in state.obligations
        }:
            raise InvalidCommandError("obligation parent references must already exist")
        return (
            ObligationOpened(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                obligation=command.obligation,
            ),
        )

    if isinstance(command, RecordObligationDisposition):
        obligation = state.obligation_by_id(command.disposition.obligation_id)
        if obligation is None:
            raise InvalidCommandError("obligation disposition references an unknown obligation")
        existing_obligation_disposition = next(
            (item for item in state.obligation_dispositions if item.id == command.disposition.id),
            None,
        )
        if existing_obligation_disposition is not None:
            if existing_obligation_disposition == command.disposition:
                return ()
            raise IdentityConflictError("obligation disposition id was reused")
        disposition_history = tuple(
            item for item in state.obligation_dispositions if item.obligation_id == obligation.id
        )
        expected_predecessor = disposition_history[-1].id if disposition_history else None
        if command.disposition.predecessor_id != expected_predecessor:
            raise InvalidCommandError("obligation disposition must extend the current history tail")
        current_status = (
            disposition_history[-1].status if disposition_history else obligation.status
        )
        if command.disposition.status is current_status:
            raise InvalidCommandError("obligation disposition must change standing")
        if command.disposition.status is ObligationStatus.IMPOSSIBLE:
            raise InvalidCommandError(
                "generic dispositions cannot establish impossibility; use a typed checked discharge"
            )
        if command.disposition.status is ObligationStatus.SATISFIED:
            hard_decision_ids = {
                item.id
                for item in state.warrant_decisions
                if item.warrant_class is WarrantClass.HARD
                and item.proposition_id == obligation.carrier_id
                and item.scope_fingerprint == obligation.scope.fingerprint
            }
            accepted_decode_ids = {
                request.accepted_decoded_outcome_id
                for request in state.effect_requests
                if request.accepted_decoded_outcome_id is not None
                and (plan := state.step_plan_by_id(request.request.step_plan_id)) is not None
                and plan.status is PlanStatus.READY
                and plan.selected_obligation_id == obligation.id
                and plan.selected_attempt_key is not None
                and plan.selected_attempt_key.obligation_fingerprint == obligation.fingerprint
                and plan.selected_attempt_key.binding_revision == obligation.binding_revision
            }
            lawful_evidence_refs = hard_decision_ids | accepted_decode_ids
            if (
                not command.disposition.evidence_refs
                or not set(command.disposition.evidence_refs) <= lawful_evidence_refs
            ):
                raise InvalidCommandError(
                    "satisfied obligations require owned evidence tied to the exact obligation "
                    "and scope"
                )
        lawful = {
            ObligationStatus.OPEN: {
                ObligationStatus.BLOCKED,
                ObligationStatus.SATISFIED,
                ObligationStatus.IMPOSSIBLE,
                ObligationStatus.UNKNOWN,
            },
            ObligationStatus.BLOCKED: {
                ObligationStatus.OPEN,
                ObligationStatus.SATISFIED,
                ObligationStatus.UNKNOWN,
            },
            ObligationStatus.UNKNOWN: {ObligationStatus.OPEN},
            ObligationStatus.SATISFIED: {ObligationStatus.OPEN},
            ObligationStatus.IMPOSSIBLE: {ObligationStatus.OPEN},
        }
        if command.disposition.status not in lawful[current_status]:
            raise InvalidCommandError("illegal obligation status transition")
        return (
            ObligationDispositionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                disposition=command.disposition,
            ),
        )

    if isinstance(command, RecordCandidate):
        existing_candidate = next(
            (item for item in state.candidates if item.id == command.candidate.id),
            None,
        )
        if existing_candidate is not None:
            if existing_candidate == command.candidate:
                return ()
            raise IdentityConflictError("candidate id was reused")
        if not _scope_matches_context(state, command.candidate.scope):
            raise InvalidCommandError("candidate scope does not match the inquiry context")
        return (
            CandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=command.candidate,
            ),
        )

    if isinstance(command, RecordResidual):
        existing_residual = next(
            (item for item in state.residuals if item.id == command.residual.id),
            None,
        )
        if existing_residual is not None:
            if existing_residual == command.residual:
                return ()
            raise IdentityConflictError("residual id was reused")
        if not _scope_matches_context(state, command.residual.scope):
            raise InvalidCommandError("residual scope does not match the inquiry context")
        if not set(command.residual.source_obligation_ids) <= {
            item.id for item in state.obligations
        }:
            raise InvalidCommandError("residual references an unknown obligation")
        return (
            ResidualRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                residual=command.residual,
            ),
        )

    if isinstance(command, AppendCorrection):
        existing_correction = next(
            (item for item in state.corrections if item.id == command.correction.id),
            None,
        )
        if existing_correction is not None:
            if existing_correction == command.correction:
                return ()
            raise IdentityConflictError("correction id was reused")
        if not _scope_matches_context(state, command.correction.scope):
            raise InvalidCommandError("correction scope does not match the inquiry context")
        known_ids = _known_entity_ids(state)
        if command.correction.target_id not in known_ids:
            raise InvalidCommandError("correction target is not recorded")
        if not set(command.correction.related_ids) <= known_ids:
            raise InvalidCommandError("correction relation references an unknown record")
        return (
            CorrectionAppended(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                correction=command.correction,
            ),
        )

    if isinstance(command, ChangeGuardStanding):
        existing_guard_change = next(
            (item for item in state.guard_changes if item.id == command.change.id),
            None,
        )
        if existing_guard_change is not None:
            if existing_guard_change == command.change:
                return ()
            raise IdentityConflictError("guard-change id was reused")
        if (
            state.context is None
            or command.change.scope_fingerprint != state.context.scope_fingerprint
        ):
            raise InvalidCommandError("guard change scope does not match the inquiry context")
        latest = state.latest_guard_change(command.change.condition_id)
        expected_predecessor = latest.id if latest is not None else None
        if command.change.predecessor_id != expected_predecessor:
            raise InvalidCommandError("guard change must extend the current history tail")
        if latest is not None and latest.standing is command.change.standing:
            raise InvalidCommandError("guard change must change standing")
        return (
            GuardStandingChanged(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                change=command.change,
            ),
        )

    if isinstance(command, RecordNogood):
        nogood = command.nogood
        existing_nogood = state.nogood_by_id(nogood.id)
        if existing_nogood is not None:
            if existing_nogood == nogood:
                return ()
            raise IdentityConflictError("nogood id was reused")
        if state.context is None or (
            nogood.scope_fingerprint != state.context.scope_fingerprint
            or nogood.binding_revision != state.context.binding_revision
            or nogood.finite_universe_hash != state.context.finite_universe_hash
            or nogood.policy_version != state.context.warrant_policy_version
        ):
            raise InvalidCommandError("nogood does not match the current support class")
        decision = state.warrant_decision_by_id(nogood.warrant_decision_id)
        if decision is None or (
            decision.warrant_class is not WarrantClass.HARD
            or decision.proposition_id != nogood.id
            or decision.proposition_kind is not PropositionKind.EXISTENTIAL
            or decision.scope_fingerprint != nogood.scope_fingerprint
            or decision.policy_version != nogood.policy_version
            or decision.evidence_id != nogood.check.evidence_id
            or decision.checker_verdict_id != nogood.check.checker_verdict_id
        ):
            raise InvalidCommandError("nogood requires an exact recorded hard warrant decision")
        checked, reason = resolve_check_reference(
            nogood.check,
            evidence_by_id=evidence_index(state.evidence_records),
            checker_verdict_by_id=checker_verdict_index(state.checker_verdicts),
            proposition_id=nogood.id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope_fingerprint=nogood.scope_fingerprint,
            authorized_checker_ids=state.context.discharge_mechanism_ids,
        )
        if not checked:
            raise InvalidCommandError(f"nogood check is not independently valid: {reason}")
        return (
            NogoodRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                nogood=nogood,
            ),
        )

    if isinstance(command, ChangeSupportRouteStanding):
        route_standing_change = command.change
        existing_route_change = next(
            (
                item
                for item in state.support_route_standing_changes
                if item.id == route_standing_change.id
            ),
            None,
        )
        if existing_route_change is not None:
            if existing_route_change == route_standing_change:
                return ()
            raise IdentityConflictError("support-route standing-change id was reused")
        if state.support_route_by_id(route_standing_change.support_route_id) is None:
            raise InvalidCommandError("support-route standing change references an unknown route")
        latest_route_change = state.latest_support_route_standing_change(
            route_standing_change.support_route_id
        )
        if route_standing_change.predecessor_id != (
            latest_route_change.id if latest_route_change is not None else None
        ):
            raise InvalidCommandError("support-route standing change must extend its exact tail")
        current_route_standing = (
            latest_route_change.standing
            if latest_route_change is not None
            else SupportStanding.STANDING
        )
        if route_standing_change.standing is current_route_standing:
            raise InvalidCommandError("support-route standing change must change standing")
        return (
            SupportRouteStandingChanged(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                change=route_standing_change,
            ),
        )

    if isinstance(command, ChangeNogoodStanding):
        nogood_standing_change = command.change
        existing_nogood_change = next(
            (
                item
                for item in state.nogood_standing_changes
                if item.id == nogood_standing_change.id
            ),
            None,
        )
        if existing_nogood_change is not None:
            if existing_nogood_change == nogood_standing_change:
                return ()
            raise IdentityConflictError("nogood standing-change id was reused")
        if state.nogood_by_id(nogood_standing_change.nogood_id) is None:
            raise InvalidCommandError("nogood standing change references an unknown nogood")
        latest_nogood_change = state.latest_nogood_standing_change(nogood_standing_change.nogood_id)
        if nogood_standing_change.predecessor_id != (
            latest_nogood_change.id if latest_nogood_change is not None else None
        ):
            raise InvalidCommandError("nogood standing change must extend its exact tail")
        current_nogood_standing = (
            latest_nogood_change.standing
            if latest_nogood_change is not None
            else SupportStanding.STANDING
        )
        if nogood_standing_change.standing is current_nogood_standing:
            raise InvalidCommandError("nogood standing change must change standing")
        return (
            NogoodStandingChanged(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                change=nogood_standing_change,
            ),
        )

    if isinstance(command, RecordEvidence):
        if (
            state.context is None
            or command.evidence.scope_fingerprint != state.context.scope_fingerprint
        ):
            raise InvalidCommandError("evidence scope does not match the inquiry context")
        existing_evidence = state.evidence_by_id(command.evidence.id)
        if existing_evidence is not None:
            if existing_evidence == command.evidence:
                return ()
            raise IdentityConflictError("evidence id was reused")
        return (
            EvidenceRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                evidence=command.evidence,
            ),
        )

    if isinstance(command, RecordCheckerVerdict):
        verdict = command.checker_verdict
        evidence = state.evidence_by_id(verdict.evidence_id)
        if evidence is None:
            raise InvalidCommandError("checker verdict requires recorded evidence")
        if (
            verdict.evidence_artifact != evidence.artifact
            or verdict.proposition_id != evidence.proposition_id
            or verdict.proposition_kind is not evidence.proposition_kind
            or verdict.scope_fingerprint != evidence.scope_fingerprint
        ):
            raise InvalidCommandError("checker verdict does not match the exact evidence record")
        existing_verdict = state.checker_verdict_by_id(verdict.id)
        if existing_verdict is not None:
            if existing_verdict == verdict:
                return ()
            raise IdentityConflictError("checker verdict id was reused")
        return (
            CheckerVerdictRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                checker_verdict=verdict,
            ),
        )

    if isinstance(command, EvaluateWarrant):
        if not _scope_matches_context(state, command.scope):
            raise InvalidCommandError("warrant scope does not match the inquiry context")
        evidence = state.evidence_by_id(command.evidence_id)
        checker_verdict = state.checker_verdict_by_id(command.checker_verdict_id)
        if evidence is None or checker_verdict is None:
            raise InvalidCommandError("warrant evaluation requires recorded evidence and check")
        if checker_verdict.evidence_id != evidence.id:
            raise InvalidCommandError("warrant evidence and checker verdict do not align")
        if state.context is None:
            raise InvalidCommandError("an active inquiry requires warrant policy context")
        warrant_class, reason = decide_evidence_warrant(
            evidence,
            checker_verdict,
            proposition_id=command.proposition_id,
            proposition_kind=command.proposition_kind,
            scope=command.scope,
            authorized_checker_ids=state.context.discharge_mechanism_ids,
        )
        decision = WarrantDecisionRecord(
            id=command.decision_id,
            evidence_id=evidence.id,
            checker_verdict_id=checker_verdict.id,
            proposition_id=command.proposition_id,
            proposition_kind=command.proposition_kind,
            scope_fingerprint=command.scope.fingerprint,
            warrant_class=warrant_class,
            reason=reason,
            policy_version=state.context.warrant_policy_version,
        )
        existing_warrant_decision = state.warrant_decision_by_id(command.decision_id)
        if existing_warrant_decision is not None:
            if existing_warrant_decision == decision:
                return ()
            raise IdentityConflictError("warrant decision id was reused")
        return (
            WarrantDecisionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                scope=command.scope,
                decision=decision,
            ),
        )

    if isinstance(command, PromoteClaim):
        source_claims = tuple(state.claim_by_id(item) for item in command.source_claim_ids)
        if not command.source_claim_ids or any(item is None for item in source_claims):
            raise InvalidCommandError("promotion must preserve recorded source claims")
        if any(
            item is not None and item.scope.fingerprint != command.scope.fingerprint
            for item in source_claims
        ):
            raise InvalidCommandError("promotion scope differs from its source claim")
        if any(
            item is not None
            and item.proposition_id is not None
            and item.proposition_id != command.relation_id
            for item in source_claims
        ):
            raise InvalidCommandError("promotion proposition differs from its source claim")
        if not _scope_matches_context(state, command.scope):
            raise InvalidCommandError("promotion scope does not match the inquiry context")
        assert state.context is not None
        if not set(command.predecessor_refs) <= {item.id for item in state.lemma_versions}:
            raise InvalidCommandError("promotion ancestry references an unknown lemma version")
        recorded_warrant_decision = state.warrant_decision_by_id(command.warrant_decision_id)
        if recorded_warrant_decision is None:
            raise InvalidCommandError("promotion requires a recorded warrant decision")
        if (
            recorded_warrant_decision.warrant_class is not WarrantClass.HARD
            or recorded_warrant_decision.proposition_id != command.relation_id
            or recorded_warrant_decision.proposition_kind is not command.proposition_kind
            or recorded_warrant_decision.scope_fingerprint != command.scope.fingerprint
        ):
            raise InvalidCommandError("promotion requires an exact hard warrant decision")
        evidence = state.evidence_by_id(recorded_warrant_decision.evidence_id)
        checker_verdict = state.checker_verdict_by_id(recorded_warrant_decision.checker_verdict_id)
        if evidence is None or checker_verdict is None:
            raise InvalidCommandError("promotion warrant evidence or check is unavailable")
        if any(
            recorded_warrant_decision.id not in route.warrant_refs
            for route in command.support_routes
        ):
            raise InvalidCommandError("every support route must bind the warrant decision")
        promotion = decide_promotion(
            lemma_id=command.lemma_id,
            relation_id=command.relation_id,
            proposition_kind=command.proposition_kind,
            scope=command.scope,
            applicability=command.applicability,
            support_routes=command.support_routes,
            evidence=evidence,
            checker_verdict=checker_verdict,
            evidence_records=state.evidence_records,
            checker_verdicts=state.checker_verdicts,
            authorized_checker_ids=state.context.discharge_mechanism_ids,
            policy_version=state.context.warrant_policy_version,
            provenance_refs=command.provenance_refs,
            source_claim_ids=command.source_claim_ids,
            predecessor_refs=command.predecessor_refs,
            existing_lemmas=state.warranted_lemmas,
            current_assumption_ids=state.context.assumption_ids,
            current_context_ids=tuple(sorted(state.standing_context_ids)),
        )
        if promotion.outcome is not PromotionOutcome.ACCEPTED or promotion.lemma is None:
            raise InvalidCommandError(promotion.reason)
        link = PromotionLink(
            id=command.promotion_id,
            lemma_version_id=promotion.lemma.id,
            source_claim_ids=command.source_claim_ids,
            warrant_decision_id=recorded_warrant_decision.id,
        )
        existing_version = next(
            (item for item in state.lemma_versions if item.id == promotion.lemma.id),
            None,
        )
        existing_link = next(
            (item for item in state.promotion_links if item.id == link.id),
            None,
        )
        if existing_version is not None or existing_link is not None:
            if (
                existing_version == promotion.lemma.version
                and existing_link == link
                and next(
                    (
                        item
                        for item in state.lemma_supports
                        if item.lemma_version_id == promotion.lemma.id
                    ),
                    None,
                )
                == promotion.lemma.support
            ):
                return ()
            raise IdentityConflictError("lemma or promotion identity was reused")
        return (
            LemmaPromoted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                version=promotion.lemma.version,
                support=promotion.lemma.support,
                link=link,
            ),
        )

    if isinstance(command, AdmitProbe):
        fingerprint = command.probe.fingerprint
        existing_probe = next(
            (item for item in state.admitted_probes if item.fingerprint == fingerprint),
            None,
        )
        if existing_probe is not None:
            if existing_probe == command.probe:
                return ()
            raise IdentityConflictError("probe fingerprint was reused")
        if command.probe.question_contract_key == "learned-recurrent-probe@1.0.0":
            raise InvalidCommandError(
                "learned probes require a recorded evaluation and controller admission decision"
            )
        if state.context is None or (
            command.probe.binding_revision != state.context.binding_revision
            or command.probe.binding_schema_id not in state.context.carrier_schema_ids
            or command.probe.scope_fingerprint != state.context.scope_fingerprint
        ):
            raise InvalidCommandError("probe binding does not match the inquiry context")
        return (
            ProbeAdmitted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                probe=command.probe,
            ),
        )

    if isinstance(command, RecordCognitivePlan):
        existing_cognitive_plan = state.cognitive_plan_by_id(command.plan.id)
        if existing_cognitive_plan is not None:
            if existing_cognitive_plan == command.plan:
                return ()
            raise IdentityConflictError("cognitive plan id was reused")
        obligation = state.obligation_by_id(command.plan.obligation_id)
        effect_request = state.request_by_id(command.plan.effect_request_id)
        if obligation is None or effect_request is None:
            raise InvalidCommandError("cognitive plan requires an obligation and effect request")
        scheduler_plan = state.step_plan_by_id(effect_request.request.step_plan_id)
        if (
            scheduler_plan is None
            or scheduler_plan.selected_obligation_id != command.plan.obligation_id
        ):
            raise InvalidCommandError(
                "effect request scheduler plan does not select this cognitive obligation"
            )
        if obligation.scope.fingerprint != command.plan.scope_fingerprint:
            raise InvalidCommandError("cognitive plan scope differs from its obligation")
        if command.plan.source_state_revision > state.sequence:
            raise InvalidCommandError("cognitive plan cannot reference a future state")
        if command.plan.planned_sequence != state.sequence + 1:
            raise InvalidCommandError("cognitive plan sequence must match its event position")
        if command.plan.effect_attempt_plan_id is not None:
            known_attempt = next(
                (
                    attempt.plan
                    for item in state.effect_requests
                    for attempt in item.attempts
                    if attempt.plan.id == command.plan.effect_attempt_plan_id
                ),
                None,
            )
            if known_attempt is not None and known_attempt.request_id != effect_request.request.id:
                raise InvalidCommandError("cognitive plan references another request's attempt")
        return (
            CognitivePlanRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                plan=command.plan,
            ),
        )

    if isinstance(command, SealPrediction):
        existing_prediction = next(
            (item for item in state.predictions if item.id == command.prediction.id),
            None,
        )
        if existing_prediction is not None:
            if existing_prediction == command.prediction:
                return ()
            raise IdentityConflictError("prediction id was reused")
        cognitive_plan = state.cognitive_plan_by_id(command.prediction.cognitive_plan_id)
        if cognitive_plan is None:
            raise InvalidCommandError("prediction requires a recorded cognitive plan")
        if (
            command.prediction.probe_or_action_id != cognitive_plan.probe_or_action_id
            or command.prediction.scope_fingerprint != cognitive_plan.scope_fingerprint
        ):
            raise InvalidCommandError("prediction does not match its cognitive plan")
        if not set(command.prediction.basis_claim_ids) <= {item.id for item in state.claims}:
            raise InvalidCommandError("prediction basis references an unknown claim")
        if command.prediction.sealed_sequence != state.sequence + 1:
            raise InvalidCommandError("prediction seal sequence must match its event position")
        if cognitive_plan.effect_attempt_plan_id is not None:
            linked_attempt = next(
                (
                    attempt
                    for request in state.effect_requests
                    for attempt in request.attempts
                    if attempt.plan.id == cognitive_plan.effect_attempt_plan_id
                ),
                None,
            )
            if linked_attempt is not None and linked_attempt.outcome is not None:
                raise InvalidCommandError("prediction must be sealed before an attempt returns")
        return (
            PredictionSealed(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                prediction=command.prediction,
            ),
        )

    if isinstance(command, RecordProbeObservation):
        existing_observation = next(
            (item for item in state.probe_observations if item.id == command.observation.id),
            None,
        )
        if existing_observation is not None:
            if existing_observation == command.observation:
                return ()
            raise IdentityConflictError("probe observation id was reused")
        fingerprint = command.observation.probe_identity.fingerprint
        if not any(item.fingerprint == fingerprint for item in state.admitted_probes):
            raise InvalidCommandError("probe observation requires an admitted probe identity")
        if state.context is None or (
            command.observation.binding_revision != state.context.binding_revision
            or command.observation.probe_identity.binding_revision != state.context.binding_revision
            or command.observation.probe_identity.scope_fingerprint
            != state.context.scope_fingerprint
        ):
            raise InvalidCommandError("probe observation binding does not match the inquiry")
        if command.observation.state_revision > state.sequence:
            raise InvalidCommandError("probe observation cannot reference a future state")
        if not set(command.observation.external_return_ids) <= state.captured_external_return_ids:
            raise InvalidCommandError("probe observation references an unknown raw return")
        claim_refs = set(command.observation.interpretation_claim_ids)
        if command.observation.generated_answer_claim_id is not None:
            claim_refs.add(command.observation.generated_answer_claim_id)
        if not claim_refs <= {item.id for item in state.claims}:
            raise InvalidCommandError("probe observation references an unknown claim")
        bridge = command.observation.comparability_bridge
        if bridge is not None:
            active_lemma_ids = _current_active_lemma_ids(state)
            bridge_lemma = next(
                (
                    item
                    for item in state.lemma_versions
                    if item.id == bridge.warrant_lemma_id and item.id in active_lemma_ids
                ),
                None,
            )
            if bridge_lemma is None:
                raise InvalidCommandError("probe comparison bridge requires an active hard lemma")
            if (
                bridge.comparison_proposition_id != bridge_lemma.relation_id
                or bridge.scope_fingerprint != bridge_lemma.scope.fingerprint
                or bridge.scope_fingerprint != state.context.scope_fingerprint
            ):
                raise InvalidCommandError(
                    "probe comparison bridge warrant does not match its proposition and scope"
                )
        observation_history = tuple(
            item
            for item in state.probe_observations
            if item.probe_identity.fingerprint == fingerprint
        )
        trace = ProbeTrace(
            probe_fingerprint=fingerprint,
            events=observation_history,
            protected_horizon_id=command.observation.probe_identity.protected_horizon_id,
            comparison_policy_id=command.observation.probe_identity.comparison_semantics_id,
            active_guard_id=command.observation.probe_identity.applicability_guard_id,
        )
        try:
            append_probe_event(trace, command.observation)
        except ValueError as exc:
            raise InvalidCommandError(str(exc)) from exc
        return (
            ProbeObservationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                observation=command.observation,
            ),
        )

    if isinstance(command, RecordReconstruction):
        existing_reconstruction = next(
            (item for item in state.reconstructions if item.id == command.reconstruction.id),
            None,
        )
        if existing_reconstruction is not None:
            if existing_reconstruction == command.reconstruction:
                return ()
            raise IdentityConflictError("reconstruction id was reused")
        if command.reconstruction.external_return_id not in state.captured_external_return_ids:
            raise InvalidCommandError("reconstruction requires an owned raw return")
        decode_by_id = {
            outcome.id: outcome
            for request in state.effect_requests
            for outcome in request.decode_outcomes
        }
        if not set(command.reconstruction.decode_outcome_ids) <= set(decode_by_id):
            raise InvalidCommandError("reconstruction references an unknown decode outcome")
        if any(
            decode_by_id[decode_id].external_return_id != command.reconstruction.external_return_id
            for decode_id in command.reconstruction.decode_outcome_ids
        ):
            raise InvalidCommandError("reconstruction decode does not belong to its raw return")
        if not set(command.reconstruction.candidate_claim_ids) <= {
            item.id for item in state.claims
        }:
            raise InvalidCommandError("reconstruction references an unknown candidate claim")
        if command.reconstruction.prior_state_revision > state.sequence:
            raise InvalidCommandError("reconstruction cannot reference a future state")
        if command.reconstruction.reconstructed_sequence != state.sequence + 1:
            raise InvalidCommandError("reconstruction sequence must match its event position")
        return (
            ReconstructionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                reconstruction=command.reconstruction,
            ),
        )

    if isinstance(command, RecordMismatch):
        existing_mismatch = next(
            (item for item in state.mismatches if item.id == command.mismatch.id),
            None,
        )
        if existing_mismatch is not None:
            if existing_mismatch == command.mismatch:
                return ()
            raise IdentityConflictError("mismatch id was reused")
        prediction = next(
            (item for item in state.predictions if item.id == command.mismatch.prediction_id),
            None,
        )
        if prediction is None:
            raise InvalidCommandError("mismatch requires a sealed prediction")
        if command.mismatch.scope_fingerprint != prediction.scope_fingerprint:
            raise InvalidCommandError("mismatch scope differs from its prediction")
        difference_claim = state.claim_by_id(command.mismatch.difference_claim_id)
        if difference_claim is None or (
            difference_claim.scope.fingerprint != command.mismatch.scope_fingerprint
        ):
            raise InvalidCommandError("mismatch difference claim is absent or out of scope")
        decoded = next(
            (
                outcome
                for request in state.effect_requests
                for outcome in request.decode_outcomes
                if outcome.id == command.mismatch.decode_outcome_id
            ),
            None,
        )
        if not isinstance(decoded, Decoded):
            raise InvalidCommandError("mismatch requires a successfully decoded observation")
        if decoded.external_return_id != command.mismatch.external_return_id:
            raise InvalidCommandError("mismatch decode and raw return do not match")
        cognitive_plan = state.cognitive_plan_by_id(prediction.cognitive_plan_id)
        if cognitive_plan is None or cognitive_plan.effect_attempt_plan_id is None:
            raise InvalidCommandError("mismatch prediction lacks an effect attempt")
        returned_from_plan = any(
            attempt.plan.id == cognitive_plan.effect_attempt_plan_id
            and isinstance(attempt.outcome, ReturnedOutcome)
            and attempt.outcome.external_return.id == command.mismatch.external_return_id
            for request in state.effect_requests
            for attempt in request.attempts
        )
        if not returned_from_plan:
            raise InvalidCommandError("mismatch return did not arise from the predicted attempt")
        return (
            MismatchRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                mismatch=command.mismatch,
            ),
        )

    if isinstance(command, CommitSemanticDelta):
        existing_delta = next(
            (item for item in state.semantic_deltas if item.id == command.delta.id),
            None,
        )
        if existing_delta is not None:
            if existing_delta == command.delta:
                return ()
            raise IdentityConflictError("semantic delta id was reused")
        reconstruction_record = next(
            (item for item in state.reconstructions if item.id == command.delta.reconstruction_id),
            None,
        )
        if reconstruction_record is None:
            raise InvalidCommandError("semantic delta requires an owned reconstruction")
        if command.delta.committed_sequence != state.sequence + 1:
            raise InvalidCommandError("semantic delta sequence must match its event position")
        if command.delta.committed_sequence <= reconstruction_record.reconstructed_sequence:
            raise InvalidCommandError("semantic delta must follow its reconstruction")
        if state.context is None:
            raise InvalidCommandError("semantic delta requires inquiry context")
        active_ids = _current_active_lemma_ids(state)
        versions = {version.id: version for version in state.lemma_versions}
        for change in command.delta.warranted_changes:
            version = versions.get(change.warrant_lemma_id)
            if version is None or change.warrant_lemma_id not in active_ids:
                raise InvalidCommandError("semantic delta requires an active hard warrant lemma")
            if (
                version.relation_id != change.proposition_id
                or version.scope.fingerprint != change.scope_fingerprint
                or change.scope_fingerprint != state.context.scope_fingerprint
            ):
                raise InvalidCommandError("semantic change exceeds its exact warrant proposition")
            expected_operation = (
                SemanticChangeOperation.REOPEN
                if change.change_id in command.delta.reopened_structure_ids
                else SemanticChangeOperation.RETIRE
                if change.change_id in command.delta.retired_structure_ids
                else SemanticChangeOperation.ADD
            )
            if change.operation is not expected_operation:
                raise InvalidCommandError("semantic change operation does not match the delta")
        return (
            SemanticDeltaCommitted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                delta=command.delta,
            ),
        )

    if isinstance(command, RegisterRetentionPackage):
        registration = command.registration
        package = next(
            (item for item in state.retention_packages if item.id == registration.package.id),
            None,
        )
        if package is not None:
            exact = (
                package == registration.package
                and all(item in state.direct_use_routes for item in registration.direct_use_routes)
                and all(
                    item in state.reconstruction_routes
                    for item in registration.reconstruction_routes
                )
                and all(
                    item in state.consequence_evaluation_routes
                    for item in registration.consequence_evaluation_routes
                )
                and all(
                    item in state.reacquisition_routes for item in registration.reacquisition_routes
                )
                and all(item in state.reacquisition_scaffolds for item in registration.scaffolds)
                and all(
                    item in state.recovery_protocols for item in registration.recovery_protocols
                )
            )
            if exact:
                return ()
            raise IdentityConflictError("retention package identity was reused")
        if state.context is None or (
            registration.package.scope_fingerprint,
            registration.package.binding_revision,
            registration.package.protected_horizon_id,
        ) != (
            state.context.scope_fingerprint,
            state.context.binding_revision,
            state.context.protected_horizon_id,
        ):
            raise InvalidCommandError("retention package pins must match the inquiry context")
        registration_reuses_owned_id = (
            any(
                prior.id == proposed.id
                for prior in state.direct_use_routes
                for proposed in registration.direct_use_routes
            )
            or any(
                prior.id == proposed.id
                for prior in state.reconstruction_routes
                for proposed in registration.reconstruction_routes
            )
            or any(
                prior.id == proposed.id
                for prior in state.consequence_evaluation_routes
                for proposed in registration.consequence_evaluation_routes
            )
            or any(
                prior.id == proposed.id
                for prior in state.reacquisition_routes
                for proposed in registration.reacquisition_routes
            )
            or any(
                prior.id == proposed.id
                for prior in state.reacquisition_scaffolds
                for proposed in registration.scaffolds
            )
            or any(
                prior.id == proposed.id
                for prior in state.recovery_protocols
                for proposed in registration.recovery_protocols
            )
        )
        if registration_reuses_owned_id:
            raise InvalidCommandError(
                "a new retention package cannot take ownership of an existing route"
            )
        for reference in registration.package.owned_refs:
            resolved, reason = resolve_owned_memory_ref(
                reference,
                owned_records=state.owned_memory_records,
            )
            if not resolved:
                raise InvalidCommandError(
                    f"retention package has an invalid pre-existing reference: {reason}"
                )
        return (
            RetentionPackageRegistered(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                registration=registration,
            ),
        )

    if isinstance(command, RunRetrieval):
        existing_result = next(
            (item for item in state.retrieval_results if item.id == command.result_id),
            None,
        )
        existing_query = next(
            (item for item in state.retrieval_queries if item.id == command.query.id),
            None,
        )
        if existing_result is not None or existing_query is not None:
            if (
                existing_result is not None
                and existing_query == command.query
                and existing_result.query_id == command.query.id
            ):
                return ()
            raise IdentityConflictError("retrieval query or result identity was reused")
        if command.query.source_sequence != state.sequence:
            raise InvalidCommandError("retrieval query must pin the current committed sequence")
        actual_index = structural_index_fingerprint(
            state.retention_packages,
            state.owned_memory_fingerprints,
        )
        if command.query.source_index_fingerprint != actual_index:
            raise InvalidCommandError("retrieval query must pin the current structural index")
        try:
            policy = resolve_structural_retrieval_policy(
                command.query.policy_id,
                command.query.policy_version,
            )
            result = retrieve(
                result_id=command.result_id,
                query=command.query,
                policy=policy,
                packages=state.retention_packages,
                owned_fingerprints=state.owned_memory_fingerprints,
            )
        except (KeyError, RetrievalConflictError, ValueError) as error:
            raise InvalidCommandError(str(error)) from error
        return (
            RetrievalCompleted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                policy=policy,
                query=command.query,
                result=result,
            ),
        )

    if isinstance(command, RequestReacquisition):
        reacquisition_request = command.request
        existing_reacquisition_request = next(
            (item for item in state.reacquisition_requests if item.id == reacquisition_request.id),
            None,
        )
        if existing_reacquisition_request is not None:
            if existing_reacquisition_request == reacquisition_request:
                return ()
            raise IdentityConflictError("reacquisition request identity was reused")
        if any(
            item.child_inquiry_id == reacquisition_request.child_inquiry_id
            for item in state.reacquisition_requests
        ):
            raise IdentityConflictError("reacquisition child inquiry identity was reused")
        if state.context is None or reacquisition_request.parent_inquiry_id != state.inquiry_id:
            raise InvalidCommandError("reacquisition request must belong to this inquiry")
        if (
            reacquisition_request.pins.scope_fingerprint,
            reacquisition_request.pins.binding_revision,
            reacquisition_request.pins.protected_horizon_id,
            reacquisition_request.pins.finite_universe_hash,
        ) != (
            state.context.scope_fingerprint,
            state.context.binding_revision,
            state.context.protected_horizon_id,
            state.context.finite_universe_hash,
        ):
            raise InvalidCommandError("reacquisition request pins differ from inquiry context")
        recovery_protocol = next(
            (
                item
                for item in state.recovery_protocols
                if item.id == reacquisition_request.pins.recovery_protocol_id
                and item.version == reacquisition_request.pins.recovery_protocol_version
            ),
            None,
        )
        if recovery_protocol is None or recovery_protocol.pins != reacquisition_request.pins:
            raise InvalidCommandError("reacquisition request requires an exact owned protocol")
        if reacquisition_request.retention_package_id is not None:
            retained_package = next(
                (
                    item
                    for item in state.retention_packages
                    if item.id == reacquisition_request.retention_package_id
                ),
                None,
            )
            if (
                retained_package is None
                or reacquisition_request.scaffold_id not in retained_package.scaffold_ids
                or recovery_protocol.id not in retained_package.recovery_protocol_ids
                or not any(
                    route.id in retained_package.reacquisition_route_ids
                    and route.recovery_protocol_id == recovery_protocol.id
                    and route.reacquisition_scaffold_id == reacquisition_request.scaffold_id
                    for route in state.reacquisition_routes
                )
            ):
                raise InvalidCommandError(
                    "retained reacquisition requires one package-owned scaffold and protocol"
                )
        return (
            ReacquisitionRequested(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                request=reacquisition_request,
            ),
        )

    if isinstance(command, LinkReacquisitionInquiry):
        reacquisition_link = command.link
        existing_reacquisition_link = next(
            (
                item
                for item in state.reacquisition_inquiry_links
                if item.id == reacquisition_link.id
            ),
            None,
        )
        if existing_reacquisition_link is not None:
            if existing_reacquisition_link == reacquisition_link:
                return ()
            raise IdentityConflictError("reacquisition link identity was reused")
        linked_request = next(
            (
                item
                for item in state.reacquisition_requests
                if item.id == reacquisition_link.request_id
            ),
            None,
        )
        if linked_request is None:
            raise InvalidCommandError("reacquisition link requires an owned request")
        if any(
            item.request_id == reacquisition_link.request_id
            for item in state.reacquisition_inquiry_links
        ):
            raise IdentityConflictError("reacquisition request is already linked")
        if (
            reacquisition_link.parent_inquiry_id,
            reacquisition_link.child_inquiry_id,
            reacquisition_link.child_manifest_artifact,
            reacquisition_link.child_context_digest,
        ) != (
            linked_request.parent_inquiry_id,
            linked_request.child_inquiry_id,
            linked_request.child_manifest_artifact,
            linked_request.child_context_digest,
        ):
            raise InvalidCommandError("reacquisition link differs from its request pins")
        return (
            ReacquisitionInquiryLinked(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                link=reacquisition_link,
            ),
        )

    if isinstance(command, RecordRecoveryObservation):
        recovery_observation = command.observation
        existing_recovery_observation = next(
            (item for item in state.recovery_observations if item.id == recovery_observation.id),
            None,
        )
        if existing_recovery_observation is not None:
            if existing_recovery_observation == recovery_observation:
                return ()
            raise IdentityConflictError("recovery observation identity was reused")
        observation_request = next(
            (
                item
                for item in state.reacquisition_requests
                if item.id == recovery_observation.reacquisition_request_id
            ),
            None,
        )
        observation_link = next(
            (
                item
                for item in state.reacquisition_inquiry_links
                if item.request_id == recovery_observation.reacquisition_request_id
            ),
            None,
        )
        if observation_request is None or observation_link is None:
            raise InvalidCommandError("recovery observation requires a linked child inquiry")
        if any(
            item.reacquisition_request_id == recovery_observation.reacquisition_request_id
            for item in state.recovery_observations
        ):
            raise IdentityConflictError("reacquisition request already has an observation")
        if (
            recovery_observation.branch,
            recovery_observation.child_inquiry_id,
            recovery_observation.retention_package_id,
            recovery_observation.pins,
        ) != (
            observation_request.branch,
            observation_request.child_inquiry_id,
            observation_request.retention_package_id,
            observation_request.pins,
        ):
            raise InvalidCommandError("recovery observation differs from request pins")
        if recovery_observation.child_prefix_sequence < observation_link.child_prefix_sequence:
            raise InvalidCommandError("recovery observation predates its child linkage")
        if (
            not recovery_observation.competence_established
            and recovery_observation.competence_check is not None
        ):
            raise InvalidCommandError("unsuccessful recovery cannot carry a competence check")
        _require_g2a_check(
            state,
            recovery_observation.measurement_check,
            proposition_id=recovery_observation.measurement_proposition_id,
            scope_fingerprint=recovery_observation.pins.scope_fingerprint,
        )
        if recovery_observation.competence_check is not None:
            _require_g2a_check(
                state,
                recovery_observation.competence_check,
                proposition_id=recovery_observation.pins.target_competence_id,
                scope_fingerprint=recovery_observation.pins.scope_fingerprint,
            )
        return (
            RecoveryObservationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                observation=recovery_observation,
            ),
        )

    if isinstance(command, RecordRecoveryComparison):
        recovery_comparison = command.comparison
        existing_recovery_comparison = next(
            (item for item in state.recovery_comparisons if item.id == recovery_comparison.id),
            None,
        )
        if existing_recovery_comparison is not None:
            if existing_recovery_comparison == recovery_comparison:
                return ()
            raise IdentityConflictError("recovery comparison identity was reused")
        observations = {item.id: item for item in state.recovery_observations}
        try:
            baseline_observations = tuple(
                observations[identifier]
                for identifier in recovery_comparison.baseline_frontier.source_observation_ids
            )
            retained_observations = tuple(
                observations[identifier]
                for identifier in recovery_comparison.retained_frontier.source_observation_ids
            )
        except KeyError as error:
            raise InvalidCommandError(
                "recovery comparison references an unknown observation"
            ) from error
        try:
            baseline = derive_recovery_frontier(
                branch=recovery_comparison.baseline_frontier.branch,
                pins=recovery_comparison.baseline_frontier.pins,
                observations=baseline_observations,
            )
            retained = derive_recovery_frontier(
                branch=recovery_comparison.retained_frontier.branch,
                pins=recovery_comparison.retained_frontier.pins,
                observations=retained_observations,
            )
            expected = compare_recovery_frontiers(
                comparison_id=recovery_comparison.id,
                baseline=baseline,
                retained=retained,
                comparison_check=recovery_comparison.comparison_check,
            )
        except RecoveryCompatibilityError as error:
            raise InvalidCommandError(str(error)) from error
        if expected != recovery_comparison:
            raise InvalidCommandError("recovery comparison is not the exact derived result")
        _require_g2a_check(
            state,
            recovery_comparison.comparison_check,
            proposition_id=recovery_comparison.comparison_proposition_id,
            scope_fingerprint=recovery_comparison.baseline_frontier.pins.scope_fingerprint,
        )
        return (
            RecoveryComparisonRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                comparison=recovery_comparison,
            ),
        )

    if isinstance(command, RecordConsolidationCheckpoint):
        checkpoint = command.checkpoint
        existing_consolidation_checkpoint = next(
            (item for item in state.consolidation_checkpoints if item.id == checkpoint.id), None
        )
        if existing_consolidation_checkpoint is not None:
            if existing_consolidation_checkpoint == checkpoint:
                return ()
            raise IdentityConflictError("consolidation checkpoint identity was reused")
        if state.context is None or (
            checkpoint.scope_fingerprint,
            checkpoint.binding_revision,
            checkpoint.protected_horizon_id,
        ) != (
            state.context.scope_fingerprint,
            state.context.binding_revision,
            state.context.protected_horizon_id,
        ):
            raise InvalidCommandError("consolidation checkpoint pins differ from inquiry context")
        expected_consolidation_checkpoint = select_consolidation_checkpoint(
            checkpoint_id=checkpoint.id,
            policy=checkpoint.policy,
            source_sequence=state.sequence,
            scope_fingerprint=checkpoint.scope_fingerprint,
            binding_revision=checkpoint.binding_revision,
            protected_horizon_id=checkpoint.protected_horizon_id,
            probe_observations=state.probe_observations,
            claims=state.claims,
            conflicts=state.conflicts,
            mismatches=state.mismatches,
            accepted_counterexample_requests={
                item.request.id: item for item in state.effect_requests
            },
        )
        if checkpoint != expected_consolidation_checkpoint:
            raise InvalidCommandError("consolidation checkpoint is not the exact policy selection")
        return (
            ConsolidationCheckpointRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                checkpoint=checkpoint,
            ),
        )

    if isinstance(command, RecordConsolidationCandidate):
        consolidation_candidate = command.candidate
        existing_consolidation_candidate = next(
            (
                item
                for item in state.consolidation_candidates
                if item.id == consolidation_candidate.id
            ),
            None,
        )
        if existing_consolidation_candidate is not None:
            if existing_consolidation_candidate == consolidation_candidate:
                return ()
            raise IdentityConflictError("consolidation candidate identity was reused")
        candidate_checkpoint = next(
            (
                item
                for item in state.consolidation_checkpoints
                if item.id == consolidation_candidate.checkpoint_id
            ),
            None,
        )
        candidate_claim = state.claim_by_id(consolidation_candidate.generalization_claim_id)
        obligation_by_id = {item.id: item for item in state.obligations}
        if (
            candidate_checkpoint is None
            or candidate_checkpoint.status is not ConsolidationStatus.READY
        ):
            raise InvalidCommandError("consolidation requires a ready checkpoint")
        if candidate_claim is None or candidate_claim.role is not ClaimRole.GENERALIZATION:
            raise InvalidCommandError(
                "consolidation output must be an ordinary generalization claim"
            )
        if consolidation_candidate.boundary.scope != candidate_claim.scope or (
            state.context is None
            or consolidation_candidate.boundary.scope.fingerprint != state.context.scope_fingerprint
        ):
            raise InvalidCommandError("consolidation boundary must preserve exact claim scope")
        referenced_obligations = (
            *consolidation_candidate.challenge_obligation_ids,
            *consolidation_candidate.boundary.open_dependency_obligation_ids,
        )
        if any(
            obligation_by_id.get(identifier) is None
            or state.current_obligation_status(identifier) is not ObligationStatus.OPEN
            for identifier in referenced_obligations
        ):
            raise InvalidCommandError("consolidation challenges and dependencies must be open")
        return (
            ConsolidationCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=consolidation_candidate,
            ),
        )

    if isinstance(command, RecordMemoryPatchCandidate):
        memory_patch = command.candidate
        existing_memory_patch = next(
            (item for item in state.memory_patch_candidates if item.id == memory_patch.id), None
        )
        if existing_memory_patch is not None:
            if existing_memory_patch == memory_patch:
                return ()
            raise IdentityConflictError("memory patch identity was reused")
        patch_version = next(
            (item for item in state.lemma_versions if item.id == memory_patch.target_lemma_id), None
        )
        patch_mismatch = next(
            (item for item in state.mismatches if item.id == memory_patch.triggering_mismatch_id),
            None,
        )
        patch_claim = state.claim_by_id(memory_patch.proposed_claim_id)
        if patch_version is None or patch_version.id not in _current_active_lemma_ids(state):
            raise InvalidCommandError("memory patch requires an active predecessor lemma")
        if (
            patch_mismatch is None
            or patch_mismatch.external_return_id != memory_patch.triggering_return_id
        ):
            raise InvalidCommandError("memory patch must pin its exact mismatch and return")
        if patch_claim is None or patch_claim.scope.fingerprint != memory_patch.scope_fingerprint:
            raise InvalidCommandError("memory patch must name an owned in-scope proposed claim")
        patch_support = next(
            (item for item in state.lemma_supports if item.lemma_version_id == patch_version.id),
            None,
        )
        if patch_support is None or not set(memory_patch.predecessor_support_route_ids) <= {
            route.id for route in patch_support.all_support_routes
        }:
            raise InvalidCommandError(
                "memory patch support routes are not owned by its predecessor"
            )
        dependencies = {
            dependency
            for route in patch_support.all_support_routes
            if route.id in memory_patch.predecessor_support_route_ids
            for dependency in route.required_dependency_ids
        }
        dispositions = {item.dependency_id: item for item in memory_patch.dependency_dispositions}
        if set(dispositions) != dependencies:
            raise InvalidCommandError(
                "memory patch must explicitly transport or discharge every dependency"
            )
        decisions = {item.id: item for item in state.warrant_decisions}
        versions = {item.id: item for item in state.lemma_versions}
        for dependency_id, disposition in dispositions.items():
            if disposition.kind is DependencyDispositionKind.TRANSPORTED:
                continue
            decision = decisions.get(disposition.warrant_decision_id or "")
            dependency = versions.get(dependency_id)
            if (
                decision is None
                or dependency is None
                or decision.warrant_class is not WarrantClass.HARD
                or decision.proposition_id != dependency.relation_id
                or decision.scope_fingerprint != dependency.scope.fingerprint
            ):
                raise InvalidCommandError("dependency discharge requires an exact hard decision")
        if any(
            state.current_obligation_status(identifier) is not ObligationStatus.OPEN
            for identifier in memory_patch.challenge_obligation_ids
        ):
            raise InvalidCommandError("memory patch challenges must remain open")
        return (
            MemoryPatchCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=memory_patch,
            ),
        )

    if isinstance(command, RecordReconsolidationLink):
        reconsolidation_link = command.link
        existing_reconsolidation_link = next(
            (item for item in state.reconsolidation_links if item.id == reconsolidation_link.id),
            None,
        )
        if existing_reconsolidation_link is not None:
            if existing_reconsolidation_link == reconsolidation_link:
                return ()
            raise IdentityConflictError("reconsolidation link identity was reused")
        linked_patch = next(
            (
                item
                for item in state.memory_patch_candidates
                if item.id == reconsolidation_link.memory_patch_id
            ),
            None,
        )
        predecessor = next(
            (
                item
                for item in state.lemma_versions
                if item.id == reconsolidation_link.predecessor_lemma_id
            ),
            None,
        )
        successor = next(
            (
                item
                for item in state.lemma_versions
                if item.id == reconsolidation_link.successor_lemma_id
            ),
            None,
        )
        correction = next(
            (item for item in state.corrections if item.id == reconsolidation_link.correction_id),
            None,
        )
        successor_promotion = next(
            (
                item
                for item in state.promotion_links
                if item.lemma_version_id == reconsolidation_link.successor_lemma_id
            ),
            None,
        )
        if linked_patch is None or predecessor is None or successor is None or correction is None:
            raise InvalidCommandError(
                "reconsolidation link requires owned patch and succession records"
            )
        if (
            linked_patch.target_lemma_id != predecessor.id
            or predecessor.id not in successor.predecessor_refs
        ):
            raise InvalidCommandError(
                "reconsolidation successor must preserve predecessor ancestry"
            )
        if correction.target_id != predecessor.id or successor.id not in correction.related_ids:
            raise InvalidCommandError(
                "reconsolidation correction must link predecessor to successor"
            )
        if (
            successor_promotion is None
            or successor_promotion.warrant_decision_id != reconsolidation_link.warrant_decision_id
        ):
            raise InvalidCommandError(
                "reconsolidation successor requires its exact promotion warrant"
            )
        if any(
            state.current_obligation_status(identifier) is not ObligationStatus.SATISFIED
            for identifier in linked_patch.challenge_obligation_ids
        ):
            raise InvalidCommandError(
                "reconsolidation cannot apply before all attacks are discharged"
            )
        return (
            ReconsolidationLinked(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                link=reconsolidation_link,
            ),
        )

    if isinstance(command, RecordSemanticFieldEvaluation):
        field_evaluation = command.evaluation
        existing_field_evaluation = next(
            (item for item in state.semantic_field_evaluations if item.id == field_evaluation.id),
            None,
        )
        if existing_field_evaluation is not None:
            if existing_field_evaluation == field_evaluation:
                return ()
            raise IdentityConflictError("semantic-field evaluation identity was reused")
        if field_evaluation.source_sequence != state.sequence:
            raise InvalidCommandError("semantic-field evaluation must pin current source sequence")
        expected_field_evaluation = evaluate_conservative_field(
            evaluation_id=field_evaluation.id,
            field=field_evaluation.field,
            policy=field_evaluation.policy,
            source_sequence=field_evaluation.source_sequence,
            source_index_fingerprint=field_evaluation.source_index_fingerprint,
            probe_fingerprint=field_evaluation.probe_fingerprint,
            required_structure_ids=field_evaluation.required_structure_ids,
            overflow_structure_ids=field_evaluation.overflow_structure_ids,
        )
        if expected_field_evaluation != field_evaluation:
            raise InvalidCommandError("semantic-field diagnostic is not exactly recomputed")
        if state.context is None:
            raise InvalidCommandError("semantic-field evaluation requires inquiry context")
        expected_overflow_residual = semantic_field_overflow_residual(
            field_evaluation,
            Scope(
                id=state.context.scope_id,
                binding_revision=state.context.binding_revision,
                assumption_ids=state.context.assumption_ids,
                applicability_guard_id=state.context.guard_condition_id,
                finite_universe_hash=state.context.finite_universe_hash,
                closed_world=state.context.closed_world,
            ),
        )
        if command.overflow_residual != expected_overflow_residual:
            raise InvalidCommandError("semantic-field overflow must preserve its exact residual")
        active_versions = {
            version.id: version
            for version in state.lemma_versions
            if version.id in _current_active_lemma_ids(state)
        }
        for item in field_evaluation.field.items:
            if item.relevance is not RelevanceStatus.IRRELEVANT:
                continue
            warrant = active_versions.get(item.irrelevance_warrant_id or "")
            if warrant is None or warrant.relation_id != f"consequence-null:{item.structure_id}":
                raise InvalidCommandError(
                    "irrelevance requires an active exact hard consequence-null lemma"
                )
        return (
            SemanticFieldEvaluationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                evaluation=field_evaluation,
                overflow_residual=command.overflow_residual,
            ),
        )

    if isinstance(command, RecordRepresentationGap):
        gap = command.gap
        existing_gap = next((item for item in state.representation_gaps if item.id == gap.id), None)
        if existing_gap is not None:
            if existing_gap == gap:
                return ()
            raise IdentityConflictError("representation-gap identity was reused")
        if state.context is None or (
            gap.scope_fingerprint,
            gap.binding_revision,
            gap.protected_horizon_id,
        ) != (
            state.context.scope_fingerprint,
            state.context.binding_revision,
            state.context.protected_horizon_id,
        ):
            raise InvalidCommandError("representation gap pins differ from inquiry context")
        if state.obligation_by_id(gap.obligation_id) is None:
            raise InvalidCommandError("representation gap requires an owned obligation")
        known_probes = {item.fingerprint for item in state.admitted_probes}
        if not set(gap.failed_probe_fingerprints) <= known_probes:
            raise InvalidCommandError(
                "representation gap references a probe not admitted by policy"
            )
        return (
            RepresentationGapRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                gap=gap,
            ),
        )

    if isinstance(command, RecordLearnedProbeCandidate):
        learned_candidate = command.candidate
        existing_learned_candidate = next(
            (item for item in state.learned_probe_candidates if item.id == learned_candidate.id),
            None,
        )
        if existing_learned_candidate is not None:
            if existing_learned_candidate == learned_candidate:
                return ()
            raise IdentityConflictError("learned-probe candidate identity was reused")
        candidate_gap = next(
            (
                item
                for item in state.representation_gaps
                if item.id == learned_candidate.representation_gap_id
            ),
            None,
        )
        if (
            candidate_gap is None
            or state.context is None
            or (
                learned_candidate.probe_identity.scope_fingerprint,
                learned_candidate.probe_identity.binding_revision,
                learned_candidate.probe_identity.protected_horizon_id,
            )
            != (
                state.context.scope_fingerprint,
                state.context.binding_revision,
                state.context.protected_horizon_id,
            )
        ):
            raise InvalidCommandError(
                "learned-probe candidate requires an exact owned gap and context"
            )
        if any(
            state.current_obligation_status(identifier) is not ObligationStatus.OPEN
            for identifier in learned_candidate.challenge_obligation_ids
        ):
            raise InvalidCommandError("learned-probe attacks must be open obligations")
        return (
            LearnedProbeCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=learned_candidate,
            ),
        )

    if isinstance(command, RecordProbeEvaluation):
        probe_evaluation = command.evaluation
        existing_probe_evaluation = next(
            (item for item in state.probe_evaluations if item.id == probe_evaluation.id),
            None,
        )
        if existing_probe_evaluation is not None:
            if existing_probe_evaluation == probe_evaluation:
                return ()
            raise IdentityConflictError("probe-evaluation identity was reused")
        evaluated_candidate = next(
            (
                item
                for item in state.learned_probe_candidates
                if item.id == probe_evaluation.candidate_probe_id
            ),
            None,
        )
        if evaluated_candidate is None:
            raise InvalidCommandError("probe evaluation requires an owned candidate")
        expected_probe_evaluation = build_probe_evaluation(
            evaluation_id=probe_evaluation.id,
            candidate_probe_id=probe_evaluation.candidate_probe_id,
            samples=probe_evaluation.samples,
            protocol=probe_evaluation.protocol,
            redundancy_check=probe_evaluation.redundancy_check,
            protected_behavior_check=probe_evaluation.protected_behavior_check,
        )
        if expected_probe_evaluation != probe_evaluation:
            raise InvalidCommandError("probe evaluation is not the exact deterministic result")
        observation_ids = {item.id for item in state.probe_observations}
        if (
            not set(
                (
                    *probe_evaluation.training_observation_ids,
                    *probe_evaluation.holdout_observation_ids,
                )
            )
            <= observation_ids
        ):
            raise InvalidCommandError("probe evaluation references unknown observations")
        for check_reference in (
            probe_evaluation.redundancy_check,
            probe_evaluation.protected_behavior_check,
        ):
            _require_g2a_check(
                state,
                check_reference,
                proposition_id=probe_evaluation.evaluation_proposition_id,
                scope_fingerprint=evaluated_candidate.probe_identity.scope_fingerprint,
            )
        return (
            ProbeEvaluationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                evaluation=probe_evaluation,
            ),
        )

    if isinstance(command, RecordProbeAdmissionDecision):
        admission_decision = command.decision
        existing_admission_decision = next(
            (item for item in state.probe_admission_decisions if item.id == admission_decision.id),
            None,
        )
        if existing_admission_decision is not None:
            if existing_admission_decision == admission_decision:
                return ()
            raise IdentityConflictError("probe-admission decision identity was reused")
        admission_candidate = next(
            (
                item
                for item in state.learned_probe_candidates
                if item.id == admission_decision.candidate_probe_id
            ),
            None,
        )
        admission_evaluation = next(
            (
                item
                for item in state.probe_evaluations
                if item.id == admission_decision.evaluation_id
            ),
            None,
        )
        if (
            admission_candidate is None
            or admission_evaluation is None
            or admission_evaluation.candidate_probe_id != admission_candidate.id
        ):
            raise InvalidCommandError("probe admission requires its exact candidate evaluation")
        challenges_closed = all(
            state.current_obligation_status(identifier) is ObligationStatus.SATISFIED
            for identifier in admission_candidate.challenge_obligation_ids
        )
        qualifies = (
            challenges_closed
            and admission_evaluation.training_discrimination_gain > 0
            and admission_evaluation.holdout_discrimination_gain > 0
            and admission_evaluation.protected_error_count == 0
        )
        if admission_decision.outcome is ProbeAdmissionOutcome.ADMIT and not qualifies:
            raise InvalidCommandError("learned probe does not satisfy controller admission policy")
        if admission_decision.outcome is ProbeAdmissionOutcome.ADMIT and any(
            item.fingerprint == admission_candidate.probe_identity.fingerprint
            for item in state.admitted_probes
        ):
            raise IdentityConflictError("learned probe identity is already admitted")
        return (
            ProbeAdmissionDecisionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=admission_decision,
            ),
        )

    if isinstance(command, RegisterBindingCarrierManifest):
        manifest = command.manifest
        existing_carrier_manifest = next(
            (item for item in state.binding_carrier_manifests if item.id == manifest.id), None
        )
        if existing_carrier_manifest is not None:
            if existing_carrier_manifest == manifest:
                return ()
            raise IdentityConflictError("carrier-manifest identity was reused")
        if state.context is None or manifest.binding_revision != state.context.binding_revision:
            raise InvalidCommandError("carrier manifest must match the inquiry binding revision")
        declared_schema_ids = set(state.context.carrier_schema_ids)
        if manifest.configuration_carrier.schema_id not in declared_schema_ids:
            raise InvalidCommandError("configuration carrier schema is not pinned by the inquiry")
        if manifest.realized_history_carrier.schema_id not in declared_schema_ids:
            raise InvalidCommandError("history carrier schema is not pinned by the inquiry")
        return (
            BindingCarrierManifestRegistered(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                manifest=manifest,
            ),
        )

    if isinstance(command, RecordRealizedHistoryDerivation):
        derivation = command.derivation
        existing_history_derivation = next(
            (item for item in state.realized_history_derivations if item.id == derivation.id),
            None,
        )
        if existing_history_derivation is not None:
            if existing_history_derivation == derivation:
                return ()
            raise IdentityConflictError("history-derivation identity was reused")
        if not any(
            item.id == derivation.carrier_manifest_id for item in state.binding_carrier_manifests
        ):
            raise InvalidCommandError("history derivation requires an owned carrier manifest")
        if derivation.source_ledger_sequence != state.sequence:
            raise InvalidCommandError("history derivation must pin the current committed prefix")
        if derivation.status is HistoryDerivationStatus.DERIVED:
            assert derivation.derivation_check is not None
            assert state.context is not None
            _require_g2a_check(
                state,
                derivation.derivation_check,
                proposition_id=f"history-derivation:{derivation.id}",
                scope_fingerprint=state.context.scope_fingerprint,
            )
        return (
            RealizedHistoryDerivationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                derivation=derivation,
            ),
        )

    if isinstance(command, RegisterCompressionContract):
        contract = command.contract
        existing_compression_contract = next(
            (item for item in state.compression_contracts if item.id == contract.id), None
        )
        if existing_compression_contract is not None:
            if existing_compression_contract == contract:
                return ()
            raise IdentityConflictError("compression-contract identity was reused")
        carrier_manifest = next(
            (
                item
                for item in state.binding_carrier_manifests
                if item.id == contract.carrier_manifest_id
            ),
            None,
        )
        if carrier_manifest is None or state.context is None:
            raise InvalidCommandError("compression contract requires its carrier manifest")
        carriers = (
            carrier_manifest.configuration_carrier,
            carrier_manifest.realized_history_carrier,
            *carrier_manifest.other_carriers,
        )
        if not any(item.id == contract.source_carrier_id for item in carriers):
            raise InvalidCommandError("compression source carrier is not explicitly declared")
        if (
            contract.binding_revision,
            contract.scope_fingerprint,
            contract.protected_horizon_id,
        ) != (
            state.context.binding_revision,
            state.context.scope_fingerprint,
            state.context.protected_horizon_id,
        ):
            raise InvalidCommandError("compression contract pins must match inquiry context")
        return (
            CompressionContractRegistered(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                contract=contract,
            ),
        )

    if isinstance(command, RecordCompressionValidation):
        validation = command.validation
        existing_compression_validation = next(
            (item for item in state.compression_validations if item.id == validation.id), None
        )
        if existing_compression_validation is not None:
            if existing_compression_validation == validation:
                return ()
            raise IdentityConflictError("compression-validation identity was reused")
        validation_contract = next(
            (item for item in state.compression_contracts if item.id == validation.contract_id),
            None,
        )
        if validation_contract is None:
            raise InvalidCommandError("compression validation requires an owned contract")
        expected_fingerprint = sha256_digest(canonical_json_bytes(validation_contract))
        if validation.contract_fingerprint != expected_fingerprint:
            raise InvalidCommandError("compression validation does not pin the exact contract")
        by_property = {item.property: item for item in validation.properties}
        required = {
            ValidationProperty.CONSEQUENCE_FACTORIZATION,
            ValidationProperty.RESIDUE_COMPLETENESS,
        }
        if ExactClaimKind.COARSEST_EXACT_QUOTIENT in validation_contract.claim_kinds:
            required.add(ValidationProperty.EXACT_EQUIVALENCE)
        if ExactClaimKind.EXECUTABLE_RETAINED_STATE in validation_contract.claim_kinds:
            required.update(
                {
                    ValidationProperty.CONTINUATION_COMPATIBILITY,
                    ValidationProperty.RECURSIVE_UPDATE,
                }
            )
        for property_kind in required:
            if by_property[property_kind].outcome is ValidationOutcome.NOT_CLAIMED:
                raise InvalidCommandError(
                    f"compression claim requires a disposition for {property_kind.value}"
                )
        for property_check in validation.properties:
            if property_check.outcome is ValidationOutcome.NOT_CLAIMED:
                continue
            assert property_check.check is not None
            assert property_check.proposition_id is not None
            expected_property_proposition = (
                f"compression-property:{validation_contract.id}:{property_check.property.value}"
            )
            if property_check.proposition_id != expected_property_proposition:
                raise InvalidCommandError(
                    "compression property check is not bound to its exact contract property"
                )
            _require_g2a_check(
                state,
                property_check.check,
                proposition_id=property_check.proposition_id,
                scope_fingerprint=validation_contract.scope_fingerprint,
            )
        return (
            CompressionValidationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                validation=validation,
            ),
        )

    if isinstance(command, GrantExactCompressionLicense):
        license_record = command.license
        existing_exact_license = next(
            (item for item in state.exact_compression_licenses if item.id == license_record.id),
            None,
        )
        if existing_exact_license is not None:
            if existing_exact_license == license_record:
                return ()
            raise IdentityConflictError("exact-license identity was reused")
        licensed_contract = next(
            (item for item in state.compression_contracts if item.id == license_record.contract_id),
            None,
        )
        licensed_validation = next(
            (
                item
                for item in state.compression_validations
                if item.id == license_record.validation_id
            ),
            None,
        )
        decision = state.warrant_decision_by_id(license_record.warrant_decision_id)
        if (
            licensed_contract is None
            or licensed_validation is None
            or licensed_validation.contract_id != licensed_contract.id
        ):
            raise InvalidCommandError("exact license requires its exact contract validation")
        if not licensed_validation.valid:
            raise InvalidCommandError("invalid compression validation cannot be licensed")
        if (
            state.context is None
            or license_record.policy_version != state.context.warrant_policy_version
        ):
            raise InvalidCommandError("exact license must use the active warrant policy")
        if (
            decision is None
            or decision.warrant_class is not WarrantClass.HARD
            or decision.proposition_id != f"compression-license:{licensed_validation.id}"
            or decision.scope_fingerprint != licensed_contract.scope_fingerprint
            or decision.policy_version != license_record.policy_version
        ):
            raise InvalidCommandError("exact license requires an exact active hard warrant")
        if license_record.predecessor_license_id is not None and not any(
            item.id == license_record.predecessor_license_id
            for item in state.exact_compression_licenses
        ):
            raise InvalidCommandError("compression-license predecessor is not owned")
        return (
            ExactCompressionLicenseGranted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                license=license_record,
            ),
        )

    if isinstance(command, RecordCompressionApplication):
        application = command.application
        existing_application = next(
            (item for item in state.compression_applications if item.id == application.id), None
        )
        if existing_application is not None:
            if existing_application == application and all(
                item in state.path_residues for item in command.path_residues
            ):
                return ()
            raise IdentityConflictError("compression-application identity was reused")
        application_license = next(
            (
                item
                for item in state.exact_compression_licenses
                if item.id == application.license_id
            ),
            None,
        )
        application_derivation = next(
            (
                item
                for item in state.realized_history_derivations
                if item.id == application.source_history_derivation_id
            ),
            None,
        )
        if application_license is None or application_derivation is None:
            raise InvalidCommandError("compression application requires license and history")
        if (
            application_derivation.status is not HistoryDerivationStatus.DERIVED
            or application_derivation.history_artifact != application.source_artifact
        ):
            raise InvalidCommandError(
                "compression application must consume its exact derived history"
            )
        if application.retained_state_fingerprint != application.retained_state_artifact.digest:
            raise InvalidCommandError("retained-state fingerprint must pin the exact CAS bytes")
        supplied_residues = {item.id: item for item in command.path_residues}
        if set(application.path_residue_ids) != set(supplied_residues):
            raise InvalidCommandError(
                "application must atomically provide every named path residue"
            )
        application_contract = next(
            (
                item
                for item in state.compression_contracts
                if item.id == application_license.contract_id
            ),
            None,
        )
        if application_contract is None or any(
            item.contract_id != application_contract.id for item in command.path_residues
        ):
            raise InvalidCommandError("path residue must belong to the applied contract")
        if any(
            item.source_history_derivation_id != application_derivation.id
            for item in command.path_residues
        ):
            raise InvalidCommandError("path residue must belong to the applied history")
        if any(
            item.id in {prior.id for prior in state.path_residues} for item in command.path_residues
        ):
            raise InvalidCommandError("path-residue identity is already owned")
        return (
            CompressionApplicationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                application=application,
                path_residues=command.path_residues,
            ),
        )

    if isinstance(command, GrantRecoveryLicense):
        recovery_license_record = command.license
        existing_recovery_license = next(
            (item for item in state.recovery_licenses if item.id == recovery_license_record.id),
            None,
        )
        if existing_recovery_license is not None:
            if existing_recovery_license == recovery_license_record:
                return ()
            raise IdentityConflictError("recovery-license identity was reused")
        recovery_application = next(
            (
                item
                for item in state.compression_applications
                if item.id == recovery_license_record.compression_application_id
            ),
            None,
        )
        recovery_package = next(
            (
                item
                for item in state.retention_packages
                if item.id == recovery_license_record.retention_package_id
            ),
            None,
        )
        recovery_warrant = state.warrant_decision_by_id(recovery_license_record.warrant_decision_id)
        route_ids = (
            set()
            if recovery_package is None
            else {
                *recovery_package.direct_use_route_ids,
                *recovery_package.reconstruction_route_ids,
                *recovery_package.consequence_evaluation_route_ids,
                *recovery_package.reacquisition_route_ids,
            }
        )
        if (
            recovery_application is None
            or recovery_package is None
            or recovery_license_record.route_id not in route_ids
        ):
            raise InvalidCommandError("recovery license requires exact application/package route")
        if (
            state.context is None
            or recovery_license_record.policy_version != state.context.warrant_policy_version
        ):
            raise InvalidCommandError("recovery license must use the active warrant policy")
        if (
            recovery_warrant is None
            or recovery_warrant.warrant_class is not WarrantClass.HARD
            or recovery_warrant.proposition_id != f"recovery-license:{recovery_license_record.id}"
            or recovery_warrant.scope_fingerprint != recovery_package.scope_fingerprint
        ):
            raise InvalidCommandError("recovery license requires an exact active hard warrant")
        return (
            RecoveryLicenseGranted(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                license=recovery_license_record,
            ),
        )

    if isinstance(command, LinkRetentionCapability):
        capability_link = command.link
        existing_capability_link = next(
            (item for item in state.retention_capability_links if item.id == capability_link.id),
            None,
        )
        if existing_capability_link is not None:
            if existing_capability_link == capability_link:
                return ()
            raise IdentityConflictError("retention-capability link identity was reused")
        recovery_license = next(
            (
                item
                for item in state.recovery_licenses
                if item.id == capability_link.recovery_license_id
            ),
            None,
        )
        if recovery_license is None or (
            recovery_license.compression_application_id,
            recovery_license.retention_package_id,
            recovery_license.route_id,
        ) != (
            capability_link.compression_application_id,
            capability_link.retention_package_id,
            capability_link.route_id,
        ):
            raise InvalidCommandError("retention capability link must match its recovery license")
        return (
            RetentionCapabilityLinked(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                link=capability_link,
            ),
        )

    if isinstance(command, DecideRepresentationSuccessor):
        decision_record = command.decision
        existing_successor_decision = next(
            (
                item
                for item in state.representation_successor_decisions
                if item.id == decision_record.id
            ),
            None,
        )
        if existing_successor_decision is not None:
            if existing_successor_decision == decision_record:
                return ()
            raise IdentityConflictError("representation-successor identity was reused")
        licenses = {item.id: item for item in state.exact_compression_licenses}
        incumbent = licenses.get(decision_record.incumbent_license_id)
        candidate = licenses.get(decision_record.candidate_license_id)
        if incumbent is None or candidate is None or incumbent.id == candidate.id:
            raise InvalidCommandError("successor decision requires two distinct owned licenses")
        candidate_contract = next(
            (item for item in state.compression_contracts if item.id == candidate.contract_id),
            None,
        )
        if candidate_contract is None:
            raise InvalidCommandError("successor candidate lacks its owned compression contract")
        covered = set(decision_record.preserved_capability_ids) | set(
            decision_record.explicitly_disposed_capability_ids
        )
        if not set(incumbent.granted_capability_ids) <= covered:
            raise InvalidCommandError(
                "successor must preserve or disposition every predecessor capability"
            )
        if decision_record.disposition is SuccessorDisposition.REPLACE:
            if candidate.predecessor_license_id != incumbent.id:
                raise InvalidCommandError("replacement candidate must name its exact predecessor")
            successor_warrant = state.warrant_decision_by_id(
                decision_record.warrant_decision_id or ""
            )
            if (
                successor_warrant is None
                or successor_warrant.warrant_class is not WarrantClass.HARD
                or successor_warrant.proposition_id
                != f"representation-successor:{decision_record.id}"
                or successor_warrant.scope_fingerprint != candidate_contract.scope_fingerprint
                or successor_warrant.policy_version != candidate.policy_version
            ):
                raise InvalidCommandError("replacement requires exact independent hard warrant")
        return (
            RepresentationSuccessorDecided(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=decision_record,
            ),
        )

    if isinstance(command, ReopenRepresentation):
        reopening = command.reopening
        existing_reopening = next(
            (item for item in state.representation_reopenings if item.id == reopening.id), None
        )
        if existing_reopening is not None:
            if existing_reopening == reopening:
                return ()
            raise IdentityConflictError("representation-reopening identity was reused")
        reopened_license = next(
            (item for item in state.exact_compression_licenses if item.id == reopening.license_id),
            None,
        )
        if reopened_license is None:
            raise InvalidCommandError("reopening requires an owned exact license")
        reopened_contract = next(
            (
                item
                for item in state.compression_contracts
                if item.id == reopened_license.contract_id
            ),
            None,
        )
        if reopened_contract is None:
            raise InvalidCommandError("reopening requires the licensed contract")
        if reopening.prior_horizon_id != reopened_contract.protected_horizon_id:
            raise InvalidCommandError("reopening prior horizon must match the licensed contract")
        _require_g2a_check(
            state,
            reopening.factorization_failure_check,
            proposition_id=f"representation-reopening:{reopening.id}",
            scope_fingerprint=reopened_contract.scope_fingerprint,
        )
        if reopening.path_residue_id is not None:
            reopening_residue = next(
                (item for item in state.path_residues if item.id == reopening.path_residue_id),
                None,
            )
            if reopening_residue is None or reopening_residue.contract_id != reopened_contract.id:
                raise InvalidCommandError("reopening path residue is not owned by the contract")
        if reopening.recovery_license_id is not None:
            reopening_recovery = next(
                (
                    item
                    for item in state.recovery_licenses
                    if item.id == reopening.recovery_license_id
                ),
                None,
            )
            recovery_application = (
                None
                if reopening_recovery is None
                else next(
                    (
                        item
                        for item in state.compression_applications
                        if item.id == reopening_recovery.compression_application_id
                    ),
                    None,
                )
            )
            if (
                recovery_application is None
                or recovery_application.license_id != reopened_license.id
            ):
                raise InvalidCommandError("reopening recovery route is not licensed for this state")
        if reopening.outcome is ReopeningOutcome.UNKNOWN and (
            reopening.path_residue_id is not None or reopening.recovery_license_id is not None
        ):
            raise InvalidCommandError("Unknown reopening cannot claim a recovery path")
        return (
            RepresentationReopened(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                reopening=reopening,
            ),
        )

    if isinstance(command, RecordProjectAnchor):
        anchor = command.anchor
        anchor_existing = next(
            (item for item in state.project_anchors if item.id == anchor.id), None
        )
        if anchor_existing is not None:
            if anchor_existing == anchor:
                return ()
            raise IdentityConflictError("project-anchor identity was reused")
        return (
            ProjectAnchorRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                anchor=anchor,
            ),
        )

    if isinstance(command, RecordCapabilityLimitation):
        limitation = command.limitation
        limitation_existing = next(
            (item for item in state.capability_limitations if item.id == limitation.id), None
        )
        if limitation_existing is not None:
            if limitation_existing == limitation:
                return ()
            raise IdentityConflictError("capability-limitation identity was reused")
        if not any(item.id == limitation.anchor_id for item in state.project_anchors):
            raise InvalidCommandError("capability limitation requires an owned clean anchor")
        return (
            CapabilityLimitationRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                limitation=limitation,
            ),
        )

    if isinstance(command, RecordQuestionContractCandidate):
        question_candidate = command.candidate
        question_existing = next(
            (
                item
                for item in state.question_contract_candidates
                if item.id == question_candidate.id
            ),
            None,
        )
        if question_existing is not None:
            if question_existing == question_candidate:
                return ()
            raise IdentityConflictError("question-candidate identity was reused")
        if not any(
            item.id == question_candidate.limitation_id for item in state.capability_limitations
        ):
            raise InvalidCommandError("question candidate requires an owned limitation")
        return (
            QuestionContractCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=question_candidate,
            ),
        )

    if isinstance(command, DecideQuestionRepertoire):
        question_decision = command.decision
        question_decision_existing = next(
            (
                item
                for item in state.question_repertoire_decisions
                if item.id == question_decision.id
            ),
            None,
        )
        if question_decision_existing is not None:
            if question_decision_existing == question_decision:
                return ()
            raise IdentityConflictError("question-decision identity was reused")
        question_candidate_record = next(
            (
                item
                for item in state.question_contract_candidates
                if item.id == question_decision.candidate_id
            ),
            None,
        )
        if question_candidate_record is None:
            raise InvalidCommandError("question decision requires its inert candidate")
        if (
            question_decision.outcome is AdmissionOutcome.ADMIT
            and question_candidate_record.contract.family != "recursive-project"
        ):
            raise InvalidCommandError("generated admission is confined to recursive-project")
        _require_project_admission_evidence(
            state,
            evidence_ids=question_decision.evidence_ids,
            limitation_id=question_candidate_record.limitation_id,
            require_valid_review=question_decision.outcome is AdmissionOutcome.ADMIT,
        )
        return (
            QuestionRepertoireDecided(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=question_decision,
            ),
        )

    if isinstance(command, RecordMethodBindingCandidate):
        method_candidate_record = command.candidate
        method_existing = next(
            (
                item
                for item in state.method_binding_candidates
                if item.id == method_candidate_record.id
            ),
            None,
        )
        if method_existing is not None:
            if method_existing == method_candidate_record:
                return ()
            raise IdentityConflictError("method-candidate identity was reused")
        if not any(
            item.id == method_candidate_record.limitation_id
            for item in state.capability_limitations
        ):
            raise InvalidCommandError("method binding requires an owned limitation")
        return (
            MethodBindingCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=method_candidate_record,
            ),
        )

    if isinstance(command, DecideMethodAdmission):
        method_decision = command.decision
        method_decision_existing = next(
            (item for item in state.method_admission_decisions if item.id == method_decision.id),
            None,
        )
        if method_decision_existing is not None:
            if method_decision_existing == method_decision:
                return ()
            raise IdentityConflictError("method-decision identity was reused")
        method_candidate = next(
            (
                item
                for item in state.method_binding_candidates
                if item.id == method_decision.candidate_id
            ),
            None,
        )
        if method_candidate is None:
            raise InvalidCommandError("method decision requires its inert candidate")
        _require_project_admission_evidence(
            state,
            evidence_ids=method_decision.evidence_ids,
            limitation_id=method_candidate.limitation_id,
            require_valid_review=method_decision.outcome is AdmissionOutcome.ADMIT,
        )
        implementation_goal = (
            next(
                (
                    item
                    for item in state.implementation_goals
                    if item.id == method_decision.implementation_goal_id
                ),
                None,
            )
            if method_decision.implementation_goal_id is not None
            else None
        )
        if method_decision.outcome is AdmissionOutcome.ADMIT and method_candidate.adapter_required:
            if implementation_goal is None:
                raise InvalidCommandError("a missing method adapter must open a sealed goal")
            goal_candidate = next(
                (
                    item
                    for item in state.capability_successor_candidates
                    if item.id == implementation_goal.candidate_id
                ),
                None,
            )
            if (
                goal_candidate is None
                or goal_candidate.limitation_id != method_candidate.limitation_id
            ):
                raise InvalidCommandError("method adapter goal must address the exact limitation")
        return (
            MethodAdmissionDecided(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=method_decision,
            ),
        )

    if isinstance(command, RecordCapabilitySuccessorCandidate):
        project_candidate = command.candidate
        project_candidate_existing = next(
            (
                item
                for item in state.capability_successor_candidates
                if item.id == project_candidate.id
            ),
            None,
        )
        if project_candidate_existing is not None:
            if project_candidate_existing == project_candidate:
                return ()
            raise IdentityConflictError("project-successor candidate identity was reused")
        if not any(
            item.id == project_candidate.anchor_id for item in state.project_anchors
        ) or not any(
            item.id == project_candidate.limitation_id for item in state.capability_limitations
        ):
            raise InvalidCommandError("project successor requires owned anchor and limitation")
        return (
            CapabilitySuccessorCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=project_candidate,
            ),
        )

    if isinstance(command, RecordCapabilityFrontier):
        project_frontier = command.frontier
        project_frontier_existing = next(
            (item for item in state.capability_frontiers if item.id == project_frontier.id),
            None,
        )
        if project_frontier_existing is not None:
            if project_frontier_existing == project_frontier:
                return ()
            raise IdentityConflictError("capability-frontier identity was reused")
        candidates_by_id = {item.id: item for item in state.capability_successor_candidates}
        try:
            expected_frontier = derive_capability_frontier(
                frontier_id=project_frontier.id,
                candidates=tuple(candidates_by_id[item] for item in project_frontier.candidate_ids),
            )
        except (KeyError, ValueError) as error:
            raise InvalidCommandError("frontier references invalid successor candidates") from error
        if expected_frontier != project_frontier:
            raise InvalidCommandError("capability frontier must equal pure deterministic selection")
        return (
            CapabilityFrontierRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                frontier=project_frontier,
            ),
        )

    if isinstance(command, RecordImplementationGoalCandidate):
        derived_goal_candidate = command.candidate
        existing_goal_candidate = next(
            (
                item
                for item in state.implementation_goal_candidates
                if item.id == derived_goal_candidate.id
            ),
            None,
        )
        if existing_goal_candidate is not None:
            if existing_goal_candidate == derived_goal_candidate:
                return ()
            raise IdentityConflictError("implementation-Goal candidate identity was reused")
        recomputed = compile_implementation_goal_candidate(
            state,
            source_obligation_id=derived_goal_candidate.source_obligation_id,
            downstream_obligation_id=derived_goal_candidate.downstream_obligation_id,
            frontier_id=derived_goal_candidate.frontier_id,
        )
        if isinstance(recomputed, GoalSynthesisUnknown) or recomputed != derived_goal_candidate:
            raise InvalidCommandError(
                "implementation-Goal candidate must equal pure deterministic compilation"
            )
        return (
            ImplementationGoalCandidateRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                candidate=derived_goal_candidate,
            ),
        )

    if isinstance(command, DecideGoalAdmission):
        goal_decision = command.decision
        existing_decision = next(
            (
                item
                for item in state.goal_admission_decisions
                if item.candidate_id == goal_decision.candidate_id
            ),
            None,
        )
        if existing_decision is not None:
            if existing_decision == goal_decision:
                return ()
            raise IdentityConflictError("a Goal candidate permits one total admission decision")
        goal_admission_candidate = next(
            (
                item
                for item in state.implementation_goal_candidates
                if item.id == goal_decision.candidate_id
            ),
            None,
        )
        if (
            goal_admission_candidate is None
            or goal_decision.candidate_fingerprint
            != content_fingerprint("rci.implementation-goal-candidate.v1", goal_admission_candidate)
            or goal_decision.evidence_record_ids
            != goal_admission_evidence_ids(goal_admission_candidate)
            or (
                goal_decision.outcome is AdmissionOutcome.ADMIT
                and goal_decision.admitted_goal_id != goal_admission_candidate.goal.id
            )
        ):
            raise InvalidCommandError("Goal admission must reference the exact derived candidate")
        return (
            GoalAdmissionDecided(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=goal_decision,
            ),
        )

    if isinstance(command, SealImplementationGoal):
        implementation_goal = command.goal
        implementation_goal_existing = next(
            (item for item in state.implementation_goals if item.id == implementation_goal.id),
            None,
        )
        if implementation_goal_existing is not None:
            if implementation_goal_existing == implementation_goal:
                return ()
            raise IdentityConflictError("sealed implementation goal is immutable")
        goal_frontier = next(
            (
                item
                for item in state.capability_frontiers
                if item.id == implementation_goal.frontier_id
            ),
            None,
        )
        if (
            goal_frontier is None
            or goal_frontier.status != "ready"
            or goal_frontier.selected_discriminator_candidate_id != implementation_goal.candidate_id
        ):
            raise InvalidCommandError(
                "goal must seal the frontier-selected discriminator candidate"
            )
        generated_candidates = tuple(
            item
            for item in state.implementation_goal_candidates
            if item.goal.id == implementation_goal.id
        )
        if generated_candidates and (
            len(generated_candidates) != 1
            or generated_candidates[0].goal != implementation_goal
            or not any(
                decision.candidate_id == generated_candidates[0].id
                and decision.outcome is AdmissionOutcome.ADMIT
                and decision.admitted_goal_id == implementation_goal.id
                for decision in state.goal_admission_decisions
            )
        ):
            raise InvalidCommandError("generated Goal requires its exact admission decision")
        return (
            ImplementationGoalSealed(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                goal=implementation_goal,
            ),
        )

    if isinstance(command, RecordCandidateEnvironment):
        candidate_manifest = command.manifest
        candidate_manifest_existing = next(
            (item for item in state.candidate_environments if item.id == candidate_manifest.id),
            None,
        )
        if candidate_manifest_existing is not None:
            if candidate_manifest_existing == candidate_manifest:
                return ()
            raise IdentityConflictError("candidate-environment identity was reused")
        environment_goal = next(
            (item for item in state.implementation_goals if item.id == candidate_manifest.goal_id),
            None,
        )
        environment_anchor = (
            next(
                (item for item in state.project_anchors if item.id == environment_goal.anchor_id),
                None,
            )
            if environment_goal is not None
            else None
        )
        if (
            environment_goal is None
            or environment_anchor is None
            or candidate_manifest.base_commit_sha != environment_anchor.commit_sha
        ):
            raise InvalidCommandError("candidate environment must start from its sealed anchor")
        return (
            CandidateEnvironmentRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                manifest=candidate_manifest,
            ),
        )

    if isinstance(command, RecordDevelopmentEvidence):
        evidence_record = command.evidence
        evidence_existing = next(
            (item for item in state.development_evidence if item.id == evidence_record.id), None
        )
        if evidence_existing is not None:
            if evidence_existing == evidence_record:
                return ()
            raise IdentityConflictError("development-evidence identity was reused")
        evidence_goal = next(
            (item for item in state.implementation_goals if item.id == evidence_record.goal_id),
            None,
        )
        evidence_environment = next(
            (
                item
                for item in state.candidate_environments
                if item.id == evidence_record.candidate_environment_id
            ),
            None,
        )
        if (
            evidence_goal is None
            or evidence_environment is None
            or evidence_environment.goal_id != evidence_goal.id
        ):
            raise InvalidCommandError(
                "development evidence requires its sealed candidate environment"
            )
        if (
            evidence_record.base_commit_sha != evidence_environment.base_commit_sha
            or evidence_record.gate_digest
            not in {
                evidence_goal.incumbent_gate_digest,
                evidence_goal.proposed_gate_digest,
            }
        ):
            raise InvalidCommandError(
                "development evidence must preserve base and sealed gate pins"
            )
        return (
            DevelopmentEvidenceRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                evidence=evidence_record,
            ),
        )

    if isinstance(command, RecordIndependentReview):
        independent_review = command.review
        review_existing = next(
            (item for item in state.independent_reviews if item.id == independent_review.id),
            None,
        )
        if review_existing is not None:
            if review_existing == independent_review:
                return ()
            raise IdentityConflictError("independent-review identity was reused")
        review_environment = next(
            (
                item
                for item in state.candidate_environments
                if item.id == independent_review.candidate_environment_id
            ),
            None,
        )
        evidence_by_id = {item.id: item for item in state.development_evidence}
        try:
            reviewed_evidence = tuple(
                evidence_by_id[item] for item in independent_review.evidence_ids
            )
        except KeyError as error:
            raise InvalidCommandError("review references unknown development evidence") from error
        if (
            review_environment is None
            or review_environment.goal_id != independent_review.goal_id
            or independent_review.reviewer_id == review_environment.developer_id
            or any(item.goal_id != independent_review.goal_id for item in reviewed_evidence)
            or any(
                item.candidate_environment_id != independent_review.candidate_environment_id
                for item in reviewed_evidence
            )
            or any(
                item.candidate_commit_sha != independent_review.reviewed_commit_sha
                for item in reviewed_evidence
            )
        ):
            raise InvalidCommandError("review must be fresh, independent, and exact-head bound")
        if independent_review.outcome is ReviewOutcome.VALID and any(
            item.outcome is not EvidenceOutcome.PASS for item in reviewed_evidence
        ):
            raise InvalidCommandError("a valid review cannot bless failing or unknown evidence")
        return (
            IndependentReviewRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                review=independent_review,
            ),
        )

    if isinstance(command, DecideProjectSuccessor):
        project_decision = command.decision
        project_decision_existing = next(
            (item for item in state.project_successor_decisions if item.id == project_decision.id),
            None,
        )
        if project_decision_existing is not None:
            if project_decision_existing == project_decision:
                return ()
            raise IdentityConflictError("project-successor decision identity was reused")
        successor_goal = next(
            (item for item in state.implementation_goals if item.id == project_decision.goal_id),
            None,
        )
        decided_candidate = next(
            (
                item
                for item in state.capability_successor_candidates
                if item.id == project_decision.candidate_id
            ),
            None,
        )
        successor_review = next(
            (item for item in state.independent_reviews if item.id == project_decision.review_id),
            None,
        )
        successor_environment = next(
            (
                item
                for item in state.candidate_environments
                if item.id == project_decision.candidate_environment_id
            ),
            None,
        )
        evidence_by_id = {item.id: item for item in state.development_evidence}
        try:
            decision_evidence = tuple(
                evidence_by_id[item] for item in project_decision.evidence_ids
            )
        except KeyError as error:
            raise InvalidCommandError("successor decision references unknown evidence") from error
        if (
            successor_goal is None
            or decided_candidate is None
            or successor_review is None
            or successor_environment is None
        ):
            raise InvalidCommandError("successor decision requires its complete owned proof chain")
        if (
            successor_goal.candidate_id,
            successor_environment.goal_id,
            successor_review.goal_id,
            successor_review.candidate_environment_id,
        ) != (
            decided_candidate.id,
            successor_goal.id,
            successor_goal.id,
            successor_environment.id,
        ):
            raise InvalidCommandError("successor proof chain does not name one sealed candidate")
        if tuple(project_decision.evidence_ids) != tuple(successor_review.evidence_ids):
            raise InvalidCommandError("successor decision must use exactly the reviewed evidence")
        if project_decision.disposition is ProjectDisposition.REPLACE:
            if successor_review.outcome is not ReviewOutcome.VALID or any(
                item.outcome is not EvidenceOutcome.PASS for item in decision_evidence
            ):
                raise InvalidCommandError(
                    "replacement requires valid independent review and evidence"
                )
            if not set(decided_candidate.preserved_capability_ids) <= set(
                project_decision.preserved_capability_ids
            ) or tuple(decided_candidate.gain_kinds) != tuple(project_decision.gain_kinds):
                raise InvalidCommandError("replacement must preserve and gain exactly as proposed")
        return (
            ProjectSuccessorDecided(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=project_decision,
            ),
        )

    if isinstance(command, RecordPromotionDecision):
        promotion_decision = command.decision
        promotion_existing = next(
            (item for item in state.promotion_decisions if item.id == promotion_decision.id),
            None,
        )
        if promotion_existing is not None:
            if promotion_existing == promotion_decision:
                return ()
            raise IdentityConflictError("promotion-decision identity was reused")
        promoted_successor = next(
            (
                item
                for item in state.project_successor_decisions
                if item.id == promotion_decision.successor_decision_id
            ),
            None,
        )
        promotion_review = (
            next(
                (
                    item
                    for item in state.independent_reviews
                    if item.id == promoted_successor.review_id
                ),
                None,
            )
            if promoted_successor is not None
            else None
        )
        if promoted_successor is None or promotion_review is None:
            raise InvalidCommandError(
                "promotion requires an owned independently reviewed successor"
            )
        if promotion_decision.outcome is ProjectPromotionOutcome.MERGED and (
            promoted_successor.disposition is not ProjectDisposition.REPLACE
            or promotion_review.outcome is not ReviewOutcome.VALID
            or promotion_decision.candidate_commit_sha != promotion_review.reviewed_commit_sha
        ):
            raise InvalidCommandError("merged promotion must match the validated successor head")
        return (
            PromotionDecisionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                decision=promotion_decision,
            ),
        )

    if isinstance(command, RecordRecursiveCycleCheckpoint):
        cycle_checkpoint = command.checkpoint
        checkpoint_existing = next(
            (item for item in state.recursive_cycle_checkpoints if item.id == cycle_checkpoint.id),
            None,
        )
        if checkpoint_existing is not None:
            if checkpoint_existing == cycle_checkpoint:
                return ()
            raise IdentityConflictError("cycle-checkpoint identity was reused")
        prior = tuple(
            item
            for item in state.recursive_cycle_checkpoints
            if item.cycle_id == cycle_checkpoint.cycle_id
        )
        if prior and cycle_checkpoint.predecessor_id != prior[-1].id:
            raise InvalidCommandError("cycle checkpoint must succeed the exact current tail")
        if not prior and cycle_checkpoint.predecessor_id is not None:
            raise InvalidCommandError("first cycle checkpoint cannot name a predecessor")
        if prior and list(type(cycle_checkpoint.phase)).index(cycle_checkpoint.phase) <= list(
            type(prior[-1].phase)
        ).index(prior[-1].phase):
            raise InvalidCommandError("cycle checkpoints must advance monotonically")
        owned_project_ids = {
            item.id
            for collection in (
                state.project_anchors,
                state.capability_limitations,
                state.question_contract_candidates,
                state.question_repertoire_decisions,
                state.method_binding_candidates,
                state.method_admission_decisions,
                state.capability_successor_candidates,
                state.capability_frontiers,
                state.implementation_goals,
                state.candidate_environments,
                state.development_evidence,
                state.independent_reviews,
                state.project_successor_decisions,
                state.promotion_decisions,
                state.recursive_cycle_checkpoints,
                state.recursive_stop_dispositions,
            )
            for item in collection
        }
        if not set(cycle_checkpoint.record_ids) <= owned_project_ids:
            raise InvalidCommandError("cycle checkpoint may reference only owned project records")
        return (
            RecursiveCycleCheckpointRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                checkpoint=cycle_checkpoint,
            ),
        )

    if isinstance(command, RecordRecursiveStopDisposition):
        stop_disposition = command.disposition
        stop_existing = next(
            (item for item in state.recursive_stop_dispositions if item.id == stop_disposition.id),
            None,
        )
        if stop_existing is not None:
            if stop_existing == stop_disposition:
                return ()
            raise IdentityConflictError("recursive-stop identity was reused")
        if not any(
            item.cycle_id == stop_disposition.cycle_id for item in state.recursive_cycle_checkpoints
        ):
            raise InvalidCommandError("recursive stop requires an owned cycle checkpoint")
        if not set(stop_disposition.consequential_residual_ids) <= {
            item.id for item in state.capability_limitations
        }:
            raise InvalidCommandError("recursive stop residuals must name owned limitations")
        return (
            RecursiveStopDispositionRecorded(
                event_id=command.event_id,
                inquiry_id=command.inquiry_id,
                occurred_at=command.occurred_at,
                disposition=stop_disposition,
            ),
        )

    raise InvalidCommandError(f"unsupported command type: {type(command).__name__}")


def _replace_request(
    state: InquiryState,
    replacement: EffectRequestState,
) -> tuple[EffectRequestState, ...]:
    return tuple(
        replacement if item.request.id == replacement.request.id else item
        for item in state.effect_requests
    )


def _require_matching_decision(
    state: InquiryState,
    event: DomainEvent,
    command: DomainCommand,
) -> None:
    try:
        expected = decide(state, command)
    except DomainError as exc:
        raise InvalidTransitionError(str(exc)) from exc
    if expected != (event,):
        raise InvalidTransitionError("domain event does not match the lawful command consequence")


def _advance_domain_state(
    state: InquiryState,
    **updates: object,
) -> InquiryState:
    payload = state.model_dump()
    payload.update(updates)
    payload["sequence"] = state.sequence + 1
    return InquiryState.model_validate(payload, strict=True)


def evolve(state: InquiryState, event: DomainEvent) -> InquiryState:
    """Apply one event as a deterministic, effect-free reducer."""

    if isinstance(event, InquiryStarted):
        if state.status != "not_started":
            raise InvalidTransitionError("InquiryStarted can only evolve an empty aggregate")
        return InquiryState(
            status="active",
            inquiry_id=event.inquiry_id,
            sequence=1,
            manifest_artifact=event.manifest_artifact,
            policy_version=event.policy_version,
            context=event.context,
        )

    if state.status != "active" or state.inquiry_id != event.inquiry_id:
        raise InvalidTransitionError("event inquiry id does not match an active aggregate")

    next_sequence = state.sequence + 1

    if isinstance(event, BacklogEffectRecorded):
        _require_matching_decision(
            state,
            event,
            RecordBacklogEffect(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                effect=event.effect,
            ),
        )
        return _advance_domain_state(
            state,
            backlog_effects=(*state.backlog_effects, event.effect),
        )

    if isinstance(event, StepPlanRecorded):
        _require_matching_decision(
            state,
            event,
            RecordStepPlan(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                plan=event.plan,
            ),
        )
        return _advance_domain_state(
            state,
            step_plans=(*state.step_plans, event.plan),
        )

    if isinstance(event, EffectRequested):
        if state.request_by_id(event.request.id) is not None:
            raise InvalidTransitionError("duplicate effect request event")
        if state.step_plan_by_id(event.request.step_plan_id) is None:
            raise InvalidTransitionError("effect request references an unknown step plan")
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=(*state.effect_requests, EffectRequestState(request=event.request)),
        )

    if isinstance(event, EffectAttemptPlanned):
        request = state.request_by_id(event.plan.request_id)
        if request is None:
            raise InvalidTransitionError("attempt plan references an unknown request")
        if any(
            attempt.plan.id == event.plan.id
            for item in state.effect_requests
            for attempt in item.attempts
        ):
            raise InvalidTransitionError("duplicate attempt plan event")
        if request.accepted_decoded_outcome_id is not None:
            raise InvalidTransitionError("resolved requests cannot gain attempts")
        replacement = EffectRequestState(
            request=request.request,
            attempts=(*request.attempts, AttemptState(plan=event.plan)),
            no_attempt_dispositions=request.no_attempt_dispositions,
            decode_outcomes=request.decode_outcomes,
            accepted_decoded_outcome_id=request.accepted_decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, EffectAttemptStarted):
        containing_request = next(
            (
                request
                for request in state.effect_requests
                if any(attempt.plan.id == event.attempt_id for attempt in request.attempts)
            ),
            None,
        )
        if containing_request is None:
            raise InvalidTransitionError("attempt start references an unknown attempt")
        started_attempt_state = next(
            item for item in containing_request.attempts if item.plan.id == event.attempt_id
        )
        if started_attempt_state.started:
            raise InvalidTransitionError("attempt already has start metadata")
        if containing_request.accepted_decoded_outcome_id is not None:
            raise InvalidTransitionError("a resolved request cannot start another attempt")
        attempts = tuple(
            AttemptState(
                plan=item.plan,
                started=True,
                started_event_id=event.event_id,
                started_at=event.occurred_at,
            )
            if item.plan.id == event.attempt_id
            else item
            for item in containing_request.attempts
        )
        replacement = EffectRequestState(
            request=containing_request.request,
            attempts=attempts,
            no_attempt_dispositions=containing_request.no_attempt_dispositions,
            decode_outcomes=containing_request.decode_outcomes,
            accepted_decoded_outcome_id=containing_request.accepted_decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, EffectNoAttemptDispositionRecorded):
        request = state.request_by_id(event.disposition.request_id)
        if request is None:
            raise InvalidTransitionError("no-attempt disposition references an unknown request")
        if event.disposition.step_plan_id != request.request.step_plan_id:
            raise InvalidTransitionError(
                "no-attempt disposition references a different persisted step plan"
            )
        if any(
            disposition.id == event.disposition.id
            for item in state.effect_requests
            for disposition in item.no_attempt_dispositions
        ):
            raise InvalidTransitionError("duplicate no-attempt disposition event")
        if request.accepted_decoded_outcome_id is not None:
            raise InvalidTransitionError("resolved requests cannot gain no-attempt dispositions")
        replacement = EffectRequestState(
            request=request.request,
            attempts=request.attempts,
            no_attempt_dispositions=(*request.no_attempt_dispositions, event.disposition),
            decode_outcomes=request.decode_outcomes,
            accepted_decoded_outcome_id=request.accepted_decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, EffectAttemptOutcomeRecorded):
        request = state.request_by_id(event.request_id)
        if request is None:
            raise InvalidTransitionError("attempt outcome references an unknown request")
        event_attempt = next(
            (item for item in request.attempts if item.plan.id == event.outcome.attempt_id),
            None,
        )
        if event_attempt is None:
            raise InvalidTransitionError("attempt outcome references an unknown attempt")
        if not event_attempt.started:
            raise InvalidTransitionError("attempt outcome precedes attempt start")
        if event_attempt.outcome is not None:
            raise InvalidTransitionError("an attempt already has an outcome")
        if event_attempt.plan.route.id != event.outcome.route_id:
            raise InvalidTransitionError("attempt outcome route mismatch")
        attempts = tuple(
            AttemptState(
                plan=item.plan,
                started=item.started,
                started_event_id=item.started_event_id,
                started_at=item.started_at,
                outcome=event.outcome,
            )
            if item.plan.id == event_attempt.plan.id
            else item
            for item in request.attempts
        )
        replacement = EffectRequestState(
            request=request.request,
            attempts=attempts,
            no_attempt_dispositions=request.no_attempt_dispositions,
            decode_outcomes=request.decode_outcomes,
            accepted_decoded_outcome_id=request.accepted_decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, EffectDecodeOutcomeRecorded):
        request = state.request_by_id(event.request_id)
        if request is None:
            raise InvalidTransitionError("decode outcome references an unknown request")
        if any(
            outcome.id == event.outcome.id
            for item in state.effect_requests
            for outcome in item.decode_outcomes
        ):
            raise InvalidTransitionError("duplicate decode outcome event")
        captured_return_ids = {
            attempt.outcome.external_return.id
            for attempt in request.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        }
        if event.outcome.external_return_id not in captured_return_ids:
            raise InvalidTransitionError("decode outcome has no captured external return")
        replacement = EffectRequestState(
            request=request.request,
            attempts=request.attempts,
            no_attempt_dispositions=request.no_attempt_dispositions,
            decode_outcomes=(*request.decode_outcomes, event.outcome),
            accepted_decoded_outcome_id=request.accepted_decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, EffectResultAccepted):
        request = state.request_by_id(event.request_id)
        if request is None:
            raise InvalidTransitionError("accepted result references an unknown request")
        if request.accepted_decoded_outcome_id is not None:
            raise InvalidTransitionError("an effect request already accepted a result")
        decoded = next(
            (
                outcome
                for outcome in request.decode_outcomes
                if outcome.id == event.decoded_outcome_id
            ),
            None,
        )
        if not isinstance(decoded, Decoded):
            raise InvalidTransitionError("accepted result must reference a successful decode")
        replacement = EffectRequestState(
            request=request.request,
            attempts=request.attempts,
            no_attempt_dispositions=request.no_attempt_dispositions,
            decode_outcomes=request.decode_outcomes,
            accepted_decoded_outcome_id=event.decoded_outcome_id,
        )
        return InquiryState(
            **state.model_dump(exclude={"sequence", "effect_requests"}),
            sequence=next_sequence,
            effect_requests=_replace_request(state, replacement),
        )

    if isinstance(event, ClaimAdmitted):
        _require_matching_decision(
            state,
            event,
            AdmitClaim(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                claim=event.claim,
            ),
        )
        return _advance_domain_state(
            state,
            claims=(*state.claims, event.claim),
            conflicts=(*state.conflicts, *event.derived_conflicts),
            obligations=(*state.obligations, *event.derived_obligations),
        )

    if isinstance(event, ObligationOpened):
        _require_matching_decision(
            state,
            event,
            OpenObligation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                obligation=event.obligation,
            ),
        )
        return _advance_domain_state(
            state,
            obligations=(*state.obligations, event.obligation),
        )

    if isinstance(event, ObligationDispositionRecorded):
        _require_matching_decision(
            state,
            event,
            RecordObligationDisposition(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                disposition=event.disposition,
            ),
        )
        return _advance_domain_state(
            state,
            obligation_dispositions=(
                *state.obligation_dispositions,
                event.disposition,
            ),
        )

    if isinstance(event, CandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            candidates=(*state.candidates, event.candidate),
        )

    if isinstance(event, ResidualRecorded):
        _require_matching_decision(
            state,
            event,
            RecordResidual(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                residual=event.residual,
            ),
        )
        return _advance_domain_state(
            state,
            residuals=(*state.residuals, event.residual),
        )

    if isinstance(event, CorrectionAppended):
        _require_matching_decision(
            state,
            event,
            AppendCorrection(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                correction=event.correction,
            ),
        )
        return _advance_domain_state(
            state,
            corrections=(*state.corrections, event.correction),
        )

    if isinstance(event, GuardStandingChanged):
        _require_matching_decision(
            state,
            event,
            ChangeGuardStanding(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                change=event.change,
            ),
        )
        return _advance_domain_state(
            state,
            guard_changes=(*state.guard_changes, event.change),
        )

    if isinstance(event, NogoodRecorded):
        _require_matching_decision(
            state,
            event,
            RecordNogood(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                nogood=event.nogood,
            ),
        )
        return _advance_domain_state(state, nogoods=(*state.nogoods, event.nogood))

    if isinstance(event, SupportRouteStandingChanged):
        _require_matching_decision(
            state,
            event,
            ChangeSupportRouteStanding(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                change=event.change,
            ),
        )
        return _advance_domain_state(
            state,
            support_route_standing_changes=(
                *state.support_route_standing_changes,
                event.change,
            ),
        )

    if isinstance(event, NogoodStandingChanged):
        _require_matching_decision(
            state,
            event,
            ChangeNogoodStanding(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                change=event.change,
            ),
        )
        return _advance_domain_state(
            state,
            nogood_standing_changes=(*state.nogood_standing_changes, event.change),
        )

    if isinstance(event, EvidenceRecorded):
        _require_matching_decision(
            state,
            event,
            RecordEvidence(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                evidence=event.evidence,
            ),
        )
        return _advance_domain_state(
            state,
            evidence_records=(*state.evidence_records, event.evidence),
        )

    if isinstance(event, CheckerVerdictRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCheckerVerdict(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                checker_verdict=event.checker_verdict,
            ),
        )
        return _advance_domain_state(
            state,
            checker_verdicts=(*state.checker_verdicts, event.checker_verdict),
        )

    if isinstance(event, WarrantDecisionRecorded):
        _require_matching_decision(
            state,
            event,
            EvaluateWarrant(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision_id=event.decision.id,
                evidence_id=event.decision.evidence_id,
                checker_verdict_id=event.decision.checker_verdict_id,
                proposition_id=event.decision.proposition_id,
                proposition_kind=event.decision.proposition_kind,
                scope=event.scope,
            ),
        )
        return _advance_domain_state(
            state,
            warrant_decisions=(*state.warrant_decisions, event.decision),
        )

    if isinstance(event, LemmaPromoted):
        _require_matching_decision(
            state,
            event,
            PromoteClaim(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                promotion_id=event.link.id,
                lemma_id=event.version.id,
                relation_id=event.version.relation_id,
                proposition_kind=event.version.proposition_kind,
                scope=event.version.scope,
                applicability=event.version.applicability,
                support_routes=event.support.all_support_routes,
                warrant_decision_id=event.link.warrant_decision_id,
                provenance_refs=event.support.provenance_refs,
                source_claim_ids=event.version.source_claim_ids,
                predecessor_refs=event.version.predecessor_refs,
            ),
        )
        return _advance_domain_state(
            state,
            lemma_versions=(*state.lemma_versions, event.version),
            lemma_supports=(*state.lemma_supports, event.support),
            promotion_links=(*state.promotion_links, event.link),
        )

    if isinstance(event, ProbeAdmitted):
        _require_matching_decision(
            state,
            event,
            AdmitProbe(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                probe=event.probe,
            ),
        )
        return _advance_domain_state(
            state,
            admitted_probes=(*state.admitted_probes, event.probe),
        )

    if isinstance(event, CognitivePlanRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCognitivePlan(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                plan=event.plan,
            ),
        )
        return _advance_domain_state(
            state,
            cognitive_plans=(*state.cognitive_plans, event.plan),
        )

    if isinstance(event, PredictionSealed):
        _require_matching_decision(
            state,
            event,
            SealPrediction(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                prediction=event.prediction,
            ),
        )
        return _advance_domain_state(
            state,
            predictions=(*state.predictions, event.prediction),
        )

    if isinstance(event, ProbeObservationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordProbeObservation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                observation=event.observation,
            ),
        )
        return _advance_domain_state(
            state,
            probe_observations=(*state.probe_observations, event.observation),
        )

    if isinstance(event, ReconstructionRecorded):
        _require_matching_decision(
            state,
            event,
            RecordReconstruction(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                reconstruction=event.reconstruction,
            ),
        )
        return _advance_domain_state(
            state,
            reconstructions=(*state.reconstructions, event.reconstruction),
        )

    if isinstance(event, MismatchRecorded):
        _require_matching_decision(
            state,
            event,
            RecordMismatch(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                mismatch=event.mismatch,
            ),
        )
        return _advance_domain_state(
            state,
            mismatches=(*state.mismatches, event.mismatch),
        )

    if isinstance(event, SemanticDeltaCommitted):
        _require_matching_decision(
            state,
            event,
            CommitSemanticDelta(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                delta=event.delta,
            ),
        )
        return _advance_domain_state(
            state,
            semantic_deltas=(*state.semantic_deltas, event.delta),
        )

    if isinstance(event, RetentionPackageRegistered):
        _require_matching_decision(
            state,
            event,
            RegisterRetentionPackage(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                registration=event.registration,
            ),
        )
        registration = event.registration
        return _advance_domain_state(
            state,
            direct_use_routes=(*state.direct_use_routes, *registration.direct_use_routes),
            reconstruction_routes=(
                *state.reconstruction_routes,
                *registration.reconstruction_routes,
            ),
            consequence_evaluation_routes=(
                *state.consequence_evaluation_routes,
                *registration.consequence_evaluation_routes,
            ),
            reacquisition_routes=(
                *state.reacquisition_routes,
                *registration.reacquisition_routes,
            ),
            reacquisition_scaffolds=(
                *state.reacquisition_scaffolds,
                *registration.scaffolds,
            ),
            recovery_protocols=(
                *state.recovery_protocols,
                *registration.recovery_protocols,
            ),
            retention_packages=(*state.retention_packages, registration.package),
        )

    if isinstance(event, RetrievalCompleted):
        _require_matching_decision(
            state,
            event,
            RunRetrieval(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                result_id=event.result.id,
                query=event.query,
            ),
        )
        return _advance_domain_state(
            state,
            retrieval_policies=(*state.retrieval_policies, event.policy),
            retrieval_queries=(*state.retrieval_queries, event.query),
            retrieval_results=(*state.retrieval_results, event.result),
        )

    if isinstance(event, ReacquisitionRequested):
        _require_matching_decision(
            state,
            event,
            RequestReacquisition(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                request=event.request,
            ),
        )
        return _advance_domain_state(
            state,
            reacquisition_requests=(*state.reacquisition_requests, event.request),
        )

    if isinstance(event, ReacquisitionInquiryLinked):
        _require_matching_decision(
            state,
            event,
            LinkReacquisitionInquiry(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                link=event.link,
            ),
        )
        return _advance_domain_state(
            state,
            reacquisition_inquiry_links=(*state.reacquisition_inquiry_links, event.link),
        )

    if isinstance(event, RecoveryObservationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRecoveryObservation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                observation=event.observation,
            ),
        )
        return _advance_domain_state(
            state,
            recovery_observations=(*state.recovery_observations, event.observation),
        )

    if isinstance(event, RecoveryComparisonRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRecoveryComparison(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                comparison=event.comparison,
            ),
        )
        return _advance_domain_state(
            state,
            recovery_comparisons=(*state.recovery_comparisons, event.comparison),
        )

    if isinstance(event, ConsolidationCheckpointRecorded):
        _require_matching_decision(
            state,
            event,
            RecordConsolidationCheckpoint(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                checkpoint=event.checkpoint,
            ),
        )
        return _advance_domain_state(
            state,
            consolidation_checkpoints=(*state.consolidation_checkpoints, event.checkpoint),
        )

    if isinstance(event, ConsolidationCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordConsolidationCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            consolidation_candidates=(*state.consolidation_candidates, event.candidate),
        )

    if isinstance(event, MemoryPatchCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordMemoryPatchCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            memory_patch_candidates=(*state.memory_patch_candidates, event.candidate),
        )

    if isinstance(event, ReconsolidationLinked):
        _require_matching_decision(
            state,
            event,
            RecordReconsolidationLink(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                link=event.link,
            ),
        )
        return _advance_domain_state(
            state,
            reconsolidation_links=(*state.reconsolidation_links, event.link),
        )

    if isinstance(event, SemanticFieldEvaluationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordSemanticFieldEvaluation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                evaluation=event.evaluation,
                overflow_residual=event.overflow_residual,
            ),
        )
        return _advance_domain_state(
            state,
            semantic_field_evaluations=(
                *state.semantic_field_evaluations,
                event.evaluation,
            ),
            residuals=(
                state.residuals
                if event.overflow_residual is None
                else (*state.residuals, event.overflow_residual)
            ),
        )

    if isinstance(event, RepresentationGapRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRepresentationGap(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                gap=event.gap,
            ),
        )
        return _advance_domain_state(
            state,
            representation_gaps=(*state.representation_gaps, event.gap),
        )

    if isinstance(event, LearnedProbeCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordLearnedProbeCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            learned_probe_candidates=(*state.learned_probe_candidates, event.candidate),
        )

    if isinstance(event, ProbeEvaluationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordProbeEvaluation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                evaluation=event.evaluation,
            ),
        )
        return _advance_domain_state(
            state,
            probe_evaluations=(*state.probe_evaluations, event.evaluation),
        )

    if isinstance(event, ProbeAdmissionDecisionRecorded):
        _require_matching_decision(
            state,
            event,
            RecordProbeAdmissionDecision(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        candidate = next(
            item
            for item in state.learned_probe_candidates
            if item.id == event.decision.candidate_probe_id
        )
        admitted = state.admitted_probes
        if event.decision.outcome is ProbeAdmissionOutcome.ADMIT:
            admitted = (*admitted, candidate.probe_identity)
        return _advance_domain_state(
            state,
            probe_admission_decisions=(*state.probe_admission_decisions, event.decision),
            admitted_probes=admitted,
        )

    if isinstance(event, BindingCarrierManifestRegistered):
        _require_matching_decision(
            state,
            event,
            RegisterBindingCarrierManifest(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                manifest=event.manifest,
            ),
        )
        return _advance_domain_state(
            state,
            binding_carrier_manifests=(*state.binding_carrier_manifests, event.manifest),
        )

    if isinstance(event, RealizedHistoryDerivationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRealizedHistoryDerivation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                derivation=event.derivation,
            ),
        )
        return _advance_domain_state(
            state,
            realized_history_derivations=(
                *state.realized_history_derivations,
                event.derivation,
            ),
        )

    if isinstance(event, CompressionContractRegistered):
        _require_matching_decision(
            state,
            event,
            RegisterCompressionContract(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                contract=event.contract,
            ),
        )
        return _advance_domain_state(
            state,
            compression_contracts=(*state.compression_contracts, event.contract),
        )

    if isinstance(event, CompressionValidationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCompressionValidation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                validation=event.validation,
            ),
        )
        return _advance_domain_state(
            state,
            compression_validations=(*state.compression_validations, event.validation),
        )

    if isinstance(event, ExactCompressionLicenseGranted):
        _require_matching_decision(
            state,
            event,
            GrantExactCompressionLicense(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                license=event.license,
            ),
        )
        return _advance_domain_state(
            state,
            exact_compression_licenses=(*state.exact_compression_licenses, event.license),
        )

    if isinstance(event, CompressionApplicationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCompressionApplication(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                application=event.application,
                path_residues=event.path_residues,
            ),
        )
        return _advance_domain_state(
            state,
            path_residues=(*state.path_residues, *event.path_residues),
            compression_applications=(*state.compression_applications, event.application),
        )

    if isinstance(event, RecoveryLicenseGranted):
        _require_matching_decision(
            state,
            event,
            GrantRecoveryLicense(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                license=event.license,
            ),
        )
        return _advance_domain_state(
            state,
            recovery_licenses=(*state.recovery_licenses, event.license),
        )

    if isinstance(event, RetentionCapabilityLinked):
        _require_matching_decision(
            state,
            event,
            LinkRetentionCapability(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                link=event.link,
            ),
        )
        return _advance_domain_state(
            state,
            retention_capability_links=(*state.retention_capability_links, event.link),
        )

    if isinstance(event, RepresentationSuccessorDecided):
        _require_matching_decision(
            state,
            event,
            DecideRepresentationSuccessor(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state,
            representation_successor_decisions=(
                *state.representation_successor_decisions,
                event.decision,
            ),
        )

    if isinstance(event, RepresentationReopened):
        _require_matching_decision(
            state,
            event,
            ReopenRepresentation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                reopening=event.reopening,
            ),
        )
        return _advance_domain_state(
            state,
            representation_reopenings=(*state.representation_reopenings, event.reopening),
        )

    if isinstance(event, ProjectAnchorRecorded):
        _require_matching_decision(
            state,
            event,
            RecordProjectAnchor(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                anchor=event.anchor,
            ),
        )
        return _advance_domain_state(state, project_anchors=(*state.project_anchors, event.anchor))

    if isinstance(event, CapabilityLimitationRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCapabilityLimitation(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                limitation=event.limitation,
            ),
        )
        return _advance_domain_state(
            state, capability_limitations=(*state.capability_limitations, event.limitation)
        )

    if isinstance(event, QuestionContractCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordQuestionContractCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            question_contract_candidates=(*state.question_contract_candidates, event.candidate),
        )

    if isinstance(event, QuestionRepertoireDecided):
        _require_matching_decision(
            state,
            event,
            DecideQuestionRepertoire(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state,
            question_repertoire_decisions=(*state.question_repertoire_decisions, event.decision),
        )

    if isinstance(event, MethodBindingCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordMethodBindingCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state, method_binding_candidates=(*state.method_binding_candidates, event.candidate)
        )

    if isinstance(event, MethodAdmissionDecided):
        _require_matching_decision(
            state,
            event,
            DecideMethodAdmission(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state, method_admission_decisions=(*state.method_admission_decisions, event.decision)
        )

    if isinstance(event, CapabilitySuccessorCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCapabilitySuccessorCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            capability_successor_candidates=(
                *state.capability_successor_candidates,
                event.candidate,
            ),
        )

    if isinstance(event, CapabilityFrontierRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCapabilityFrontier(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                frontier=event.frontier,
            ),
        )
        return _advance_domain_state(
            state, capability_frontiers=(*state.capability_frontiers, event.frontier)
        )

    if isinstance(event, ImplementationGoalCandidateRecorded):
        _require_matching_decision(
            state,
            event,
            RecordImplementationGoalCandidate(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                candidate=event.candidate,
            ),
        )
        return _advance_domain_state(
            state,
            implementation_goal_candidates=(
                *state.implementation_goal_candidates,
                event.candidate,
            ),
        )

    if isinstance(event, GoalAdmissionDecided):
        _require_matching_decision(
            state,
            event,
            DecideGoalAdmission(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state,
            goal_admission_decisions=(*state.goal_admission_decisions, event.decision),
        )

    if isinstance(event, ImplementationGoalSealed):
        _require_matching_decision(
            state,
            event,
            SealImplementationGoal(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                goal=event.goal,
            ),
        )
        return _advance_domain_state(
            state, implementation_goals=(*state.implementation_goals, event.goal)
        )

    if isinstance(event, CandidateEnvironmentRecorded):
        _require_matching_decision(
            state,
            event,
            RecordCandidateEnvironment(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                manifest=event.manifest,
            ),
        )
        return _advance_domain_state(
            state, candidate_environments=(*state.candidate_environments, event.manifest)
        )

    if isinstance(event, DevelopmentEvidenceRecorded):
        _require_matching_decision(
            state,
            event,
            RecordDevelopmentEvidence(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                evidence=event.evidence,
            ),
        )
        return _advance_domain_state(
            state, development_evidence=(*state.development_evidence, event.evidence)
        )

    if isinstance(event, IndependentReviewRecorded):
        _require_matching_decision(
            state,
            event,
            RecordIndependentReview(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                review=event.review,
            ),
        )
        return _advance_domain_state(
            state, independent_reviews=(*state.independent_reviews, event.review)
        )

    if isinstance(event, ProjectSuccessorDecided):
        _require_matching_decision(
            state,
            event,
            DecideProjectSuccessor(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state,
            project_successor_decisions=(*state.project_successor_decisions, event.decision),
        )

    if isinstance(event, PromotionDecisionRecorded):
        _require_matching_decision(
            state,
            event,
            RecordPromotionDecision(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                decision=event.decision,
            ),
        )
        return _advance_domain_state(
            state, promotion_decisions=(*state.promotion_decisions, event.decision)
        )

    if isinstance(event, RecursiveCycleCheckpointRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRecursiveCycleCheckpoint(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                checkpoint=event.checkpoint,
            ),
        )
        return _advance_domain_state(
            state,
            recursive_cycle_checkpoints=(*state.recursive_cycle_checkpoints, event.checkpoint),
        )

    if isinstance(event, RecursiveStopDispositionRecorded):
        _require_matching_decision(
            state,
            event,
            RecordRecursiveStopDisposition(
                event_id=event.event_id,
                inquiry_id=event.inquiry_id,
                occurred_at=event.occurred_at,
                disposition=event.disposition,
            ),
        )
        return _advance_domain_state(
            state,
            recursive_stop_dispositions=(
                *state.recursive_stop_dispositions,
                event.disposition,
            ),
        )

    raise InvalidTransitionError(f"unsupported event type: {type(event).__name__}")
