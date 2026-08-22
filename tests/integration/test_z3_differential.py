from __future__ import annotations

from collections.abc import Mapping
from itertools import product

import pytest

import rci.backends.z3_backend as z3_backend
from rci.backends import BackendExecutionStatus, LogicalResult, check_with_z3
from rci.claims import Scope
from rci.core import ArtifactRef
from rci.formal import (
    And,
    BoolLiteral,
    EnumEquals,
    Equivalence,
    ExhaustiveVerdict,
    FiniteDomain,
    FiniteUniverse,
    Formula,
    Implies,
    Not,
    Or,
    Symbol,
    evaluate,
)
from rci.formal.exhaustive import exhaustive_check
from rci.warrant import (
    Applicability,
    CheckerVerdict,
    CheckerVerdictRecord,
    Evidence,
    EvidenceKind,
    PromotionOutcome,
    PropositionKind,
    WarrantClass,
    decide_evidence_warrant,
    decide_promotion,
)


def _universe() -> FiniteUniverse:
    return FiniteUniverse(
        id="universe:z3-differential",
        revision="1",
        domains=(
            FiniteDomain(symbol="mode", values=("safe", "unsafe")),
            FiniteDomain(symbol="p", values=(False, True)),
            FiniteDomain(symbol="q", values=(False, True)),
        ),
        closed_world=True,
    )


def _bounded_formulas() -> tuple[Formula, ...]:
    atoms: tuple[Formula, ...] = (
        BoolLiteral(value=False),
        BoolLiteral(value=True),
        Symbol(name="p"),
        Symbol(name="q"),
        EnumEquals(symbol="mode", value="safe"),
        EnumEquals(symbol="mode", value="unsafe"),
        EnumEquals(symbol="mode", value="not-in-domain"),
    )
    formulas: list[Formula] = [*atoms, *(Not(operand=item) for item in atoms)]
    for left, right in product(atoms, repeat=2):
        formulas.extend(
            (
                And(operands=(left, right)),
                Or(operands=(left, right)),
                Implies(antecedent=left, consequent=right),
                Equivalence(left=left, right=right),
            )
        )
    formulas.extend(
        (
            Not(
                operand=And(
                    operands=(
                        Symbol(name="p"),
                        Or(
                            operands=(
                                Symbol(name="q"),
                                EnumEquals(symbol="mode", value="safe"),
                            )
                        ),
                    )
                )
            ),
            Equivalence(
                left=Implies(antecedent=Symbol(name="p"), consequent=Symbol(name="q")),
                right=Or(operands=(Not(operand=Symbol(name="p")), Symbol(name="q"))),
            ),
        )
    )
    return tuple(formulas)


@pytest.mark.optional
def test_z3_matches_independent_exhaustive_interpreter_over_bounded_formulas() -> None:
    universe = _universe()
    expected_results = {
        ExhaustiveVerdict.SAT: LogicalResult.SAT,
        ExhaustiveVerdict.UNSAT: LogicalResult.UNSAT,
    }
    for formula in _bounded_formulas():
        exhaustive = exhaustive_check(formula, universe)
        assert exhaustive.verdict in expected_results
        result = check_with_z3(formula, universe)
        assert result.execution_status is BackendExecutionStatus.COMPLETED, formula
        assert result.logical_result is expected_results[exhaustive.verdict], formula
        assert not result.promotion_authorized
        if result.logical_result is LogicalResult.SAT:
            assert result.witness is not None
            assert result.witness_rechecked
            assert result.checker_verdict is CheckerVerdict.VALID
            assert evaluate(formula, result.witness.as_environment())
            assert result.warrant_class is WarrantClass.NONE
        else:
            assert result.witness is None
            assert result.warrant_class is WarrantClass.SOLVER_TRUSTED


