from __future__ import annotations

from hashlib import sha256

import pytest

from rci.claims import Claim, ClaimRole, InertPayload, Provenance, Scope, bind_l0_answer
from rci.core import ArtifactRef
from rci.formal import (
    And,
    EnumEquals,
    FailedReification,
    FiniteDomain,
    FiniteUniverse,
    NeedsClarification,
    Reified,
    Symbol,
    UnsupportedReification,
    evaluate,
    reify_claim,
)
from rci.warrant import (
    Applicability,
    CheckerVerdict,
    CheckerVerdictRecord,
    CheckReference,
    Evidence,
    EvidenceKind,
    LemmaSupport,
    LemmaVersion,
    PromotionOutcome,
    PropositionKind,
    SupportEnvironment,
    SupportRoute,
    SupportRouteStandingChange,
    SupportStanding,
    TheorySelector,
    WarrantClass,
    WarrantedLemma,
    active_lemma_views,
    ancestry_is_acyclic,
    decide_promotion,
    grounded_lemma_ids,
    support_graph_is_acyclic,
    ungrounded_support_cycles,
)

AUTHORIZED_CHECKER = "independent-enumerator"
POLICY_VERSION = "warrant-policy:1"


def artifact(label: str) -> ArtifactRef:
    return ArtifactRef(digest=sha256(label.encode()).hexdigest(), size=len(label))


def scope() -> Scope:
    universe = FiniteUniverse(
        id="u",
        revision="1",
        domains=(FiniteDomain(symbol="p", values=(False, True)),),
        closed_world=True,
    )
    return Scope(
        id="scope:test",
        binding_revision="binding:1",
        finite_universe_hash=universe.fingerprint,
        closed_world=True,
    )


def check_reference(label: str) -> CheckReference:
    return CheckReference(
        evidence_id=f"evidence:{label}",
        checker_verdict_id=f"check:{label}",
    )


def checked_material(
    label: str,
    *,
    proposition_id: str,
    proposition_kind: PropositionKind,
    current_scope: Scope | None = None,
    evidence_kind: EvidenceKind = EvidenceKind.INDEPENDENT_WITNESS,
    closed_finite_universe: bool = False,
    finite_universe_hash: str | None = None,
    checker_id: str = AUTHORIZED_CHECKER,
) -> tuple[Evidence, CheckerVerdictRecord]:
    checked_scope = current_scope or scope()
    evidence = Evidence(
        id=f"evidence:{label}",
        kind=evidence_kind,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=checked_scope.fingerprint,
        artifact=artifact(f"evidence:{label}"),
        closed_finite_universe=closed_finite_universe,
        finite_universe_hash=finite_universe_hash,
    )
    verdict = CheckerVerdictRecord(
        id=f"check:{label}",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=proposition_id,
        proposition_kind=proposition_kind,
        scope_fingerprint=checked_scope.fingerprint,
        checker_id=checker_id,
        checker_version="1",
        verdict=CheckerVerdict.VALID,
        verdict_artifact=artifact(f"verdict:{label}"),
        certificate_artifact=artifact(f"certificate:{label}"),
    )
    return evidence, verdict


def environment(identifier: str = "environment:empty") -> SupportEnvironment:
    current_scope = scope()
    return SupportEnvironment(
        id=identifier,
        scope_fingerprint=current_scope.fingerprint,
        binding_revision=current_scope.binding_revision,
        assumption_ids=(),
        finite_universe_hash=current_scope.finite_universe_hash,
        realizability_check=check_reference(identifier),
    )


def lemma(identifier: str, dependencies: tuple[str, ...]) -> WarrantedLemma:
    route = SupportRoute(
        id=f"route:{identifier}",
        conclusion_id=identifier,
        environment=environment(f"environment:{identifier}"),
        required_dependency_ids=dependencies,
        open_dependency_ids=dependencies,
        certificate_check=check_reference(f"route:{identifier}"),
    )
    return WarrantedLemma(
        version=LemmaVersion(
            id=identifier,
            relation_id=f"relation:{identifier}",
            proposition_kind=PropositionKind.RELATION,
            scope=scope(),
            applicability=Applicability(condition_id="always"),
            source_claim_ids=(f"claim:{identifier}",),
        ),
        support=LemmaSupport(
            lemma_version_id=identifier,
            policy_version=POLICY_VERSION,
            support_routes=(route,),
            warrant_class=WarrantClass.HARD,
            certificate_refs=(artifact(f"certificate:route:{identifier}").digest,),
            provenance_refs=("test",),
        ),
    )


