"""A code-free Boolean and finite-enum expression language."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import Field, model_validator

from rci.claims.models import FrozenModel

type Scalar = bool | str
type Environment = Mapping[str, Scalar]


class BoolLiteral(FrozenModel):
    kind: Literal["bool"] = "bool"
    value: bool


class Symbol(FrozenModel):
    kind: Literal["symbol"] = "symbol"
    name: str

    @model_validator(mode="after")
    def validate_name(self) -> Symbol:
        if not self.name:
            raise ValueError("symbol name cannot be empty")
        return self


class EnumEquals(FrozenModel):
    kind: Literal["enum_equals"] = "enum_equals"
    symbol: str
    value: str

    @model_validator(mode="after")
    def validate_operands(self) -> EnumEquals:
        if not self.symbol or not self.value:
            raise ValueError("enum equality requires a symbol and value")
        return self


class Not(FrozenModel):
    kind: Literal["not"] = "not"
    operand: Formula


class And(FrozenModel):
    kind: Literal["and"] = "and"
    operands: tuple[Formula, ...]

    @model_validator(mode="after")
    def validate_operands(self) -> And:
        if not self.operands:
            raise ValueError("and requires at least one operand")
        return self


class Or(FrozenModel):
    kind: Literal["or"] = "or"
    operands: tuple[Formula, ...]

    @model_validator(mode="after")
    def validate_operands(self) -> Or:
        if not self.operands:
            raise ValueError("or requires at least one operand")
        return self


class Implies(FrozenModel):
    kind: Literal["implies"] = "implies"
    antecedent: Formula
    consequent: Formula


class Equivalence(FrozenModel):
    kind: Literal["equivalence"] = "equivalence"
    left: Formula
    right: Formula


type Formula = Annotated[
    BoolLiteral | Symbol | EnumEquals | Not | And | Or | Implies | Equivalence,
    Field(discriminator="kind"),
]

Not.model_rebuild()
And.model_rebuild()
Or.model_rebuild()
Implies.model_rebuild()
Equivalence.model_rebuild()


class EvaluationError(ValueError):
    """Raised only for an ill-bound environment, never for user payload execution."""


def evaluate(formula: Formula, environment: Environment) -> bool:
    """Interpret a validated formula directly; no source evaluation is involved."""

    if isinstance(formula, BoolLiteral):
        return formula.value
    if isinstance(formula, Symbol):
        value = environment.get(formula.name)
        if not isinstance(value, bool):
            raise EvaluationError(f"{formula.name!r} is absent or not Boolean")
        return value
    if isinstance(formula, EnumEquals):
        value = environment.get(formula.symbol)
        if not isinstance(value, str):
            raise EvaluationError(f"{formula.symbol!r} is absent or not a finite enum")
        return value == formula.value
    if isinstance(formula, Not):
        return not evaluate(formula.operand, environment)
    if isinstance(formula, And):
        return all(evaluate(operand, environment) for operand in formula.operands)
    if isinstance(formula, Or):
        return any(evaluate(operand, environment) for operand in formula.operands)
    if isinstance(formula, Implies):
        return not evaluate(formula.antecedent, environment) or evaluate(
            formula.consequent, environment
        )
    if isinstance(formula, Equivalence):
        return evaluate(formula.left, environment) == evaluate(formula.right, environment)
    raise TypeError(f"unsupported validated formula node: {type(formula).__name__}")


def formula_symbols(formula: Formula) -> frozenset[str]:
    if isinstance(formula, BoolLiteral):
        return frozenset()
    if isinstance(formula, Symbol):
        return frozenset((formula.name,))
    if isinstance(formula, EnumEquals):
        return frozenset((formula.symbol,))
    if isinstance(formula, Not):
        return formula_symbols(formula.operand)
    if isinstance(formula, (And, Or)):
        return frozenset().union(*(formula_symbols(item) for item in formula.operands))
    if isinstance(formula, Implies):
        return formula_symbols(formula.antecedent) | formula_symbols(formula.consequent)
    if isinstance(formula, Equivalence):
        return formula_symbols(formula.left) | formula_symbols(formula.right)
    raise TypeError(f"unsupported validated formula node: {type(formula).__name__}")
