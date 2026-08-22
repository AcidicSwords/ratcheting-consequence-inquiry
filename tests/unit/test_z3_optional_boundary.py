from __future__ import annotations

from types import ModuleType

import pytest

import rci.backends.z3_backend as z3_backend
from rci.backends import BackendExecutionStatus, check_with_z3
from rci.formal import EnumEquals, FiniteDomain, FiniteUniverse, Not, Symbol
from rci.warrant import CheckerVerdict, WarrantClass


def _boolean_universe() -> FiniteUniverse:
    return FiniteUniverse(
        id="universe:boolean",
        revision="1",
        domains=(FiniteDomain(symbol="p", values=(False, True)),),
        closed_world=True,
    )


def test_import_boundary_reports_missing_optional_extra_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(name: str) -> ModuleType:
        assert name == "z3"
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(z3_backend, "import_module", unavailable)
    result = check_with_z3(Symbol(name="p"), _boolean_universe())
    assert result.execution_status is BackendExecutionStatus.UNSUPPORTED
    assert result.logical_result is None
    assert result.checker_verdict is CheckerVerdict.UNSUPPORTED
    assert result.warrant_class is WarrantClass.NONE
    assert result.reason == "z3_extra_not_installed"
    assert not result.promotion_authorized


def test_mistyped_finite_binding_fails_closed_before_loading_z3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_import(name: str) -> ModuleType:
        raise AssertionError(f"unexpected optional import: {name}")

    monkeypatch.setattr(z3_backend, "import_module", unexpected_import)
    result = check_with_z3(
        EnumEquals(symbol="p", value="true"),
        _boolean_universe(),
    )
    assert result.execution_status is BackendExecutionStatus.UNSUPPORTED
    assert result.reason == "enum_equality_bound_to_boolean:p"


def test_broken_optional_backend_load_is_a_typed_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_load(name: str) -> ModuleType:
        assert name == "z3"
        raise OSError("native library unavailable")

    monkeypatch.setattr(z3_backend, "import_module", broken_load)
    result = check_with_z3(Symbol(name="p"), _boolean_universe())
    assert result.execution_status is BackendExecutionStatus.FAILED
    assert result.logical_result is None
    assert result.checker_verdict is CheckerVerdict.FAILED
    assert result.warrant_class is WarrantClass.NONE
    assert result.reason == "z3_import_failed:OSError:native library unavailable"


def test_formula_budget_is_checked_without_loading_z3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_import(name: str) -> ModuleType:
        raise AssertionError(f"unexpected optional import: {name}")

    monkeypatch.setattr(z3_backend, "import_module", unexpected_import)
    result = check_with_z3(
        Not(operand=Symbol(name="p")),
        _boolean_universe(),
        max_formula_nodes=1,
    )
    assert result.execution_status is BackendExecutionStatus.UNSUPPORTED
    assert result.reason == "formula_node_budget_exceeded"
