"""Acceptance evidence for effect-free replay and deterministic export."""

from __future__ import annotations

from datetime import UTC, datetime

from rci import RCI


def test_replay_and_export_are_identical_across_process_boundaries(tmp_path: object) -> None:
    fixed = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    writer = RCI(tmp_path, clock=lambda: fixed)  # type: ignore[arg-type]
    writer.start("replayable")
    writer.step("replayable")
    expected = writer.submit_answer("replayable", b"\x00opaque\xff")
    first_export = writer.export("replayable")

    reader = RCI(tmp_path, clock=lambda: fixed)  # type: ignore[arg-type]
    assert reader.replay("replayable") == expected
    assert reader.inspect("replayable") == expected
    assert reader.export("replayable") == first_export
