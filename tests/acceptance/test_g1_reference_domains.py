from __future__ import annotations

from rci.bindings import circuit_demonstration, route_demonstration
from rci.formal import ExhaustiveVerdict


def test_eight_state_circuit_has_the_predetermined_findings() -> None:
    demonstration = circuit_demonstration()
    assert demonstration.expected_findings_hold
    main_witness = demonstration.main_power_necessity_attack.witness
    assert main_witness is not None
    assert main_witness.as_environment() == {
        "backup_power": True,
        "main_power": False,
        "switch_closed": True,
    }
    available_witness = demonstration.available_power_sufficiency_attack.witness
    assert available_witness is not None
    assert available_witness.as_environment()["switch_closed"] is False
    assert demonstration.switch_closed_necessity_attack.verdict is ExhaustiveVerdict.UNSAT
    assert demonstration.switch_closed_necessity_attack.assignments_checked == 8


def test_two_route_graph_proves_may_reach_but_refutes_prerequisite_control() -> None:
    demonstration = route_demonstration()
    assert demonstration.expected_findings_hold
    assert demonstration.routes == (
        ("start", "bypass", "target"),
        ("start", "gate", "target"),
    )
    assert demonstration.maximal_executions == (
        ("start", "bypass", "dead_end"),
        ("start", "bypass", "target"),
        ("start", "gate", "target"),
    )
    assert demonstration.may_reach
    assert not demonstration.must_reach
    assert not demonstration.must_pass_prerequisite
    assert not demonstration.control_promoted