def owned_checks(
    lemmas: tuple[WarrantedLemma, ...],
) -> tuple[tuple[Evidence, ...], tuple[CheckerVerdictRecord, ...]]:
    pairs: list[tuple[Evidence, CheckerVerdictRecord]] = []
    for current_lemma in lemmas:
        for route in current_lemma.support.all_support_routes:
            pairs.append(
                checked_material(
                    route.environment.id,
                    proposition_id=route.environment.id,
                    proposition_kind=PropositionKind.EXISTENTIAL,
                    current_scope=current_lemma.version.scope,
                )
            )
            pairs.append(
                checked_material(
                    route.id,
                    proposition_id=current_lemma.version.relation_id,
                    proposition_kind=current_lemma.version.proposition_kind,
                    current_scope=current_lemma.version.scope,
                )
            )
    evidence_by_id = {evidence.id: evidence for evidence, _ in pairs}
    verdict_by_id = {verdict.id: verdict for _, verdict in pairs}
    return tuple(evidence_by_id.values()), tuple(verdict_by_id.values())


def promotion_records(
    evidence: Evidence,
    checker_verdict: CheckerVerdictRecord,
    route: SupportRoute,
    *,
    relation_id: str,
    proposition_kind: PropositionKind,
    current_scope: Scope,
) -> tuple[tuple[Evidence, ...], tuple[CheckerVerdictRecord, ...]]:
    environment_pair = checked_material(
        route.environment.id,
        proposition_id=route.environment.id,
        proposition_kind=PropositionKind.EXISTENTIAL,
        current_scope=current_scope,
    )
    route_pair = checked_material(
        route.id,
        proposition_id=relation_id,
        proposition_kind=proposition_kind,
        current_scope=current_scope,
    )
    return (
        (evidence, environment_pair[0], route_pair[0]),
        (checker_verdict, environment_pair[1], route_pair[1]),
    )


def test_restricted_ast_interprets_boolean_and_finite_enum() -> None:
    formula = And(operands=(Symbol(name="enabled"), EnumEquals(symbol="mode", value="safe")))
    assert evaluate(formula, {"enabled": True, "mode": "safe"})
    assert not evaluate(formula, {"enabled": True, "mode": "unsafe"})


def test_reification_outcomes_fail_closed() -> None:
    def claim(answer: InertPayload) -> Claim:
        return bind_l0_answer(
            question_contract_id="q@1",
            role=ClaimRole.OBSERVATION,
            answer=answer,
            bound_args=(),
            scope=scope(),
            provenance=Provenance(kind="manual", source_id="test"),
        )

    opaque = claim("p")
    assert isinstance(reify_claim(opaque), NeedsClarification)
    unsupported = claim({"schema_id": "python.eval.v1", "carrier_id": "c", "expression": {}})
    assert isinstance(reify_claim(unsupported), UnsupportedReification)
    malformed = claim(
        {
            "schema_id": "rci.boolean-finite.v1",
            "carrier_id": "c",
            "expression": {"kind": "and", "operands": []},
        }
    )
    assert isinstance(reify_claim(malformed), FailedReification)
    valid = claim(
        {
            "schema_id": "rci.boolean-finite.v1",
            "carrier_id": "c",
            "expression": {"kind": "symbol", "name": "p"},
        }
    )
    assert isinstance(reify_claim(valid), Reified)


def test_support_recurrence_does_not_self_discharge() -> None:
    left = lemma("lemma:a", ("lemma:b",))
    right = lemma("lemma:b", ("lemma:a",))
    lemmas = (left, right)
    assert (
        grounded_lemma_ids(lemmas, current_assumption_ids=(), current_context_ids=()) == frozenset()
    )
    assert ungrounded_support_cycles(lemmas, current_assumption_ids=(), current_context_ids=()) == (
        ("lemma:a", "lemma:b"),
    )
    assert not support_graph_is_acyclic(lemmas)


