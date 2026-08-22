"""Lazy, optional Z3 translation for the restricted finite formula language.

The backend deliberately does not produce promotion decisions.  A satisfiable model is
translated back into an RCI assignment and re-evaluated by the independent interpreter.
An UNSAT answer without an independently replayable proof remains solver-trusted only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
from types import ModuleType
from typing import Any, Literal

from pydantic import model_validator

from rci.claims.models import FrozenModel, content_fingerprint
from rci.formal.ast import (
    And,
    BoolLiteral,
    EnumEquals,
    Equivalence,
    Formula,
    Implies,
    Not,
    Or,
    Symbol,
    evaluate,
)
from rci.formal.exhaustive import Assignment, AssignmentValue, FiniteDomain, FiniteUniverse
from rci.warrant.models import CheckerVerdict, WarrantClass


class BackendExecutionStatus(StrEnum):
    """Execution status kept separate from the backend's logical answer."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class LogicalResult(StrEnum):
    SAT = "sat"
    UNSAT = "unsat"
    UNKNOWN = "unknown"


class Z3CheckResult(FrozenModel):
    """Typed Z3 return after translation and any independent witness check."""

    backend_id: Literal["z3"] = "z3"
    backend_version: str | None
    execution_status: BackendExecutionStatus
    logical_result: LogicalResult | None
    checker_verdict: CheckerVerdict
    warrant_class: WarrantClass
    query_fingerprint: str
    universe_id: str
    universe_revision: str
    universe_fingerprint: str
    witness: Assignment | None = None
    witness_rechecked: bool | None = None
    reason: str | None = None
    promotion_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_stage_separation(self) -> Z3CheckResult:
        if self.execution_status in (
            BackendExecutionStatus.UNSUPPORTED,
            BackendExecutionStatus.FAILED,
        ):
            if self.logical_result is not None:
                raise ValueError("non-executed Z3 checks cannot claim a logical result")
            if self.warrant_class is not WarrantClass.NONE:
                raise ValueError("non-executed Z3 checks cannot carry warrant")
        elif self.logical_result is None:
            raise ValueError("completed or timed-out Z3 checks require a logical result")

        if self.logical_result is LogicalResult.SAT:
            if self.witness is None or self.witness_rechecked is None:
                raise ValueError("SAT requires an extracted and independently checked witness")
            expected = CheckerVerdict.VALID if self.witness_rechecked else CheckerVerdict.INVALID
            if self.checker_verdict is not expected:
                raise ValueError("SAT checker verdict must reflect independent interpretation")
            if self.warrant_class is not WarrantClass.NONE:
                raise ValueError("the backend cannot bind a witness to scoped warrant")
        elif self.witness is not None or self.witness_rechecked is not None:
            raise ValueError("only SAT results may carry a witness")

        if self.logical_result is LogicalResult.UNSAT:
            if self.execution_status is not BackendExecutionStatus.COMPLETED:
                raise ValueError("UNSAT requires completed solver execution")
            if self.checker_verdict is not CheckerVerdict.VALID:
                raise ValueError("UNSAT requires a valid translated solver response")
            if self.warrant_class is not WarrantClass.SOLVER_TRUSTED:
                raise ValueError("Z3-only UNSAT must remain solver-trusted")
        elif self.warrant_class is WarrantClass.SOLVER_TRUSTED:
            raise ValueError("solver-trusted warrant is reserved for Z3-only UNSAT")

        if self.logical_result is LogicalResult.UNKNOWN and self.reason is None:
            raise ValueError("unknown logical results require the solver reason")
        if self.execution_status is BackendExecutionStatus.TIMEOUT:
            if self.logical_result is not LogicalResult.UNKNOWN:
                raise ValueError("timeout cannot imply SAT or UNSAT")
            if self.checker_verdict is not CheckerVerdict.TIMEOUT:
                raise ValueError("timeout requires a timeout checker verdict")
        return self


class _UnsupportedTranslation(ValueError):
    pass


