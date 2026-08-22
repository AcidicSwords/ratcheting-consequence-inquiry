"""Independent exhaustive semantics for bounded formulas."""

from __future__ import annotations

from enum import StrEnum
from itertools import product
from math import prod

from pydantic import model_validator

from rci.claims.models import FrozenModel, content_fingerprint
from rci.formal.ast import And, Formula, Not, Scalar, evaluate, formula_symbols


class AttackProfile(StrEnum):
    NECESSITY = "necessity"
    SUFFICIENCY = "sufficiency"
    PREREQUISITE = "prerequisite"
    LOCALIZATION = "localization"
    GENERALIZATION = "generalization"
    ACTUALIZATION = "actualization"


class ExhaustiveVerdict(StrEnum):
    SAT = "sat"
    UNSAT = "unsat"
    UNKNOWN = "unknown"


class AssignmentValue(FrozenModel):
    symbol: str
    value: Scalar


class Assignment(FrozenModel):
    values: tuple[AssignmentValue, ...]

    def as_environment(self) -> dict[str, Scalar]:
        return {item.symbol: item.value for item in self.values}


class FiniteDomain(FrozenModel):
    symbol: str
    values: tuple[Scalar, ...]

    @model_validator(mode="after")
    def validate_domain(self) -> FiniteDomain:
        if not self.symbol or not self.values:
            raise ValueError("finite domains require a symbol and at least one value")
        if len({(type(value).__name__, value) for value in self.values}) != len(self.values):
            raise ValueError("finite domain values must be unique")
        types = {type(value) for value in self.values}
        if types not in ({bool}, {str}):
            raise ValueError("each domain must be uniformly Boolean or string-enum")
        return self


class FiniteUniverse(FrozenModel):
    id: str
    revision: str
    domains: tuple[FiniteDomain, ...]
    closed_world: bool

    @model_validator(mode="after")
    def validate_universe(self) -> FiniteUniverse:
        if not self.id or not self.revision or not self.domains:
            raise ValueError("finite-universe identity, revision, and domains are required")
        names = [domain.symbol for domain in self.domains]
        if len(set(names)) != len(names):
            raise ValueError("finite-universe symbols must be unique")
        if names != sorted(names):
            raise ValueError("finite-universe domains must use canonical symbol order")
        return self

    @property
    def assignment_count(self) -> int:
        return prod(len(domain.values) for domain in self.domains)

    @property
    def fingerprint(self) -> str:
        return content_fingerprint("rci.finite-universe.v1", self)


class ExhaustiveResult(FrozenModel):
    verdict: ExhaustiveVerdict
    universe_id: str
    universe_revision: str
    universe_fingerprint: str
    closed_world: bool
    assignments_checked: int
    witness: Assignment | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_result(self) -> ExhaustiveResult:
        if self.verdict is ExhaustiveVerdict.SAT and self.witness is None:
            raise ValueError("SAT results require a witness")
        if self.verdict is not ExhaustiveVerdict.SAT and self.witness is not None:
            raise ValueError("only SAT results may carry a witness")
        if self.verdict is ExhaustiveVerdict.UNKNOWN and self.reason is None:
            raise ValueError("unknown results require a reason")
        return self

    @property
    def hard_unsat_eligible(self) -> bool:
        return self.verdict is ExhaustiveVerdict.UNSAT and self.closed_world


def enumerate_assignments(universe: FiniteUniverse) -> tuple[Assignment, ...]:
    return tuple(
        Assignment(
            values=tuple(
                AssignmentValue(symbol=domain.symbol, value=value)
                for domain, value in zip(universe.domains, combination, strict=True)
            )
        )
        for combination in product(*(domain.values for domain in universe.domains))
    )


def exhaustive_check(
    formula: Formula,
    universe: FiniteUniverse,
    *,
    max_assignments: int = 4096,
) -> ExhaustiveResult:
    if max_assignments < 1:
        raise ValueError("max_assignments must be positive")
    if universe.assignment_count > max_assignments:
        return ExhaustiveResult(
            verdict=ExhaustiveVerdict.UNKNOWN,
            universe_id=universe.id,
            universe_revision=universe.revision,
            universe_fingerprint=universe.fingerprint,
            closed_world=universe.closed_world,
            assignments_checked=0,
            reason="assignment_budget_exceeded",
        )
    universe_symbols = {domain.symbol for domain in universe.domains}
    missing = formula_symbols(formula) - universe_symbols
    if missing:
        return ExhaustiveResult(
            verdict=ExhaustiveVerdict.UNKNOWN,
            universe_id=universe.id,
            universe_revision=universe.revision,
            universe_fingerprint=universe.fingerprint,
            closed_world=universe.closed_world,
            assignments_checked=0,
            reason=f"unbound_symbols:{','.join(sorted(missing))}",
        )
    checked = 0
    for assignment in enumerate_assignments(universe):
        checked += 1
        if evaluate(formula, assignment.as_environment()):
            return ExhaustiveResult(
                verdict=ExhaustiveVerdict.SAT,
                universe_id=universe.id,
                universe_revision=universe.revision,
                universe_fingerprint=universe.fingerprint,
                closed_world=universe.closed_world,
                assignments_checked=checked,
                witness=assignment,
            )
    return ExhaustiveResult(
        verdict=ExhaustiveVerdict.UNSAT,
        universe_id=universe.id,
        universe_revision=universe.revision,
        universe_fingerprint=universe.fingerprint,
        closed_world=universe.closed_world,
        assignments_checked=checked,
    )


def implication_attack(
    *,
    profile: AttackProfile,
    proposed_condition: Formula,
    protected_consequence: Formula,
    universe: FiniteUniverse,
    max_assignments: int = 4096,
) -> ExhaustiveResult:
    """Search the exact counterexample shape required by an attack profile."""

    if profile in (AttackProfile.NECESSITY, AttackProfile.PREREQUISITE):
        counterexample = And(operands=(protected_consequence, Not(operand=proposed_condition)))
    elif profile in (
        AttackProfile.SUFFICIENCY,
        AttackProfile.GENERALIZATION,
        AttackProfile.ACTUALIZATION,
    ):
        counterexample = And(operands=(proposed_condition, Not(operand=protected_consequence)))
    else:
        counterexample = And(operands=(proposed_condition, Not(operand=protected_consequence)))
    return exhaustive_check(counterexample, universe, max_assignments=max_assignments)