def test_grounded_route_can_discharge_a_downstream_dependency() -> None:
    base = lemma("lemma:base", ())
    downstream = lemma("lemma:downstream", ("lemma:base",))
    evidence_records, checker_verdicts = owned_checks((downstream, base))
    grounded = grounded_lemma_ids(
        (downstream, base),
        current_assumption_ids=(),
        current_context_ids=(),
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
    )
    assert grounded == frozenset(("lemma:base", "lemma:downstream"))


def test_active_theory_selection_is_exactly_policy_scoped() -> None:
    base = lemma("lemma:policy-pinned", ())
    evidence_records, checker_verdicts = owned_checks((base,))
    selected = active_lemma_views(
        (base,),
        selector=TheorySelector(
            scope_fingerprint=scope().fingerprint,
            binding_revision=scope().binding_revision,
            finite_universe_hash=scope().finite_universe_hash,
            policy_version=POLICY_VERSION,
        ),
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
    )
    assert selected[0].policy_version == POLICY_VERSION
    exact_selector = TheorySelector(
        scope_fingerprint=scope().fingerprint,
        binding_revision=scope().binding_revision,
        finite_universe_hash=scope().finite_universe_hash,
        policy_version=POLICY_VERSION,
    )
    for changed_selector in (
        exact_selector.model_copy(update={"scope_fingerprint": "different-scope"}),
        exact_selector.model_copy(update={"binding_revision": "binding:2"}),
        exact_selector.model_copy(update={"policy_version": "warrant-policy:2"}),
    ):
        assert not active_lemma_views(
            (base,),
            selector=changed_selector,
            evidence_records=evidence_records,
            checker_verdicts=checker_verdicts,
            authorized_checker_ids=(AUTHORIZED_CHECKER,),
        )
    assert (
        active_lemma_views(
            (base,),
            selector=exact_selector,
            evidence_records=evidence_records,
            checker_verdicts=checker_verdicts,
            authorized_checker_ids=(AUTHORIZED_CHECKER,),
        )
        == selected
    )

    dominated = base.support.support_routes[0].model_copy(
        update={
            "id": "route:dominated",
            "certificate_check": check_reference("route:dominated"),
            "environment": base.support.support_routes[0].environment.model_copy(
                update={
                    "id": "environment:dominated",
                    "assumption_ids": ("extra",),
                    "realizability_check": check_reference("environment:dominated"),
                }
            ),
        }
    )
    with pytest.raises(ValueError, match="minimal antichain"):
        LemmaSupport(
            lemma_version_id=base.id,
            policy_version=POLICY_VERSION,
            support_routes=(*base.support.support_routes, dominated),
            warrant_class=WarrantClass.HARD,
            certificate_refs=base.support.certificate_refs,
            provenance_refs=base.support.provenance_refs,
        )

    historical = WarrantedLemma(
        version=base.version,
        support=LemmaSupport(
            lemma_version_id=base.id,
            policy_version=POLICY_VERSION,
            support_routes=base.support.support_routes,
            historical_support_routes=(dominated,),
            warrant_class=WarrantClass.HARD,
            certificate_refs=base.support.certificate_refs,
            provenance_refs=base.support.provenance_refs,
        ),
    )
    historical_evidence, historical_verdicts = owned_checks((historical,))
    reopened = active_lemma_views(
        (historical,),
        selector=TheorySelector(
            scope_fingerprint=scope().fingerprint,
            binding_revision=scope().binding_revision,
            finite_universe_hash=scope().finite_universe_hash,
            policy_version=POLICY_VERSION,
            current_assumption_ids=("extra",),
        ),
        support_route_standing_changes=(
            SupportRouteStandingChange(
                id="route-change:withdraw-minimal",
                support_route_id=base.support.support_routes[0].id,
                standing=SupportStanding.WITHDRAWN,
                reason="the initially minimal route no longer stands",
            ),
        ),
        evidence_records=historical_evidence,
        checker_verdicts=historical_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
    )
    assert reopened[0].standing_support_route_ids == (dominated.id,)