class _BackendLoadFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class _Translation:
    expression: Any
    constraints: tuple[Any, ...]
    variables: dict[str, Any]


def _query_fingerprint(formula: Formula, universe: FiniteUniverse) -> str:
    return content_fingerprint(
        "rci.z3-query.v1",
        {
            "formula": formula,
            "universe": universe,
        },
    )


def _load_z3() -> ModuleType:
    try:
        return import_module("z3")
    except (ImportError, ModuleNotFoundError) as error:
        raise _UnsupportedTranslation("z3_extra_not_installed") from error
    except Exception as error:
        raise _BackendLoadFailure(f"z3_import_failed:{type(error).__name__}:{error}") from error


def _formula_node_count(formula: Formula) -> int:
    if isinstance(formula, (BoolLiteral, Symbol, EnumEquals)):
        return 1
    if isinstance(formula, Not):
        return 1 + _formula_node_count(formula.operand)
    if isinstance(formula, (And, Or)):
        return 1 + sum(_formula_node_count(item) for item in formula.operands)
    if isinstance(formula, Implies):
        return 1 + _formula_node_count(formula.antecedent) + _formula_node_count(formula.consequent)
    if isinstance(formula, Equivalence):
        return 1 + _formula_node_count(formula.left) + _formula_node_count(formula.right)
    raise TypeError(f"unsupported validated formula node: {type(formula).__name__}")


def _domain_by_symbol(universe: FiniteUniverse) -> dict[str, FiniteDomain]:
    return {domain.symbol: domain for domain in universe.domains}


def _validate_binding(formula: Formula, domains: dict[str, FiniteDomain]) -> None:
    if isinstance(formula, BoolLiteral):
        return
    if isinstance(formula, Symbol):
        domain = domains.get(formula.name)
        if domain is None:
            raise _UnsupportedTranslation(f"unbound_symbol:{formula.name}")
        if not all(isinstance(value, bool) for value in domain.values):
            raise _UnsupportedTranslation(f"boolean_symbol_bound_to_enum:{formula.name}")
        return
    if isinstance(formula, EnumEquals):
        domain = domains.get(formula.symbol)
        if domain is None:
            raise _UnsupportedTranslation(f"unbound_symbol:{formula.symbol}")
        if not all(isinstance(value, str) for value in domain.values):
            raise _UnsupportedTranslation(f"enum_equality_bound_to_boolean:{formula.symbol}")
        return
    if isinstance(formula, Not):
        _validate_binding(formula.operand, domains)
        return
    if isinstance(formula, (And, Or)):
        for item in formula.operands:
            _validate_binding(item, domains)
        return
    if isinstance(formula, Implies):
        _validate_binding(formula.antecedent, domains)
        _validate_binding(formula.consequent, domains)
        return
    if isinstance(formula, Equivalence):
        _validate_binding(formula.left, domains)
        _validate_binding(formula.right, domains)
        return
    raise TypeError(f"unsupported validated formula node: {type(formula).__name__}")


def _translate_node(
    formula: Formula,
    *,
    z3_module: ModuleType,
    domains: dict[str, FiniteDomain],
    variables: dict[str, Any],
) -> Any:
    if isinstance(formula, BoolLiteral):
        return z3_module.BoolVal(formula.value)
    if isinstance(formula, Symbol):
        return variables[formula.name]
    if isinstance(formula, EnumEquals):
        values = domains[formula.symbol].values
        if formula.value not in values:
            return z3_module.BoolVal(False)
        return variables[formula.symbol] == values.index(formula.value)
    if isinstance(formula, Not):
        return z3_module.Not(
            _translate_node(
                formula.operand,
                z3_module=z3_module,
                domains=domains,
                variables=variables,
            )
        )
    if isinstance(formula, And):
        return z3_module.And(
            *(
                _translate_node(
                    item,
                    z3_module=z3_module,
                    domains=domains,
                    variables=variables,
                )
                for item in formula.operands
            )
        )
    if isinstance(formula, Or):
        return z3_module.Or(
            *(
                _translate_node(
                    item,
                    z3_module=z3_module,
                    domains=domains,
                    variables=variables,
                )
                for item in formula.operands
            )
        )
    if isinstance(formula, Implies):
        return z3_module.Implies(
            _translate_node(
                formula.antecedent,
                z3_module=z3_module,
                domains=domains,
                variables=variables,
            ),
            _translate_node(
                formula.consequent,
                z3_module=z3_module,
                domains=domains,
                variables=variables,
            ),
        )
    if isinstance(formula, Equivalence):
        return _translate_node(
            formula.left,
            z3_module=z3_module,
            domains=domains,
            variables=variables,
        ) == _translate_node(
            formula.right,
            z3_module=z3_module,
            domains=domains,
            variables=variables,
        )
    raise TypeError(f"unsupported validated formula node: {type(formula).__name__}")


