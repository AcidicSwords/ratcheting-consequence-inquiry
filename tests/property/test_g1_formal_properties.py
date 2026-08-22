from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from rci.formal import Equivalence, Not, Symbol, evaluate


@given(st.booleans())
def test_double_negation_and_self_equivalence(value: bool) -> None:
    symbol = Symbol(name="p")
    environment = {"p": value}
    assert evaluate(Not(operand=Not(operand=symbol)), environment) == value
    assert evaluate(Equivalence(left=symbol, right=symbol), environment)