def test_promotion_checks_environment_scope_and_rejects_positive_cycle_atomically() -> None:
    current_scope = scope()
    evidence, checker_verdict = checked_material(
        "unsat",
        proposition_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=current_scope,
        evidence_kind=EvidenceKind.EXHAUSTIVE_UNSAT,
        closed_finite_universe=True,
        finite_universe_hash=current_scope.finite_universe_hash,
    )
    good_route = SupportRoute(
        id="route:new",
        conclusion_id="lemma:new",
        environment=environment("environment:new"),
        required_dependency_ids=(),
        open_dependency_ids=(),
        certificate_check=check_reference("route:new"),
    )
    evidence_records, checker_verdicts = promotion_records(
        evidence,
        checker_verdict,
        good_route,
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=current_scope,
    )
    accepted = decide_promotion(
        lemma_id="lemma:new",
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=current_scope,
        applicability=Applicability(condition_id="always"),
        support_routes=(good_route,),
        evidence=evidence,
        checker_verdict=checker_verdict,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
        policy_version=POLICY_VERSION,
        provenance_refs=("test",),
        source_claim_ids=("claim:new",),
    )
    assert accepted.outcome is PromotionOutcome.ACCEPTED

    cyclic_route = good_route.model_copy(
        update={
            "required_dependency_ids": ("lemma:new",),
            "open_dependency_ids": (),
        }
    )
    rejected = decide_promotion(
        lemma_id="lemma:new",
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=current_scope,
        applicability=Applicability(condition_id="always"),
        support_routes=(cyclic_route,),
        evidence=evidence,
        checker_verdict=checker_verdict,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
        policy_version=POLICY_VERSION,
        provenance_refs=("test",),
        source_claim_ids=("claim:new",),
    )
    assert rejected.outcome is PromotionOutcome.REJECTED
    assert "cycle" in rejected.reason
    assert ancestry_is_acyclic({"v1": (), "v2": ("v1",)})
    assert not ancestry_is_acyclic({"v1": ("v2",), "v2": ("v1",)})


def test_promotion_rejects_forged_closed_world_missing_dependency_and_inactive_guard() -> None:
    open_scope = Scope(id="scope:open", binding_revision="binding:1")
    forged_evidence, forged_checker = checked_material(
        "forged-closed",
        proposition_id="relation:forged",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=open_scope,
        evidence_kind=EvidenceKind.EXHAUSTIVE_UNSAT,
        closed_finite_universe=True,
        finite_universe_hash="f" * 64,
    )
    forged_environment = SupportEnvironment(
        id="environment:forged",
        scope_fingerprint=open_scope.fingerprint,
        binding_revision=open_scope.binding_revision,
        assumption_ids=(),
        finite_universe_hash=None,
        realizability_check=check_reference("environment:forged"),
    )
    forged_route = SupportRoute(
        id="route:forged",
        conclusion_id="lemma:forged",
        environment=forged_environment,
        required_dependency_ids=(),
        open_dependency_ids=(),
        certificate_check=check_reference("route:forged"),
    )
    forged_evidence_records, forged_verdicts = promotion_records(
        forged_evidence,
        forged_checker,
        forged_route,
        relation_id="relation:forged",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=open_scope,
    )
    forged = decide_promotion(
        lemma_id="lemma:forged",
        relation_id="relation:forged",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=open_scope,
        applicability=Applicability(condition_id="always"),
        support_routes=(forged_route,),
        evidence=forged_evidence,
        checker_verdict=forged_checker,
        evidence_records=forged_evidence_records,
        checker_verdicts=forged_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
        policy_version=POLICY_VERSION,
        provenance_refs=("test",),
        source_claim_ids=("claim:forged",),
    )
    assert forged.outcome is PromotionOutcome.REJECTED
    assert "scoped universe" in forged.reason

    current_scope = scope()
    evidence, checker_verdict = checked_material(
        "closed",
        proposition_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=current_scope,
        evidence_kind=EvidenceKind.EXHAUSTIVE_UNSAT,
        closed_finite_universe=True,
        finite_universe_hash=current_scope.finite_universe_hash,
    )
    missing_dependency_route = SupportRoute(
        id="route:missing-dependency",
        conclusion_id="lemma:new",
        environment=environment("environment:missing-dependency"),
        required_dependency_ids=("lemma:missing",),
        open_dependency_ids=(),
        certificate_check=check_reference("route:missing-dependency"),
    )
    evidence_records, checker_verdicts = promotion_records(
        evidence,
        checker_verdict,
        missing_dependency_route,
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=current_scope,
    )
    missing = decide_promotion(
        lemma_id="lemma:new",
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=current_scope,
        applicability=Applicability(condition_id="always"),
        support_routes=(missing_dependency_route,),
        evidence=evidence,
        checker_verdict=checker_verdict,
        evidence_records=evidence_records,
        checker_verdicts=checker_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
        policy_version=POLICY_VERSION,
        provenance_refs=("test",),
        source_claim_ids=("claim:new",),
    )
    assert missing.outcome is PromotionOutcome.REJECTED
    assert "dependency-closed" in missing.reason

    inactive_guard_route = missing_dependency_route.model_copy(
        update={
            "id": "route:inactive-guard",
            "required_dependency_ids": (),
        }
    )
    inactive_evidence_records, inactive_verdicts = promotion_records(
        evidence,
        checker_verdict,
        inactive_guard_route,
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        current_scope=current_scope,
    )
    inactive = decide_promotion(
        lemma_id="lemma:new",
        relation_id="relation:new",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=current_scope,
        applicability=Applicability(condition_id="guard:not-active"),
        support_routes=(inactive_guard_route,),
        evidence=evidence,
        checker_verdict=checker_verdict,
        evidence_records=inactive_evidence_records,
        checker_verdicts=inactive_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
        policy_version=POLICY_VERSION,
        provenance_refs=("test",),
        source_claim_ids=("claim:new",),
    )
    assert inactive.outcome is PromotionOutcome.REJECTED
    assert "guard" in inactive.reason


