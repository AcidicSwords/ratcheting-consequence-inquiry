"""The public run boundary consumes, and is bounded by, its step limit."""

from __future__ import annotations

import pytest

from rci.sdk import RCI, StepResult


class _AdvancingHarness(RCI):
    def __init__(self) -> None:
        self.calls = 0

    def step(self, inquiry_id: str) -> StepResult:
        self.calls += 1
        return StepResult(
            inquiry_id=inquiry_id,
            status="satisfied" if self.calls == 3 else "active",
            sequence=self.calls,
        )


def test_run_advances_until_a_terminal_boundary() -> None:
    harness = _AdvancingHarness()
    result = harness.run("bounded-run", max_steps=3)

    assert result.status == "satisfied"
    assert harness.calls == 3


@pytest.mark.parametrize("invalid", (0, 101))
def test_run_rejects_limits_outside_the_constitutional_budget(invalid: int) -> None:
    with pytest.raises(ValueError, match="constitutional limit"):
        _AdvancingHarness().run("bounded-run", max_steps=invalid)
