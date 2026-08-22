"""Exact scoped promotion decisions for the initial warrant policy."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import model_validator

from rci.claims.models import FrozenModel, Scope
from rci.warrant.checks import (
    checker_verdict_index,
    evidence_index,
    resolve_check_reference,
    validate_checked_evidence,
)
from rci.warrant.models import (
    Applicability,
    CheckerVerdictRecord,
    Evidence,
    EvidenceKind,
    LemmaSupport,
    LemmaVersion,
    PropositionKind,
    SupportRoute,
    WarrantClass,
    WarrantedLemma,
)
from rci.warrant.support import (
    ancestry_is_acyclic,
    grounded_lemma_ids,
    support_graph_is_acyclic,
)


class PromotionOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class PromotionDecision(FrozenModel):
    outcome: PromotionOutcome
    warrant_class: WarrantClass
    reason: str
    lemma: WarrantedLemma | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> PromotionDecision:
        if self.outcome is PromotionOutcome.ACCEPTED and self.lemma is None:
            raise ValueError("accepted promotion requires a linked lemma")
        if self.outcome is PromotionOutcome.REJECTED and self.lemma is not None:
            raise ValueError("rejected promotion cannot carry a lemma")
        return self


def decide_evidence_warrant(
    evidence: Evidence,
    checker_verdict: CheckerVerdictRecord,
    *,
    proposition_id: str,
    proposition_kind: PropositionKind,
    scope: Scope,
    authorized_checker_ids: Iterable[str],
) -> tuple[WarrantClass, str]:
    if evidence.kind in (EvidenceKind.MODEL_OUTPUT, EvidenceKind.REIFICATION):
        return WarrantClass.NONE, "model output and reification provide no warrant"
    checked, reason = validate_checked_evidence(
        evidence,
        checker_verdict,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=scope.fingerprint,
        authorized_checker_ids=authorized_checker_ids,
    )
    if not checked:
        return WarrantClass.NONE, reason
    if evidence.kind is EvidenceKind.INDEPENDENT_WITNESS:
        if proposition_kind is not PropositionKind.EXISTENTIAL:
            return WarrantClass.NONE, "a witness warrants only its exact existential"
        return WarrantClass.HARD, "exact scoped existential witness"
    if evidence.kind is EvidenceKind.EXHAUSTIVE_UNSAT:
        if evidence.closed_finite_universe and (
            not scope.closed_world
            or scope.finite_universe_hash is None
            or evidence.finite_universe_hash != scope.finite_universe_hash
        ):
            return WarrantClass.NONE, "closed-finite evidence does not match the scoped universe"
        if evidence.closed_finite_universe:
            return WarrantClass.HARD, "exhaustive UNSAT over a closed finite universe"
        return WarrantClass.SOFT, "UNSAT universe was not declared closed"
    if evidence.kind is EvidenceKind.Z3_UNSAT:
        return WarrantClass.SOLVER_TRUSTED, "Z3-only UNSAT remains soft"
    if evidence.kind in (
        EvidenceKind.HEURISTIC,
        EvidenceKind.RETRIEVAL,
        EvidenceKind.OBSERVATION,
    ):
        return WarrantClass.SOFT, "policy-authorized evidence is provisional support"
    return WarrantClass.NONE, "unsupported evidence kind"


def decide_promotion(
    *,
    lemma_id: str,
    relation_id: str,
    proposition_kind: PropositionKind,
    scope: Scope,
    applicability: Applicability,
    support_routes: tuple[SupportRoute, ...],
    evidence: Evidence,
    checker_verdict: CheckerVerdictRecord,
    evidence_records: tuple[Evidence, ...],
    checker_verdicts: tuple[CheckerVerdictRecord, ...],
    authorized_checker_ids: Iterable[str],
    policy_version: str,
    provenance_refs: tuple[str, ...],
    source_claim_ids: tuple[str, ...],
    predecessor_refs: tuple[str, ...] = (),
    existing_lemmas: tuple[WarrantedLemma, ...] = (),
    current_assumption_ids: tuple[str, ...] = (),
    current_context_ids: tuple[str, ...] = (),
) -> PromotionDecision:
    """Create a joined lemma only after support, evidence, cycle, and ancestry gates."""

    if not policy_version:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="promotion requires an exact warrant-policy version",
        )
    evidence_by_id = evidence_index(evidence_records)
    checker_verdict_by_id = checker_verdict_index(checker_verdicts)
    if evidence_by_id.get(evidence.id) != evidence:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="promotion evidence is not an owned immutable record",
        )
    if checker_verdict_by_id.get(checker_verdict.id) != checker_verdict:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="promotion checker verdict is not an owned immutable record",
        )
    authorized = tuple(authorized_checker_ids)
    warrant_class, reason = decide_evidence_warrant(
        evidence,
        checker_verdict,
        proposition_id=relation_id,
        proposition_kind=proposition_kind,
        scope=scope,
        authorized_checker_ids=authorized,
    )
    if warrant_class is not WarrantClass.HARD:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=warrant_class,
            reason=reason,
        )
    if not support_routes:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="promotion requires an explicit support environment",
        )
    if any(route.conclusion_id != lemma_id for route in support_routes):
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="support route conclusion does not match the proposed lemma",
        )
    referenced_verdict_ids = {
        reference.checker_verdict_id
        for route in support_routes
        for reference in (route.certificate_check, route.environment.realizability_check)
    }
    referenced_verdict_ids.add(checker_verdict.id)
    certificate_refs = tuple(
        sorted(
            record.certificate_artifact.digest
            for verdict_id in referenced_verdict_ids
            if (record := checker_verdict_by_id.get(verdict_id)) is not None
            and record.certificate_artifact is not None
        )
    )
    version = LemmaVersion(
        id=lemma_id,
        relation_id=relation_id,
        proposition_kind=proposition_kind,
        scope=scope,
        applicability=applicability,
        source_claim_ids=source_claim_ids,
        predecessor_refs=predecessor_refs,
    )
    ordered_routes = tuple(
        sorted(
            support_routes,
            key=lambda route: (
                len(route.environment.assumption_ids),
                route.environment.assumption_ids,
                route.id,
            ),
        )
    )
    minimal_routes: list[SupportRoute] = []
    historical_routes: list[SupportRoute] = []
    for route in ordered_routes:
        if any(
            current.environment.assumptions <= route.environment.assumptions
            for current in minimal_routes
        ):
            historical_routes.append(route)
        else:
            minimal_routes.append(route)
    support = LemmaSupport(
        lemma_version_id=lemma_id,
        policy_version=policy_version,
        support_routes=tuple(minimal_routes),
        historical_support_routes=tuple(historical_routes),
        warrant_class=WarrantClass.HARD,
        certificate_refs=certificate_refs,
        provenance_refs=provenance_refs,
    )
    candidate = WarrantedLemma(version=version, support=support)
    all_lemmas = (*existing_lemmas, candidate)
    if not support_graph_is_acyclic(all_lemmas):
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="positive support cycle rejected atomically by the active milestone",
        )
    predecessor_map = {lemma.id: lemma.version.predecessor_refs for lemma in all_lemmas}
    if not ancestry_is_acyclic(predecessor_map):
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="authoritative version ancestry would become cyclic",
        )
    active_context = frozenset(current_context_ids)
    guard_active = (
        applicability.condition_id == "always" or applicability.condition_id in active_context
    ) and set(applicability.required_context_ids) <= active_context
    if not guard_active:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="the applicability guard is not active in the checked context",
        )
    same_support_class = tuple(
        lemma
        for lemma in existing_lemmas
        if lemma.version.scope.fingerprint == scope.fingerprint
        and lemma.version.scope.binding_revision == scope.binding_revision
        and lemma.version.scope.finite_universe_hash == scope.finite_universe_hash
        and lemma.support.policy_version == policy_version
    )
    grounded_dependencies = grounded_lemma_ids(
        same_support_class,
        current_assumption_ids=current_assumption_ids,
        current_context_ids=current_context_ids,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=authorized,
    )
    closed_routes: list[SupportRoute] = []
    for route in support.support_routes:
        route_checked, _ = resolve_check_reference(
            route.certificate_check,
            evidence_by_id=evidence_by_id,
            checker_verdict_by_id=checker_verdict_by_id,
            proposition_id=relation_id,
            proposition_kind=proposition_kind,
            scope_fingerprint=scope.fingerprint,
            authorized_checker_ids=authorized,
        )
        environment_checked, _ = resolve_check_reference(
            route.environment.realizability_check,
            evidence_by_id=evidence_by_id,
            checker_verdict_by_id=checker_verdict_by_id,
            proposition_id=route.environment.id,
            proposition_kind=PropositionKind.EXISTENTIAL,
            scope_fingerprint=scope.fingerprint,
            authorized_checker_ids=authorized,
        )
        if (
            not route.open_dependency_ids
            and set(route.required_dependency_ids) <= grounded_dependencies
            and route_checked
            and environment_checked
            and route.environment.scope_fingerprint == scope.fingerprint
            and route.environment.binding_revision == scope.binding_revision
            and route.environment.finite_universe_hash == scope.finite_universe_hash
        ):
            closed_routes.append(route)
    if not closed_routes:
        return PromotionDecision(
            outcome=PromotionOutcome.REJECTED,
            warrant_class=WarrantClass.NONE,
            reason="no support route is dependency-closed and independently realizable",
        )
    return PromotionDecision(
        outcome=PromotionOutcome.ACCEPTED,
        warrant_class=WarrantClass.HARD,
        reason=reason,
        lemma=candidate,
    )