@pytest.mark.optional
def test_sat_model_is_rechecked_by_the_independent_interpreter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, bool | str]] = []
    independent_evaluate = evaluate

    def tracking_evaluate(
        formula: Formula,
        environment: Mapping[str, bool | str],
    ) -> bool:
        calls.append(dict(environment))
        return independent_evaluate(formula, environment)

    monkeypatch.setattr(z3_backend, "evaluate", tracking_evaluate)
    formula = And(
        operands=(
            Symbol(name="p"),
            EnumEquals(symbol="mode", value="safe"),
        )
    )
    result = check_with_z3(formula, _universe())
    assert result.logical_result is LogicalResult.SAT
    assert result.witness_rechecked
    assert result.witness is not None
    assert calls == [result.witness.as_environment()]


@pytest.mark.optional
def test_z3_only_unsat_is_solver_trusted_and_cannot_promote() -> None:
    universe = _universe()
    contradiction = And(
        operands=(
            Symbol(name="p"),
            Not(operand=Symbol(name="p")),
        )
    )
    result = check_with_z3(contradiction, universe)
    assert result.logical_result is LogicalResult.UNSAT
    assert result.checker_verdict is CheckerVerdict.VALID
    assert result.warrant_class is WarrantClass.SOLVER_TRUSTED
    assert not result.promotion_authorized

    scope = Scope(
        id="scope:z3-unsat",
        binding_revision="binding:1",
        finite_universe_hash=universe.fingerprint,
        closed_world=True,
    )
    evidence = Evidence(
        id="evidence:z3-unsat",
        kind=EvidenceKind.Z3_UNSAT,
        proposition_id="relation:contradiction",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope_fingerprint=scope.fingerprint,
        artifact=ArtifactRef(digest="1" * 64, size=1),
        closed_finite_universe=True,
        finite_universe_hash=universe.fingerprint,
    )
    checker_verdict = CheckerVerdictRecord(
        id="checker-verdict:z3-unsat",
        evidence_id=evidence.id,
        evidence_artifact=evidence.artifact,
        proposition_id=evidence.proposition_id,
        proposition_kind=evidence.proposition_kind,
        scope_fingerprint=evidence.scope_fingerprint,
        checker_id="z3",
        checker_version="test",
        verdict=result.checker_verdict,
        verdict_artifact=ArtifactRef(digest="2" * 64, size=1),
        certificate_artifact=ArtifactRef(digest="3" * 64, size=1),
    )
    warrant_class, _ = decide_evidence_warrant(
        evidence,
        checker_verdict,
        proposition_id="relation:contradiction",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=scope,
        authorized_checker_ids=("z3",),
    )
    assert warrant_class is WarrantClass.SOLVER_TRUSTED
    promotion = decide_promotion(
        lemma_id="lemma:contradiction",
        relation_id="relation:contradiction",
        proposition_kind=PropositionKind.UNIVERSAL,
        scope=scope,
        applicability=Applicability(condition_id="always"),
        support_routes=(),
        evidence=evidence,
        checker_verdict=checker_verdict,
        evidence_records=(evidence,),
        checker_verdicts=(checker_verdict,),
        authorized_checker_ids=("z3",),
        policy_version="warrant-policy:1",
        provenance_refs=("test",),
        source_claim_ids=("claim:contradiction",),
    )
    assert promotion.outcome is PromotionOutcome.REJECTED
    assert promotion.warrant_class is WarrantClass.SOLVER_TRUSTED


@pytest.mark.optional
def test_z3_respects_restricted_boolean_and_enum_domains() -> None:
    boolean_subset = FiniteUniverse(
        id="universe:false-only",
        revision="1",
        domains=(FiniteDomain(symbol="p", values=(False,)),),
        closed_world=True,
    )
    false_only = check_with_z3(Symbol(name="p"), boolean_subset)
    assert false_only.logical_result is LogicalResult.UNSAT

    missing_enum = check_with_z3(
        EnumEquals(symbol="mode", value="missing"),
        _universe(),
    )
    assert missing_enum.logical_result is LogicalResult.UNSAT
