"""Eight-state reference circuit used by Phase 2 acceptance tests."""

from __future__ import annotations

from itertools import product

from rci.claims.models import FrozenModel
from rci.formal.ast import And, Or, Symbol
from rci.formal.exhaustive import (
    AttackProfile,
    ExhaustiveResult,
    ExhaustiveVerdict,
    FiniteDomain,
    FiniteUniverse,
    implication_attack,
)


class CircuitState(FrozenModel):
    main_power: bool
    backup_power: bool
    switch_closed: bool
    lamp_on: bool


class CircuitDemonstration(FrozenModel):
    states: tuple[CircuitState, ...]
    main_power_necessity_attack: ExhaustiveResult
    available_power_sufficiency_attack: ExhaustiveResult
    switch_closed_necessity_attack: ExhaustiveResult

    @property
    def expected_findings_hold(self) -> bool:
        return (
            len(self.states) == 8
            and self.main_power_necessity_attack.verdict is ExhaustiveVerdict.SAT
            and self.available_power_sufficiency_attack.verdict is ExhaustiveVerdict.SAT
            and self.switch_closed_necessity_attack.verdict is ExhaustiveVerdict.UNSAT
            and self.switch_closed_necessity_attack.hard_unsat_eligible
        )


def circuit_states() -> tuple[CircuitState, ...]:
    return tuple(
        CircuitState(
            backup_power=backup_power,
            main_power=main_power,
            switch_closed=switch_closed,
            lamp_on=switch_closed and (main_power or backup_power),
        )
        for backup_power, main_power, switch_closed in product((False, True), repeat=3)
    )


def circuit_universe() -> FiniteUniverse:
    return FiniteUniverse(
        id="reference-circuit",
        revision="1",
        domains=(
            FiniteDomain(symbol="backup_power", values=(False, True)),
            FiniteDomain(symbol="main_power", values=(False, True)),
            FiniteDomain(symbol="switch_closed", values=(False, True)),
        ),
        closed_world=True,
    )


def circuit_demonstration() -> CircuitDemonstration:
    main_power = Symbol(name="main_power")
    backup_power = Symbol(name="backup_power")
    switch_closed = Symbol(name="switch_closed")
    available_power = Or(operands=(main_power, backup_power))
    lamp_on = And(operands=(switch_closed, available_power))
    universe = circuit_universe()
    return CircuitDemonstration(
        states=circuit_states(),
        main_power_necessity_attack=implication_attack(
            profile=AttackProfile.NECESSITY,
            proposed_condition=main_power,
            protected_consequence=lamp_on,
            universe=universe,
        ),
        available_power_sufficiency_attack=implication_attack(
            profile=AttackProfile.SUFFICIENCY,
            proposed_condition=available_power,
            protected_consequence=lamp_on,
            universe=universe,
        ),
        switch_closed_necessity_attack=implication_attack(
            profile=AttackProfile.NECESSITY,
            proposed_condition=switch_closed,
            protected_consequence=lamp_on,
            universe=universe,
        ),
    )
