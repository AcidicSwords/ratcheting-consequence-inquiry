"""Deeply immutable aggregate state rebuilt exclusively from events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, Protocol

from pydantic import Field, model_validator

from rci.backlog.models import BacklogEffect
from rci.claims.models import (
    Candidate,
    Claim,
    Conflict,
    Correction,
    GuardChange,
    GuardStanding,
    Obligation,
    ObligationDisposition,
    ObligationStatus,
    Residual,
)
from rci.core.effects import EffectRequestState, ReturnedOutcome
from rci.core.model import ArtifactRef, FrozenModel, Identifier, InquiryContext
from rci.core.planning import PlanStatus, StepPlan
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
    ConsequenceEvaluationRoute,
    DirectUseRoute,
    MemoryOwner,
    OwnedRecordType,
    ReacquisitionInquiryLink,
    ReacquisitionRequest,
    ReacquisitionRoute,
    ReacquisitionScaffold,
    ReconstructionRoute,
    RecoveryComparison,
    RecoveryObservation,
    RecoveryProtocol,
    RetentionPackage,
    RetrievalQuery,
    RetrievalResult,
    StructuralRetrievalPolicy,
)
from rci.memory.recovery import (
    RecoveryCompatibilityError,
    compare_recovery_frontiers,
    derive_recovery_frontier,
)
from rci.memory.references import owned_record_content_fingerprint, resolve_owned_memory_ref
from rci.probes.models import (
    CognitiveAttemptPlan,
    Mismatch,
    PredictionSeal,
    ProbeEvent,
    ProbeIdentity,
    Reconstruction,
    SemanticDelta,
)
from rci.warrant.checks import checker_verdict_index, evidence_index, resolve_check_reference
from rci.warrant.models import (
    ActiveLemmaView,
    CheckerVerdictRecord,
    Evidence,
    LemmaSupport,
    LemmaVersion,
    Nogood,
    NogoodStandingChange,
    PromotionLink,
    PropositionKind,
    SupportRoute,
    SupportRouteStandingChange,
    SupportStanding,
    TheorySelector,
    WarrantClass,
    WarrantDecisionRecord,
    WarrantedLemma,
)
from rci.warrant.support import ancestry_is_acyclic, select_active_theory, support_graph_is_acyclic


class _PinnedRetentionRecord(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def scope_fingerprint(self) -> str: ...

    @property
    def binding_revision(self) -> str: ...

    @property
    def protected_horizon_id(self) -> str: ...


class InquiryState(FrozenModel):
    status: Literal["not_started", "active"] = "not_started"
    inquiry_id: Identifier | None = None
    sequence: int = Field(default=0, ge=0)
    manifest_artifact: ArtifactRef | None = None
    policy_version: Identifier | None = None
    context: InquiryContext | None = None
    backlog_effects: tuple[BacklogEffect, ...] = ()
    step_plans: tuple[StepPlan, ...] = ()
    effect_requests: tuple[EffectRequestState, ...] = ()
    claims: tuple[Claim, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    obligations: tuple[Obligation, ...] = ()
    obligation_dispositions: tuple[ObligationDisposition, ...] = ()
    candidates: tuple[Candidate, ...] = ()
    residuals: tuple[Residual, ...] = ()
    corrections: tuple[Correction, ...] = ()
    guard_changes: tuple[GuardChange, ...] = ()
    nogoods: tuple[Nogood, ...] = ()
    support_route_standing_changes: tuple[SupportRouteStandingChange, ...] = ()
    nogood_standing_changes: tuple[NogoodStandingChange, ...] = ()
    evidence_records: tuple[Evidence, ...] = ()
    checker_verdicts: tuple[CheckerVerdictRecord, ...] = ()
    warrant_decisions: tuple[WarrantDecisionRecord, ...] = ()
    lemma_versions: tuple[LemmaVersion, ...] = ()
    lemma_supports: tuple[LemmaSupport, ...] = ()
    promotion_links: tuple[PromotionLink, ...] = ()
    admitted_probes: tuple[ProbeIdentity, ...] = ()
    cognitive_plans: tuple[CognitiveAttemptPlan, ...] = ()
    predictions: tuple[PredictionSeal, ...] = ()
    probe_observations: tuple[ProbeEvent, ...] = ()
    reconstructions: tuple[Reconstruction, ...] = ()
    mismatches: tuple[Mismatch, ...] = ()
    semantic_deltas: tuple[SemanticDelta, ...] = ()
    direct_use_routes: tuple[DirectUseRoute, ...] = ()
    reconstruction_routes: tuple[ReconstructionRoute, ...] = ()
    consequence_evaluation_routes: tuple[ConsequenceEvaluationRoute, ...] = ()
    reacquisition_routes: tuple[ReacquisitionRoute, ...] = ()
    reacquisition_scaffolds: tuple[ReacquisitionScaffold, ...] = ()
    recovery_protocols: tuple[RecoveryProtocol, ...] = ()
    retention_packages: tuple[RetentionPackage, ...] = ()
    retrieval_policies: tuple[StructuralRetrievalPolicy, ...] = ()
    retrieval_queries: tuple[RetrievalQuery, ...] = ()
    retrieval_results: tuple[RetrievalResult, ...] = ()
    reacquisition_requests: tuple[ReacquisitionRequest, ...] = ()
    reacquisition_inquiry_links: tuple[ReacquisitionInquiryLink, ...] = ()
    recovery_observations: tuple[RecoveryObservation, ...] = ()
    recovery_comparisons: tuple[RecoveryComparison, ...] = ()
    consolidation_checkpoints: tuple[ConsolidationCheckpoint, ...] = ()
    consolidation_candidates: tuple[ConsolidationCandidate, ...] = ()
    memory_patch_candidates: tuple[MemoryPatchCandidate, ...] = ()
    reconsolidation_links: tuple[ReconsolidationLink, ...] = ()
    semantic_field_evaluations: tuple[SemanticFieldEvaluation, ...] = ()
    representation_gaps: tuple[RepresentationGap, ...] = ()
    learned_probe_candidates: tuple[LearnedProbeCandidate, ...] = ()
    probe_evaluations: tuple[ProbeEvaluation, ...] = ()
    probe_admission_decisions: tuple[ProbeAdmissionDecision, ...] = ()

    @property
    def owned_memory_records(self) -> Mapping[str, object]:
        """Return the exact typed aggregate records addressable by G2A packages."""

        records: dict[str, object] = {}

        def add(
            owner: MemoryOwner,
            record_type: OwnedRecordType,
            record_id: str,
            record: object,
        ) -> None:
            schema_version = int(getattr(record, "schema_version", 1))
            key = f"{owner.value}:{record_type.value}:{record_id}:v{schema_version}"
            prior = records.get(key)
            if prior is not None and prior != record:
                raise ValueError("owned memory record key has conflicting immutable contents")
            records[key] = record

        for episodic_record in self.probe_observations:
            add(
                MemoryOwner.EPISODIC,
                OwnedRecordType.PROBE_EVENT,
                episodic_record.id,
                episodic_record,
            )
        for semantic_version in self.lemma_versions:
            add(
                MemoryOwner.SEMANTIC,
                OwnedRecordType.LEMMA_VERSION,
                semantic_version.id,
                semantic_version,
            )
        for delta_record in self.semantic_deltas:
            add(
                MemoryOwner.SEMANTIC,
                OwnedRecordType.SEMANTIC_DELTA,
                delta_record.id,
                delta_record,
            )
        for procedural_probe in self.admitted_probes:
            add(
                MemoryOwner.PROCEDURAL,
                OwnedRecordType.PROBE_IDENTITY,
                procedural_probe.fingerprint,
                procedural_probe,
            )
        for package_record in self.retention_packages:
            add(
                MemoryOwner.RETENTION,
                OwnedRecordType.RETENTION_PACKAGE,
                package_record.id,
                package_record,
            )
        for scaffold_record in self.reacquisition_scaffolds:
            add(
                MemoryOwner.RETENTION,
                OwnedRecordType.REACQUISITION_SCAFFOLD,
                scaffold_record.id,
                scaffold_record,
            )
        for protocol_record in self.recovery_protocols:
            add(
                MemoryOwner.RETENTION,
                OwnedRecordType.RECOVERY_PROTOCOL,
                protocol_record.id,
                protocol_record,
            )
        for evidence_record in self.evidence_records:
            add(
                MemoryOwner.WARRANT,
                OwnedRecordType.EVIDENCE,
                evidence_record.id,
                evidence_record,
            )
        for checker_record in self.checker_verdicts:
            add(
                MemoryOwner.WARRANT,
                OwnedRecordType.CHECKER_VERDICT,
                checker_record.id,
                checker_record,
            )
        for warrant_record in self.warrant_decisions:
            add(
                MemoryOwner.WARRANT,
                OwnedRecordType.WARRANT_DECISION,
                warrant_record.id,
                warrant_record,
            )
        for request_state in self.effect_requests:
            add(
                MemoryOwner.ACTION,
                OwnedRecordType.EFFECT_REQUEST,
                request_state.request.id,
                request_state.request,
            )
            for attempt in request_state.attempts:
                if isinstance(attempt.outcome, ReturnedOutcome):
                    returned = attempt.outcome.external_return
                    add(
                        MemoryOwner.ACTION,
                        OwnedRecordType.EXTERNAL_RETURN,
                        returned.id,
                        returned,
                    )
        for reconstruction_record in self.reconstructions:
            add(
                MemoryOwner.ACTION,
                OwnedRecordType.RECONSTRUCTION,
                reconstruction_record.id,
                reconstruction_record,
            )
        for prediction_record in self.predictions:
            add(
                MemoryOwner.PREDICTION,
                OwnedRecordType.PREDICTION_SEAL,
                prediction_record.id,
                prediction_record,
            )
        return records

    @property
    def owned_memory_fingerprints(self) -> Mapping[str, str]:
        """Return canonical fingerprints for the exact current structural index."""

        fingerprints: dict[str, str] = {}
        for key, record in self.owned_memory_records.items():
            owner_value, record_type_value, identity_and_version = key.split(":", 2)
            _record_id, version_value = identity_and_version.rsplit(":v", 1)
            owner = MemoryOwner(owner_value)
            record_type = OwnedRecordType(record_type_value)
            version = int(version_value)
            fingerprints[key] = owned_record_content_fingerprint(
                owner=owner,
                record_type=record_type,
                record_schema_version=version,
                record=record,
            )
        return fingerprints

    @model_validator(mode="after")
    def validate_lifecycle(self) -> InquiryState:
        started_fields = (
            self.inquiry_id,
            self.manifest_artifact,
            self.policy_version,
            self.context,
        )
        if self.status == "not_started":
            if self.sequence != 0 or any(value is not None for value in started_fields):
                raise ValueError("an unstarted inquiry cannot contain started state")
            if self.backlog_effects or self.step_plans or self.effect_requests:
                raise ValueError(
                    "an unstarted inquiry cannot contain backlog effects, plans, or requests"
                )
            if any(
                (
                    self.claims,
                    self.conflicts,
                    self.obligations,
                    self.obligation_dispositions,
                    self.candidates,
                    self.residuals,
                    self.corrections,
                    self.guard_changes,
                    self.nogoods,
                    self.support_route_standing_changes,
                    self.nogood_standing_changes,
                    self.evidence_records,
                    self.checker_verdicts,
                    self.warrant_decisions,
                    self.lemma_versions,
                    self.lemma_supports,
                    self.promotion_links,
                    self.admitted_probes,
                    self.cognitive_plans,
                    self.predictions,
                    self.probe_observations,
                    self.reconstructions,
                    self.mismatches,
                    self.semantic_deltas,
                    self.direct_use_routes,
                    self.reconstruction_routes,
                    self.consequence_evaluation_routes,
                    self.reacquisition_routes,
                    self.reacquisition_scaffolds,
                    self.recovery_protocols,
                    self.retention_packages,
                    self.retrieval_policies,
                    self.retrieval_queries,
                    self.retrieval_results,
                    self.reacquisition_requests,
                    self.reacquisition_inquiry_links,
                    self.recovery_observations,
                    self.recovery_comparisons,
                    self.consolidation_checkpoints,
                    self.consolidation_candidates,
                    self.memory_patch_candidates,
                    self.reconsolidation_links,
                    self.semantic_field_evaluations,
                    self.representation_gaps,
                    self.learned_probe_candidates,
                    self.probe_evaluations,
                    self.probe_admission_decisions,
                )
            ):
                raise ValueError("an unstarted inquiry cannot contain domain records")
        elif any(value is None for value in started_fields):
            raise ValueError("an active inquiry requires identity, manifest, and policy")

        request_ids = [item.request.id for item in self.effect_requests]
        if len(request_ids) != len(set(request_ids)):
            raise ValueError("effect request ids must be unique")

        backlog_effect_ids = [effect.id for effect in self.backlog_effects]
        if len(backlog_effect_ids) != len(set(backlog_effect_ids)):
            raise ValueError("backlog effect ids must be unique")

        step_plan_ids = [plan.id for plan in self.step_plans]
        if len(step_plan_ids) != len(set(step_plan_ids)):
            raise ValueError("step plan ids must be unique")
        step_plan_by_id = {plan.id: plan for plan in self.step_plans}
        if any(
            request.request.step_plan_id not in step_plan_by_id for request in self.effect_requests
        ):
            raise ValueError("effect requests must reference owned step plans")

        global_attempt_ids = [
            attempt.plan.id for request in self.effect_requests for attempt in request.attempts
        ]
        if len(global_attempt_ids) != len(set(global_attempt_ids)):
            raise ValueError("attempt ids must be unique within an inquiry")

        external_return_ids = [
            attempt.outcome.external_return.id
            for request in self.effect_requests
            for attempt in request.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        ]
        if len(external_return_ids) != len(set(external_return_ids)):
            raise ValueError("external return ids must be unique within an inquiry")

        decode_ids = [
            outcome.id for request in self.effect_requests for outcome in request.decode_outcomes
        ]
        if len(decode_ids) != len(set(decode_ids)):
            raise ValueError("decode outcome ids must be unique within an inquiry")

        result_ids = [
            request.accepted_result.id
            for request in self.effect_requests
            if request.accepted_result is not None
        ]
        if len(result_ids) != len(set(result_ids)):
            raise ValueError("accepted result ids must be unique within an inquiry")

        identified_collections = (
            tuple(item.id for item in self.claims),
            tuple(item.id for item in self.conflicts),
            tuple(item.id for item in self.obligations),
            tuple(item.id for item in self.obligation_dispositions),
            tuple(item.id for item in self.candidates),
            tuple(item.id for item in self.residuals),
            tuple(item.id for item in self.corrections),
            tuple(item.id for item in self.guard_changes),
            tuple(item.id for item in self.nogoods),
            tuple(item.id for item in self.support_route_standing_changes),
            tuple(item.id for item in self.nogood_standing_changes),
            tuple(item.id for item in self.evidence_records),
            tuple(item.id for item in self.checker_verdicts),
            tuple(item.id for item in self.warrant_decisions),
            tuple(item.id for item in self.lemma_versions),
            tuple(item.id for item in self.promotion_links),
            tuple(item.id for item in self.cognitive_plans),
            tuple(item.id for item in self.predictions),
            tuple(item.id for item in self.probe_observations),
            tuple(item.id for item in self.reconstructions),
            tuple(item.id for item in self.mismatches),
            tuple(item.id for item in self.semantic_deltas),
            tuple(item.id for item in self.direct_use_routes),
            tuple(item.id for item in self.reconstruction_routes),
            tuple(item.id for item in self.consequence_evaluation_routes),
            tuple(item.id for item in self.reacquisition_routes),
            tuple(item.id for item in self.reacquisition_scaffolds),
            tuple(item.id for item in self.recovery_protocols),
            tuple(item.id for item in self.retention_packages),
            tuple(f"{item.id}:{item.version}" for item in self.retrieval_policies),
            tuple(item.id for item in self.retrieval_queries),
            tuple(item.id for item in self.retrieval_results),
            tuple(item.id for item in self.reacquisition_requests),
            tuple(item.id for item in self.reacquisition_inquiry_links),
            tuple(item.id for item in self.recovery_observations),
            tuple(item.id for item in self.recovery_comparisons),
            tuple(item.id for item in self.consolidation_checkpoints),
            tuple(item.id for item in self.consolidation_candidates),
            tuple(item.id for item in self.memory_patch_candidates),
            tuple(item.id for item in self.reconsolidation_links),
            tuple(item.id for item in self.semantic_field_evaluations),
            tuple(item.id for item in self.representation_gaps),
            tuple(item.id for item in self.learned_probe_candidates),
            tuple(item.id for item in self.probe_evaluations),
            tuple(item.id for item in self.probe_admission_decisions),
        )
        for identifiers in identified_collections:
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("domain record identities must be unique per owner")
        probe_fingerprints = [probe.fingerprint for probe in self.admitted_probes]
        if len(probe_fingerprints) != len(set(probe_fingerprints)):
            raise ValueError("admitted recurrent probe identities must be unique")

        checkpoint_ids = {item.id for item in self.consolidation_checkpoints}
        claim_ids_for_learning = {item.id for item in self.claims}
        obligation_ids_for_learning = {item.id for item in self.obligations}
        for candidate in self.consolidation_candidates:
            if (
                candidate.checkpoint_id not in checkpoint_ids
                or candidate.generalization_claim_id not in claim_ids_for_learning
                or not set(
                    (
                        *candidate.challenge_obligation_ids,
                        *candidate.boundary.open_dependency_obligation_ids,
                    )
                )
                <= obligation_ids_for_learning
            ):
                raise ValueError("consolidation candidates require owned source records")
        mismatch_ids = {item.id for item in self.mismatches}
        captured_return_ids = self.captured_external_return_ids
        lemma_ids_for_learning = {item.id for item in self.lemma_versions}
        route_ids_for_learning = {
            route.id for support in self.lemma_supports for route in support.all_support_routes
        }
        for patch in self.memory_patch_candidates:
            if (
                patch.target_lemma_id not in lemma_ids_for_learning
                or patch.triggering_mismatch_id not in mismatch_ids
                or patch.triggering_return_id not in captured_return_ids
                or patch.proposed_claim_id not in claim_ids_for_learning
                or not set(patch.predecessor_support_route_ids) <= route_ids_for_learning
                or not set(patch.challenge_obligation_ids) <= obligation_ids_for_learning
            ):
                raise ValueError("memory patches require owned immutable predecessors")
        patch_ids = {item.id for item in self.memory_patch_candidates}
        correction_ids = {item.id for item in self.corrections}
        warrant_ids_for_learning = {item.id for item in self.warrant_decisions}
        for reconsolidation_link in self.reconsolidation_links:
            if (
                reconsolidation_link.memory_patch_id not in patch_ids
                or reconsolidation_link.predecessor_lemma_id not in lemma_ids_for_learning
                or reconsolidation_link.successor_lemma_id not in lemma_ids_for_learning
                or reconsolidation_link.correction_id not in correction_ids
                or reconsolidation_link.warrant_decision_id not in warrant_ids_for_learning
            ):
                raise ValueError("reconsolidation links require owned succession evidence")
        gap_ids = {item.id for item in self.representation_gaps}
        for gap in self.representation_gaps:
            if gap.obligation_id not in obligation_ids_for_learning:
                raise ValueError("representation gaps require an owned obligation")
        candidate_probe_ids = {item.id for item in self.learned_probe_candidates}
        for learned_candidate in self.learned_probe_candidates:
            if (
                learned_candidate.representation_gap_id not in gap_ids
                or not set(learned_candidate.challenge_obligation_ids)
                <= obligation_ids_for_learning
            ):
                raise ValueError("learned-probe candidates require owned gaps and attacks")
        evaluation_ids = {item.id for item in self.probe_evaluations}
        observation_ids_for_learning = {item.id for item in self.probe_observations}
        for evaluation in self.probe_evaluations:
            if (
                evaluation.candidate_probe_id not in candidate_probe_ids
                or not {
                    *evaluation.training_observation_ids,
                    *evaluation.holdout_observation_ids,
                }
                <= observation_ids_for_learning
            ):
                raise ValueError("probe evaluations require owned candidates and observations")
        for admission_decision in self.probe_admission_decisions:
            if (
                admission_decision.candidate_probe_id not in candidate_probe_ids
                or admission_decision.evaluation_id not in evaluation_ids
            ):
                raise ValueError("probe admission decisions require owned evaluations")

        claim_ids = {claim.id for claim in self.claims}
        if any(not set(conflict.claim_ids) <= claim_ids for conflict in self.conflicts):
            raise ValueError("conflicts must reference recorded claims")
        obligation_ids = {obligation.id for obligation in self.obligations}
        if any(
            disposition.obligation_id not in obligation_ids
            for disposition in self.obligation_dispositions
        ):
            raise ValueError("obligation dispositions must reference recorded obligations")
        obligation_by_id = {obligation.id: obligation for obligation in self.obligations}
        for plan in self.step_plans:
            if self.context is None or plan.policy_version != self.context.scheduler_policy_version:
                raise ValueError("step plan policy must match the inquiry context")
            if plan.status is not PlanStatus.READY:
                continue
            obligation = obligation_by_id.get(plan.selected_obligation_id or "")
            if obligation is None or plan.selected_attempt_key is None:
                raise ValueError("ready step plans must select an owned obligation")
            if (
                plan.selected_attempt_key.obligation_fingerprint != obligation.fingerprint
                or plan.selected_attempt_key.binding_revision != obligation.binding_revision
            ):
                raise ValueError("step plan attempt key must match its exact obligation")

        version_ids = {version.id for version in self.lemma_versions}
        support_id_sequence = tuple(support.lemma_version_id for support in self.lemma_supports)
        if len(support_id_sequence) != len(set(support_id_sequence)):
            raise ValueError("a lemma version can have only one authoritative support owner")
        support_ids = set(support_id_sequence)
        link_ids = {link.lemma_version_id for link in self.promotion_links}
        if version_ids != support_ids or version_ids != link_ids:
            raise ValueError("semantic versions, warrant support, and promotion links must align")
        route_ids = tuple(
            route.id for support in self.lemma_supports for route in support.all_support_routes
        )
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("support-route identities must be unique within an inquiry")
        warranted_lemmas = self.warranted_lemmas
        if not support_graph_is_acyclic(warranted_lemmas):
            raise ValueError("active positive support topology must remain acyclic")
        if not ancestry_is_acyclic(
            {version.id: version.predecessor_refs for version in self.lemma_versions}
        ):
            raise ValueError("semantic version ancestry must remain owned and acyclic")
        decision_ids = {decision.id for decision in self.warrant_decisions}
        evidence_by_id = {evidence.id: evidence for evidence in self.evidence_records}
        checker_by_id = {verdict.id: verdict for verdict in self.checker_verdicts}
        for verdict in self.checker_verdicts:
            evidence = evidence_by_id.get(verdict.evidence_id)
            if evidence is None:
                raise ValueError("checker verdicts must reference owned evidence")
            if (
                verdict.evidence_artifact != evidence.artifact
                or verdict.proposition_id != evidence.proposition_id
                or verdict.proposition_kind is not evidence.proposition_kind
                or verdict.scope_fingerprint != evidence.scope_fingerprint
            ):
                raise ValueError("checker verdict pins must match their exact evidence record")
        for decision in self.warrant_decisions:
            evidence = evidence_by_id.get(decision.evidence_id)
            decision_verdict = checker_by_id.get(decision.checker_verdict_id)
            if evidence is None or decision_verdict is None:
                raise ValueError("warrant decisions must reference owned evidence and checks")
            if (
                decision_verdict.evidence_id != evidence.id
                or decision.proposition_id != evidence.proposition_id
                or decision.proposition_kind is not evidence.proposition_kind
                or decision.scope_fingerprint != evidence.scope_fingerprint
                or decision_verdict.proposition_id != decision.proposition_id
                or decision_verdict.proposition_kind is not decision.proposition_kind
                or decision_verdict.scope_fingerprint != decision.scope_fingerprint
            ):
                raise ValueError("warrant decision pins must match its evidence and checker record")
        for support in self.lemma_supports:
            for route in support.all_support_routes:
                for reference in (
                    route.certificate_check,
                    route.environment.realizability_check,
                ):
                    support_verdict = checker_by_id.get(reference.checker_verdict_id)
                    if (
                        evidence_by_id.get(reference.evidence_id) is None
                        or support_verdict is None
                        or support_verdict.evidence_id != reference.evidence_id
                    ):
                        raise ValueError(
                            "support checks must reference owned evidence and verdicts"
                        )
        if any(link.warrant_decision_id not in decision_ids for link in self.promotion_links):
            raise ValueError("promotion links must reference owned warrant decisions")
        if any(not set(link.source_claim_ids) <= claim_ids for link in self.promotion_links):
            raise ValueError("promotion links must preserve recorded source claims")
        support_by_lemma_id = {support.lemma_version_id: support for support in self.lemma_supports}
        decision_by_id = {decision.id: decision for decision in self.warrant_decisions}
        for link in self.promotion_links:
            support = support_by_lemma_id[link.lemma_version_id]
            promotion_decision = decision_by_id[link.warrant_decision_id]
            if support.policy_version != promotion_decision.policy_version:
                raise ValueError("lemma support policy must match its exact warrant decision")

        route_id_set = set(route_ids)
        route_tail: dict[str, SupportRouteStandingChange] = {}
        route_standing: dict[str, SupportStanding] = {}
        for route_change in self.support_route_standing_changes:
            if route_change.support_route_id not in route_id_set:
                raise ValueError("support-route standing changes must reference an owned route")
            route_history_tail = route_tail.get(route_change.support_route_id)
            if route_change.predecessor_id != (
                route_history_tail.id if route_history_tail is not None else None
            ):
                raise ValueError("support-route standing history must extend its exact tail")
            prior_route_standing = route_standing.get(
                route_change.support_route_id, SupportStanding.STANDING
            )
            if route_change.standing is prior_route_standing:
                raise ValueError("support-route standing histories must change standing")
            route_tail[route_change.support_route_id] = route_change
            route_standing[route_change.support_route_id] = route_change.standing

        nogood_ids = {nogood.id for nogood in self.nogoods}
        nogood_tail: dict[str, NogoodStandingChange] = {}
        nogood_standing: dict[str, SupportStanding] = {}
        for nogood_change in self.nogood_standing_changes:
            if nogood_change.nogood_id not in nogood_ids:
                raise ValueError("nogood standing changes must reference an owned nogood")
            nogood_history_tail = nogood_tail.get(nogood_change.nogood_id)
            if nogood_change.predecessor_id != (
                nogood_history_tail.id if nogood_history_tail is not None else None
            ):
                raise ValueError("nogood standing history must extend its exact tail")
            prior_nogood_standing = nogood_standing.get(
                nogood_change.nogood_id, SupportStanding.STANDING
            )
            if nogood_change.standing is prior_nogood_standing:
                raise ValueError("nogood standing histories must change standing")
            nogood_tail[nogood_change.nogood_id] = nogood_change
            nogood_standing[nogood_change.nogood_id] = nogood_change.standing

        for nogood in self.nogoods:
            nogood_decision = decision_by_id.get(nogood.warrant_decision_id)
            nogood_evidence = evidence_by_id.get(nogood.check.evidence_id)
            nogood_verdict = checker_by_id.get(nogood.check.checker_verdict_id)
            if (
                nogood_evidence is None
                or nogood_verdict is None
                or nogood_verdict.evidence_id != nogood_evidence.id
            ):
                raise ValueError("nogoods must reference owned evidence and checker verdicts")
            if (
                nogood_decision is None
                or nogood_decision.warrant_class is not WarrantClass.HARD
                or nogood_decision.id != nogood.warrant_decision_id
                or nogood_decision.evidence_id != nogood_evidence.id
                or nogood_decision.checker_verdict_id != nogood_verdict.id
                or nogood_decision.proposition_id != nogood.id
                or nogood_decision.proposition_kind is not PropositionKind.EXISTENTIAL
                or nogood_decision.scope_fingerprint != nogood.scope_fingerprint
                or nogood_decision.policy_version != nogood.policy_version
            ):
                raise ValueError("nogoods require an exact owned hard warrant decision")
            if self.context is None or (
                nogood.scope_fingerprint != self.context.scope_fingerprint
                or nogood.binding_revision != self.context.binding_revision
                or nogood.finite_universe_hash != self.context.finite_universe_hash
                or nogood.policy_version != self.context.warrant_policy_version
            ):
                raise ValueError("nogoods must match the inquiry's exact support class")

        reconstruction_ids = {item.id for item in self.reconstructions}
        lemma_ids = version_ids
        for delta in self.semantic_deltas:
            if delta.reconstruction_id not in reconstruction_ids:
                raise ValueError("semantic deltas must reference an owned reconstruction")
            if any(change.warrant_lemma_id not in lemma_ids for change in delta.warranted_changes):
                raise ValueError("semantic changes must reference owned warranted lemmas")

        owned_records = self.owned_memory_records
        for memory_package in self.retention_packages:
            for owned_reference in memory_package.owned_refs:
                resolved, reason = resolve_owned_memory_ref(
                    owned_reference,
                    owned_records=owned_records,
                )
                if not resolved:
                    raise ValueError(f"retention package has an invalid owned reference: {reason}")

        registration_groups: tuple[
            tuple[tuple[_PinnedRetentionRecord, ...], tuple[str, ...], str], ...
        ] = (
            (
                self.direct_use_routes,
                tuple(
                    route_id
                    for package in self.retention_packages
                    for route_id in package.direct_use_route_ids
                ),
                "direct-use routes",
            ),
            (
                self.reconstruction_routes,
                tuple(
                    route_id
                    for package in self.retention_packages
                    for route_id in package.reconstruction_route_ids
                ),
                "reconstruction routes",
            ),
            (
                self.consequence_evaluation_routes,
                tuple(
                    route_id
                    for package in self.retention_packages
                    for route_id in package.consequence_evaluation_route_ids
                ),
                "consequence-evaluation routes",
            ),
            (
                self.reacquisition_routes,
                tuple(
                    route_id
                    for package in self.retention_packages
                    for route_id in package.reacquisition_route_ids
                ),
                "reacquisition routes",
            ),
            (
                self.reacquisition_scaffolds,
                tuple(
                    scaffold_id
                    for package in self.retention_packages
                    for scaffold_id in package.scaffold_ids
                ),
                "reacquisition scaffolds",
            ),
            (
                self.recovery_protocols,
                tuple(
                    protocol_id
                    for package in self.retention_packages
                    for protocol_id in package.recovery_protocol_ids
                ),
                "recovery protocols",
            ),
        )
        for registered_records, referenced_ids, label in registration_groups:
            if len(referenced_ids) != len(set(referenced_ids)):
                raise ValueError(f"registered {label} cannot be owned by multiple packages")
            actual_ids = {str(registered_record.id) for registered_record in registered_records}
            if actual_ids != set(referenced_ids):
                raise ValueError(f"registered {label} must be owned by a retention package")

        package_by_id = {package.id: package for package in self.retention_packages}
        scaffold_by_id = {scaffold.id: scaffold for scaffold in self.reacquisition_scaffolds}
        protocol_by_id = {protocol.id: protocol for protocol in self.recovery_protocols}
        for pinned_package in self.retention_packages:
            package_pins = (
                pinned_package.scope_fingerprint,
                pinned_package.binding_revision,
                pinned_package.protected_horizon_id,
            )
            pinned_records: tuple[_PinnedRetentionRecord, ...] = (
                *(
                    item
                    for item in self.direct_use_routes
                    if item.id in pinned_package.direct_use_route_ids
                ),
                *(
                    item
                    for item in self.reconstruction_routes
                    if item.id in pinned_package.reconstruction_route_ids
                ),
                *(
                    item
                    for item in self.consequence_evaluation_routes
                    if item.id in pinned_package.consequence_evaluation_route_ids
                ),
                *(
                    item
                    for item in self.reacquisition_routes
                    if item.id in pinned_package.reacquisition_route_ids
                ),
                *(
                    item
                    for item in self.reacquisition_scaffolds
                    if item.id in pinned_package.scaffold_ids
                ),
                *(
                    item
                    for item in self.recovery_protocols
                    if item.id in pinned_package.recovery_protocol_ids
                ),
            )
            for package_record in pinned_records:
                if (
                    package_record.scope_fingerprint,
                    package_record.binding_revision,
                    package_record.protected_horizon_id,
                ) != package_pins:
                    raise ValueError("retention package records must preserve exact package pins")

        policy_by_key = {(policy.id, policy.version): policy for policy in self.retrieval_policies}
        query_by_id = {query.id: query for query in self.retrieval_queries}
        if {result.query_id for result in self.retrieval_results} != set(query_by_id):
            raise ValueError("each retrieval query must have exactly one persisted result")
        if len(self.retrieval_results) != len(self.retrieval_queries):
            raise ValueError("retrieval query/result cardinality must remain one-to-one")
        for result in self.retrieval_results:
            query = query_by_id[result.query_id]
            if (
                result.policy_id,
                result.policy_version,
                result.source_sequence,
                result.source_index_fingerprint,
            ) != (
                query.policy_id,
                query.policy_version,
                query.source_sequence,
                query.source_index_fingerprint,
            ):
                raise ValueError("retrieval result must preserve its exact query source pins")
            if (query.policy_id, query.policy_version) not in policy_by_key:
                raise ValueError("retrieval query must preserve its resolved policy snapshot")
            if query.source_sequence >= self.sequence:
                raise ValueError("retrieval query source must precede its completion event")
            for hit in result.hits:
                hit_package = package_by_id.get(hit.package_id)
                if (
                    hit_package is None
                    or hit_package.fingerprint != hit.package_content_fingerprint
                ):
                    raise ValueError("retrieval hit must pin an owned retention package version")
        used_policy_keys = {
            (query.policy_id, query.policy_version) for query in self.retrieval_queries
        }
        if used_policy_keys != set(policy_by_key):
            raise ValueError("folded retrieval policies must be exact snapshots used by queries")

        request_by_id = {request.id: request for request in self.reacquisition_requests}
        child_ids = tuple(request.child_inquiry_id for request in self.reacquisition_requests)
        if len(child_ids) != len(set(child_ids)):
            raise ValueError("each reacquisition request must own a distinct child inquiry")
        if self.context is not None:
            for recovery_request in self.reacquisition_requests:
                if recovery_request.parent_inquiry_id != self.inquiry_id:
                    raise ValueError("reacquisition request parent must be this inquiry")
                if (
                    recovery_request.pins.scope_fingerprint,
                    recovery_request.pins.binding_revision,
                    recovery_request.pins.protected_horizon_id,
                    recovery_request.pins.finite_universe_hash,
                ) != (
                    self.context.scope_fingerprint,
                    self.context.binding_revision,
                    self.context.protected_horizon_id,
                    self.context.finite_universe_hash,
                ):
                    raise ValueError("reacquisition request pins must match its parent context")
                request_protocol = protocol_by_id.get(recovery_request.pins.recovery_protocol_id)
                if (
                    request_protocol is None
                    or request_protocol.version != recovery_request.pins.recovery_protocol_version
                ):
                    raise ValueError("reacquisition request requires an owned protocol version")
                if request_protocol.pins != recovery_request.pins:
                    raise ValueError("reacquisition request pins must equal its recovery protocol")
                if recovery_request.retention_package_id is not None:
                    request_package = package_by_id.get(recovery_request.retention_package_id)
                    request_scaffold = scaffold_by_id.get(recovery_request.scaffold_id or "")
                    if (
                        request_package is None
                        or request_scaffold is None
                        or request_scaffold.id not in request_package.scaffold_ids
                        or request_protocol.id not in request_package.recovery_protocol_ids
                        or not any(
                            route.id in request_package.reacquisition_route_ids
                            and route.recovery_protocol_id == request_protocol.id
                            and route.reacquisition_scaffold_id == request_scaffold.id
                            for route in self.reacquisition_routes
                        )
                    ):
                        raise ValueError(
                            "retained reacquisition must use one package-owned scaffold/protocol"
                        )

        links_by_request: dict[str, ReacquisitionInquiryLink] = {}
        for recovery_link in self.reacquisition_inquiry_links:
            linked_request = request_by_id.get(recovery_link.request_id)
            if linked_request is None:
                raise ValueError("reacquisition link must reference an owned request")
            if recovery_link.request_id in links_by_request:
                raise ValueError("a reacquisition request can link only one child inquiry")
            if (
                recovery_link.parent_inquiry_id,
                recovery_link.child_inquiry_id,
                recovery_link.child_manifest_artifact,
                recovery_link.child_context_digest,
            ) != (
                linked_request.parent_inquiry_id,
                linked_request.child_inquiry_id,
                linked_request.child_manifest_artifact,
                linked_request.child_context_digest,
            ):
                raise ValueError("reacquisition link must preserve its exact request pins")
            links_by_request[recovery_link.request_id] = recovery_link

        evidence_lookup = evidence_index(self.evidence_records)
        checker_lookup = checker_verdict_index(self.checker_verdicts)

        def require_independent_check(
            reference: object,
            *,
            proposition_id: str,
            scope_fingerprint: str,
        ) -> None:
            if self.context is None:
                raise ValueError("independent checks require an inquiry context")
            checked, reason = resolve_check_reference(
                reference,  # type: ignore[arg-type]
                evidence_by_id=evidence_lookup,
                checker_verdict_by_id=checker_lookup,
                proposition_id=proposition_id,
                proposition_kind=PropositionKind.RELATION,
                scope_fingerprint=scope_fingerprint,
                authorized_checker_ids=self.context.discharge_mechanism_ids,
            )
            if not checked:
                raise ValueError(f"G2A record requires an independent valid check: {reason}")

        observation_by_id = {item.id: item for item in self.recovery_observations}
        observed_request_ids: set[str] = set()
        for observation in self.recovery_observations:
            observed_request = request_by_id.get(observation.reacquisition_request_id)
            observed_link = links_by_request.get(observation.reacquisition_request_id)
            if observed_request is None or observed_link is None:
                raise ValueError("recovery observation requires a linked reacquisition child")
            if observation.reacquisition_request_id in observed_request_ids:
                raise ValueError("a reacquisition request can yield only one observation")
            observed_request_ids.add(observation.reacquisition_request_id)
            if (
                observation.branch,
                observation.child_inquiry_id,
                observation.retention_package_id,
                observation.pins,
            ) != (
                observed_request.branch,
                observed_request.child_inquiry_id,
                observed_request.retention_package_id,
                observed_request.pins,
            ):
                raise ValueError("recovery observation must preserve exact request pins")
            if observation.child_prefix_sequence < observed_link.child_prefix_sequence:
                raise ValueError("recovery observation cannot precede the linked child prefix")
            require_independent_check(
                observation.measurement_check,
                proposition_id=observation.measurement_proposition_id,
                scope_fingerprint=observation.pins.scope_fingerprint,
            )
            if not observation.competence_established and observation.competence_check is not None:
                raise ValueError("unsuccessful recovery cannot carry a competence check")
            if observation.competence_check is not None:
                require_independent_check(
                    observation.competence_check,
                    proposition_id=observation.pins.target_competence_id,
                    scope_fingerprint=observation.pins.scope_fingerprint,
                )

        for comparison in self.recovery_comparisons:
            baseline_observations = tuple(
                observation_by_id[identifier]
                for identifier in comparison.baseline_frontier.source_observation_ids
                if identifier in observation_by_id
            )
            retained_observations = tuple(
                observation_by_id[identifier]
                for identifier in comparison.retained_frontier.source_observation_ids
                if identifier in observation_by_id
            )
            if len(baseline_observations) != len(
                comparison.baseline_frontier.source_observation_ids
            ) or len(retained_observations) != len(
                comparison.retained_frontier.source_observation_ids
            ):
                raise ValueError("recovery comparison frontiers require owned observations")
            try:
                baseline = derive_recovery_frontier(
                    branch=comparison.baseline_frontier.branch,
                    pins=comparison.baseline_frontier.pins,
                    observations=baseline_observations,
                )
                retained = derive_recovery_frontier(
                    branch=comparison.retained_frontier.branch,
                    pins=comparison.retained_frontier.pins,
                    observations=retained_observations,
                )
                expected = compare_recovery_frontiers(
                    comparison_id=comparison.id,
                    baseline=baseline,
                    retained=retained,
                    comparison_check=comparison.comparison_check,
                )
            except RecoveryCompatibilityError as error:
                raise ValueError("recovery comparison has incompatible exact pins") from error
            if expected != comparison:
                raise ValueError("recovery comparison must equal its pure derived frontier check")
            require_independent_check(
                comparison.comparison_check,
                proposition_id=comparison.comparison_proposition_id,
                scope_fingerprint=comparison.baseline_frontier.pins.scope_fingerprint,
            )
        return self

    def request_by_id(self, request_id: str) -> EffectRequestState | None:
        return next(
            (item for item in self.effect_requests if item.request.id == request_id),
            None,
        )

    def backlog_effect_by_id(self, effect_id: str) -> BacklogEffect | None:
        return next((effect for effect in self.backlog_effects if effect.id == effect_id), None)

    def step_plan_by_id(self, plan_id: str) -> StepPlan | None:
        return next((plan for plan in self.step_plans if plan.id == plan_id), None)

    @property
    def manifest_digest(self) -> str | None:
        """Compatibility view; the authoritative pin is the complete artifact reference."""

        return self.manifest_artifact.digest if self.manifest_artifact is not None else None

    def claim_by_id(self, claim_id: str) -> Claim | None:
        return next((claim for claim in self.claims if claim.id == claim_id), None)

    def obligation_by_id(self, obligation_id: str) -> Obligation | None:
        return next(
            (obligation for obligation in self.obligations if obligation.id == obligation_id),
            None,
        )

    def current_obligation_status(self, obligation_id: str) -> ObligationStatus | None:
        obligation = self.obligation_by_id(obligation_id)
        if obligation is None:
            return None
        dispositions = tuple(
            item for item in self.obligation_dispositions if item.obligation_id == obligation_id
        )
        return dispositions[-1].status if dispositions else obligation.status

    def latest_guard_change(self, condition_id: str) -> GuardChange | None:
        changes = tuple(item for item in self.guard_changes if item.condition_id == condition_id)
        return changes[-1] if changes else None

    def nogood_by_id(self, nogood_id: str) -> Nogood | None:
        return next((nogood for nogood in self.nogoods if nogood.id == nogood_id), None)

    def support_route_by_id(self, route_id: str) -> SupportRoute | None:
        return next(
            (
                route
                for support in self.lemma_supports
                for route in support.all_support_routes
                if route.id == route_id
            ),
            None,
        )

    def latest_support_route_standing_change(
        self, route_id: str
    ) -> SupportRouteStandingChange | None:
        changes = tuple(
            change
            for change in self.support_route_standing_changes
            if change.support_route_id == route_id
        )
        return changes[-1] if changes else None

    def latest_nogood_standing_change(self, nogood_id: str) -> NogoodStandingChange | None:
        changes = tuple(
            change for change in self.nogood_standing_changes if change.nogood_id == nogood_id
        )
        return changes[-1] if changes else None

    @property
    def standing_context_ids(self) -> frozenset[str]:
        latest = {change.condition_id: change for change in self.guard_changes}
        return frozenset(
            condition_id
            for condition_id, change in latest.items()
            if change.standing is GuardStanding.STANDING
        )

    def evidence_by_id(self, evidence_id: str) -> Evidence | None:
        return next(
            (evidence for evidence in self.evidence_records if evidence.id == evidence_id),
            None,
        )

    def warrant_decision_by_id(self, decision_id: str) -> WarrantDecisionRecord | None:
        return next(
            (decision for decision in self.warrant_decisions if decision.id == decision_id),
            None,
        )

    def checker_verdict_by_id(self, verdict_id: str) -> CheckerVerdictRecord | None:
        return next(
            (verdict for verdict in self.checker_verdicts if verdict.id == verdict_id),
            None,
        )

    @property
    def warranted_lemmas(self) -> tuple[WarrantedLemma, ...]:
        supports = {support.lemma_version_id: support for support in self.lemma_supports}
        return tuple(
            WarrantedLemma(version=version, support=supports[version.id])
            for version in self.lemma_versions
        )

    @property
    def current_theory_selector(self) -> TheorySelector | None:
        """Return the exact current pins for the rebuildable active-theory view."""

        if self.context is None:
            return None
        return TheorySelector(
            scope_fingerprint=self.context.scope_fingerprint,
            binding_revision=self.context.binding_revision,
            finite_universe_hash=self.context.finite_universe_hash,
            policy_version=self.context.warrant_policy_version,
            current_assumption_ids=tuple(sorted(self.context.assumption_ids)),
            current_context_ids=tuple(sorted(self.standing_context_ids)),
        )

    @property
    def active_theory(self) -> tuple[ActiveLemmaView, ...]:
        """Derive active lemmas solely from records owned by this aggregate."""

        selector = self.current_theory_selector
        if selector is None or self.context is None:
            return ()
        return select_active_theory(
            self.warranted_lemmas,
            selector=selector,
            nogoods=self.nogoods,
            support_route_standing_changes=self.support_route_standing_changes,
            nogood_standing_changes=self.nogood_standing_changes,
            evidence_records=self.evidence_records,
            checker_verdicts=self.checker_verdicts,
            authorized_checker_ids=self.context.discharge_mechanism_ids,
        )

    def cognitive_plan_by_id(self, plan_id: str) -> CognitiveAttemptPlan | None:
        return next((plan for plan in self.cognitive_plans if plan.id == plan_id), None)

    @property
    def captured_external_return_ids(self) -> frozenset[str]:
        return frozenset(
            attempt.outcome.external_return.id
            for request in self.effect_requests
            for attempt in request.attempts
            if isinstance(attempt.outcome, ReturnedOutcome)
        )

    @property
    def recorded_decode_outcome_ids(self) -> frozenset[str]:
        return frozenset(
            outcome.id for request in self.effect_requests for outcome in request.decode_outcomes
        )


def initial_state() -> InquiryState:
    """Return a fresh aggregate without generating any identity or time."""

    return InquiryState()