def _translate(
    formula: Formula,
    universe: FiniteUniverse,
    z3_module: ModuleType,
) -> _Translation:
    domains = _domain_by_symbol(universe)
    _validate_binding(formula, domains)
    variables: dict[str, Any] = {}
    constraints: list[Any] = []
    for domain in universe.domains:
        if all(isinstance(value, bool) for value in domain.values):
            variable = z3_module.Bool(domain.symbol)
            variables[domain.symbol] = variable
            if len(domain.values) == 1:
                constraints.append(variable if domain.values[0] else z3_module.Not(variable))
        else:
            variable = z3_module.Int(domain.symbol)
            variables[domain.symbol] = variable
            constraints.append(
                z3_module.Or(*(variable == index for index in range(len(domain.values))))
            )
    expression = _translate_node(
        formula,
        z3_module=z3_module,
        domains=domains,
        variables=variables,
    )
    return _Translation(
        expression=expression,
        constraints=tuple(constraints),
        variables=variables,
    )


def _extract_assignment(
    *,
    model: Any,
    translation: _Translation,
    universe: FiniteUniverse,
    z3_module: ModuleType,
) -> Assignment:
    values: list[AssignmentValue] = []
    for domain in universe.domains:
        evaluated = model.eval(translation.variables[domain.symbol], model_completion=True)
        if all(isinstance(value, bool) for value in domain.values):
            value: bool | str = bool(z3_module.is_true(evaluated))
        else:
            index = int(evaluated.as_long())
            if index < 0 or index >= len(domain.values):
                raise ValueError(f"model enum value outside domain:{domain.symbol}")
            enum_value = domain.values[index]
            if not isinstance(enum_value, str):
                raise TypeError("validated enum domain unexpectedly contained a non-string")
            value = enum_value
        values.append(AssignmentValue(symbol=domain.symbol, value=value))
    return Assignment(values=tuple(values))


def _base_result(
    *,
    formula: Formula,
    universe: FiniteUniverse,
    backend_version: str | None,
    execution_status: BackendExecutionStatus,
    logical_result: LogicalResult | None,
    checker_verdict: CheckerVerdict,
    warrant_class: WarrantClass,
    witness: Assignment | None = None,
    witness_rechecked: bool | None = None,
    reason: str | None = None,
) -> Z3CheckResult:
    return Z3CheckResult(
        backend_version=backend_version,
        execution_status=execution_status,
        logical_result=logical_result,
        checker_verdict=checker_verdict,
        warrant_class=warrant_class,
        query_fingerprint=_query_fingerprint(formula, universe),
        universe_id=universe.id,
        universe_revision=universe.revision,
        universe_fingerprint=universe.fingerprint,
        witness=witness,
        witness_rechecked=witness_rechecked,
        reason=reason,
    )


