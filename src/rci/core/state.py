"""Deeply immutable aggregate state rebuilt exclusively from events."""

from __future__ import annotations

from typing import Literal

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
        )
        for identifiers in identified_collections:
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("domain record identities must be unique per owner")
        probe_fingerprints = [probe.fingerprint for probe in self.admitted_probes]
        if len(probe_fingerprints) != len(set(probe_fingerprints)):
            raise ValueError("admitted recurrent probe identities must be unique")

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