def test_grounding_uses_required_dependencies_and_checked_active_guard() -> None:
    floating = lemma("lemma:floating", ("lemma:missing",))
    floating_evidence, floating_verdicts = owned_checks((floating,))
    cleared_boundary = floating.support.support_routes[0].model_copy(
        update={"open_dependency_ids": ()}
    )
    floating = floating.model_copy(
        update={
            "support": floating.support.model_copy(update={"support_routes": (cleared_boundary,)})
        }
    )
    assert (
        grounded_lemma_ids(
            (floating,),
            current_assumption_ids=(),
            current_context_ids=(),
            evidence_records=floating_evidence,
            checker_verdicts=floating_verdicts,
            authorized_checker_ids=(AUTHORIZED_CHECKER,),
        )
        == frozenset()
    )

    guarded = lemma("lemma:guarded", ())
    guarded = guarded.model_copy(
        update={
            "version": guarded.version.model_copy(
                update={"applicability": Applicability(condition_id="guard:active")}
            )
        }
    )
    guarded_evidence, guarded_verdicts = owned_checks((guarded,))
    assert (
        grounded_lemma_ids(
            (guarded,),
            current_assumption_ids=(),
            current_context_ids=(),
            evidence_records=guarded_evidence,
            checker_verdicts=guarded_verdicts,
            authorized_checker_ids=(AUTHORIZED_CHECKER,),
        )
        == frozenset()
    )
    assert grounded_lemma_ids(
        (guarded,),
        current_assumption_ids=(item for item in ("unused",)),
        current_context_ids=("guard:active",),
        evidence_records=guarded_evidence,
        checker_verdicts=guarded_verdicts,
        authorized_checker_ids=(AUTHORIZED_CHECKER,),
    ) == frozenset(("lemma:guarded",))

    mismatched_environment = guarded.support.support_routes[0].environment.model_copy(
        update={"finite_universe_hash": "different-universe"}
    )
    mismatched_route = guarded.support.support_routes[0].model_copy(
        update={"environment": mismatched_environment}
    )
    mismatched = guarded.model_copy(
        update={
            "support": guarded.support.model_copy(update={"support_routes": (mismatched_route,)})
        }
    )
    assert (
        grounded_lemma_ids(
            (mismatched,),
            current_assumption_ids=(),
            current_context_ids=("guard:active",),
            evidence_records=guarded_evidence,
            checker_verdicts=guarded_verdicts,
            authorized_checker_ids=(AUTHORIZED_CHECKER,),
        )
        == frozenset()
    )