def check_with_z3(
    formula: Formula,
    universe: FiniteUniverse,
    *,
    timeout_ms: int = 5_000,
    max_formula_nodes: int = 2_048,
) -> Z3CheckResult:
    """Check one finite formula while preserving Z3's limited trust boundary.

    Importing :mod:`rci.backends` never imports Z3.  If the optional extra is absent,
    the call returns a typed unsupported result.  Timeout and solver unknown remain
    distinct from UNSAT.  No result from this function authorizes promotion.
    """

    if timeout_ms < 1:
        raise ValueError("timeout_ms must be positive")
    if max_formula_nodes < 1:
        raise ValueError("max_formula_nodes must be positive")
    if _formula_node_count(formula) > max_formula_nodes:
        return _base_result(
            formula=formula,
            universe=universe,
            backend_version=None,
            execution_status=BackendExecutionStatus.UNSUPPORTED,
            logical_result=None,
            checker_verdict=CheckerVerdict.UNSUPPORTED,
            warrant_class=WarrantClass.NONE,
            reason="formula_node_budget_exceeded",
        )

    domains = _domain_by_symbol(universe)
    try:
        _validate_binding(formula, domains)
        z3_module = _load_z3()
    except _UnsupportedTranslation as error:
        return _base_result(
            formula=formula,
            universe=universe,
            backend_version=None,
            execution_status=BackendExecutionStatus.UNSUPPORTED,
            logical_result=None,
            checker_verdict=CheckerVerdict.UNSUPPORTED,
            warrant_class=WarrantClass.NONE,
            reason=str(error),
        )
    except _BackendLoadFailure as error:
        return _base_result(
            formula=formula,
            universe=universe,
            backend_version=None,
            execution_status=BackendExecutionStatus.FAILED,
            logical_result=None,
            checker_verdict=CheckerVerdict.FAILED,
            warrant_class=WarrantClass.NONE,
            reason=str(error),
        )

    backend_version: str | None = None
    try:
        backend_version = str(z3_module.get_version_string())
        translation = _translate(formula, universe, z3_module)
        solver = z3_module.Solver()
        solver.set(timeout=timeout_ms)
        solver.add(*translation.constraints)
        solver.add(translation.expression)
        result = solver.check()
        if result == z3_module.sat:
            witness = _extract_assignment(
                model=solver.model(),
                translation=translation,
                universe=universe,
                z3_module=z3_module,
            )
            witness_rechecked = evaluate(formula, witness.as_environment())
            return _base_result(
                formula=formula,
                universe=universe,
                backend_version=backend_version,
                execution_status=BackendExecutionStatus.COMPLETED,
                logical_result=LogicalResult.SAT,
                checker_verdict=(
                    CheckerVerdict.VALID if witness_rechecked else CheckerVerdict.INVALID
                ),
                warrant_class=WarrantClass.NONE,
                witness=witness,
                witness_rechecked=witness_rechecked,
                reason=None if witness_rechecked else "independent_witness_check_failed",
            )
        if result == z3_module.unsat:
            return _base_result(
                formula=formula,
                universe=universe,
                backend_version=backend_version,
                execution_status=BackendExecutionStatus.COMPLETED,
                logical_result=LogicalResult.UNSAT,
                checker_verdict=CheckerVerdict.VALID,
                warrant_class=WarrantClass.SOLVER_TRUSTED,
            )
        reason = str(solver.reason_unknown()) or "solver_returned_unknown"
        timed_out = "timeout" in reason.casefold()
        return _base_result(
            formula=formula,
            universe=universe,
            backend_version=backend_version,
            execution_status=(
                BackendExecutionStatus.TIMEOUT if timed_out else BackendExecutionStatus.COMPLETED
            ),
            logical_result=LogicalResult.UNKNOWN,
            checker_verdict=(CheckerVerdict.TIMEOUT if timed_out else CheckerVerdict.INDETERMINATE),
            warrant_class=WarrantClass.NONE,
            reason=reason,
        )
    except Exception as error:  # backend failures are evidence, not process control
        return _base_result(
            formula=formula,
            universe=universe,
            backend_version=backend_version,
            execution_status=BackendExecutionStatus.FAILED,
            logical_result=None,
            checker_verdict=CheckerVerdict.FAILED,
            warrant_class=WarrantClass.NONE,
            reason=f"{type(error).__name__}:{error}",
        )
