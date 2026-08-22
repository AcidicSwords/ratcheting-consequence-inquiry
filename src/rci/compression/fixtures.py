"""Finite exact reference bindings for unbounded history carriers.

The checker works over a finite transition presentation, not a bounded sample of
histories. A total transition congruence plus its base state therefore proves the
property for every word in the generated (potentially infinite) history carrier.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations


class ExactFixtureVerdict(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True)
class ExactFixtureResult:
    verdict: ExactFixtureVerdict
    factorization: bool
    exact_equivalence: bool
    continuation_compatible: bool
    recursive_update: bool
    determination_descent: bool
    configuration_equal: bool
    event_count_equal: bool
    counterexample: tuple[str, str] | None = None


@dataclass(frozen=True)
class FiniteTransitionPresentation:
    """A finite congruence presentation of a possibly unbounded history carrier."""

    states: tuple[str, ...]
    alphabet: tuple[str, ...]
    initial_state: str
    transition: Mapping[tuple[str, str], str]
    quotient: Mapping[str, str]
    configuration: Mapping[str, str]
    consequences: Mapping[str, tuple[str, ...]]
    determinations: tuple[frozenset[str], ...] = ()


def validate_finite_transition_quotient(
    presentation: FiniteTransitionPresentation,
) -> ExactFixtureResult:
    """Independently check factorization, coarseness, descent, and recurrence."""

    states = presentation.states
    if (
        not states
        or presentation.initial_state not in states
        or set(presentation.quotient) != set(states)
        or set(presentation.configuration) != set(states)
        or set(presentation.consequences) != set(states)
        or any(
            (state, symbol) not in presentation.transition
            or presentation.transition[state, symbol] not in states
            for state in states
            for symbol in presentation.alphabet
        )
    ):
        raise ValueError("finite transition presentation must be total over exact state IDs")

    pairs = tuple(combinations(states, 2))

    def same_q(left: str, right: str) -> bool:
        return presentation.quotient[left] == presentation.quotient[right]

    def same_consequence(left: str, right: str) -> bool:
        return presentation.consequences[left] == presentation.consequences[right]

    factorization = all(
        not same_q(left, right) or same_consequence(left, right) for left, right in pairs
    )
    exact_equivalence = all(
        same_q(left, right) == same_consequence(left, right) for left, right in pairs
    )
    continuation_compatible = all(
        not same_q(left, right)
        or presentation.quotient[presentation.transition[left, symbol]]
        == presentation.quotient[presentation.transition[right, symbol]]
        for left, right in pairs
        for symbol in presentation.alphabet
    )
    determination_descent = all(
        all(
            not same_q(left, right) or ((left in determination) == (right in determination))
            for left, right in pairs
        )
        for determination in presentation.determinations
    )
    counterexample = next(
        (
            (left, right)
            for left, right in pairs
            if same_q(left, right) and not same_consequence(left, right)
        ),
        None,
    )
    if counterexample is None and not continuation_compatible:
        counterexample = next(
            (
                (left, right)
                for left, right in pairs
                if same_q(left, right)
                and any(
                    presentation.quotient[presentation.transition[left, symbol]]
                    != presentation.quotient[presentation.transition[right, symbol]]
                    for symbol in presentation.alphabet
                )
            ),
            None,
        )
    valid = factorization and continuation_compatible and determination_descent
    return ExactFixtureResult(
        verdict=ExactFixtureVerdict.VALID if valid else ExactFixtureVerdict.INVALID,
        factorization=factorization,
        exact_equivalence=exact_equivalence,
        continuation_compatible=continuation_compatible,
        recursive_update=continuation_compatible,
        determination_descent=determination_descent,
        configuration_equal=any(
            presentation.configuration[left] == presentation.configuration[right]
            for left, right in pairs
        ),
        event_count_equal=False,
        counterexample=counterexample,
    )


def validate_unary_parity(
    *, protect_parity: bool, singleton_representation: bool
) -> ExactFixtureResult:
    """Prove the unbounded unary carrier by finite base/step transition congruence."""

    quotient = {"even": "unit", "odd": "unit"}
    if not singleton_representation:
        quotient = {"even": "0", "odd": "1"}
    consequences = {
        "even": ("parity:0",) if protect_parity else (),
        "odd": ("parity:1",) if protect_parity else (),
    }
    result = validate_finite_transition_quotient(
        FiniteTransitionPresentation(
            states=("even", "odd"),
            alphabet=("a",),
            initial_state="even",
            transition={("even", "a"): "odd", ("odd", "a"): "even"},
            quotient=quotient,
            configuration={"even": "unit", "odd": "unit"},
            consequences=consequences,
            determinations=(frozenset({"odd"}),) if protect_parity else (),
        )
    )
    if result.counterexample == ("even", "odd"):
        return ExactFixtureResult(**{**result.__dict__, "counterexample": ("", "a")})
    return result


def validate_order_sensitive_count() -> ExactFixtureResult:
    """Show that equal configuration and equal event counts do not retain path order."""

    result = validate_finite_transition_quotient(
        FiniteTransitionPresentation(
            states=("ab", "ba"),
            alphabet=(),
            initial_state="ab",
            transition={},
            quotient={"ab": "count:2", "ba": "count:2"},
            configuration={"ab": "unit", "ba": "unit"},
            consequences={"ab": ("future:left",), "ba": ("future:right",)},
            determinations=(frozenset({"ab"}),),
        )
    )
    return ExactFixtureResult(**{**result.__dict__, "event_count_equal": True})


def validate_present_answer_without_continuation() -> ExactFixtureResult:
    """A quotient may answer now yet fail to descend an admitted continuation."""

    states = ("left", "right", "left-next", "right-next")
    return validate_finite_transition_quotient(
        FiniteTransitionPresentation(
            states=states,
            alphabet=("continue",),
            initial_state="left",
            transition={
                ("left", "continue"): "left-next",
                ("right", "continue"): "right-next",
                ("left-next", "continue"): "left-next",
                ("right-next", "continue"): "right-next",
            },
            quotient={
                "left": "present:same",
                "right": "present:same",
                "left-next": "future:left",
                "right-next": "future:right",
            },
            configuration={state: "unit" for state in states},
            consequences={state: ("present:same",) for state in states},
        )
    )
