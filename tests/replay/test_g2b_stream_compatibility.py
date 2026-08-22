"""Frozen G2B stream extension over the sealed G1 replay corpus."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from rci.core.replay import replay
from rci.core.serialization import canonical_json_bytes, decode_event, encode_event
from rci.persistence import SQLiteEventStore

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures"


def test_archived_g2b_stream_replays_without_acquiring_g3_authority(tmp_path: Path) -> None:
    manifest = json.loads((FIXTURE_ROOT / "g2b" / "manifest.json").read_bytes())
    base_lines = (FIXTURE_ROOT / "g1" / "archived_vertical_slice.jsonl").read_bytes().splitlines()
    delta_bytes = (FIXTURE_ROOT / "g2b" / manifest["delta_fixture"]).read_bytes()
    assert sha256(delta_bytes).hexdigest() == manifest["delta_sha256"]
    stored_lines = (*base_lines[1:], *delta_bytes.splitlines())

    events = []
    for expected_sequence, line in enumerate(stored_lines, start=1):
        stored = json.loads(line)
        assert stored["sequence"] == expected_sequence
        event_bytes = canonical_json_bytes(stored["event"])
        assert sha256(event_bytes).hexdigest() == stored["event_digest"]
        event = decode_event(event_bytes)
        assert encode_event(event) == event_bytes
        events.append(event)

    assert [event.kind for event in events] == manifest["event_kinds"]
    state = replay(events)
    assert state.sequence == manifest["event_count"]
    assert state.representation_gaps[0].id == "gap:archived-g2b"
    assert state.binding_carrier_manifests == ()
    assert state.realized_history_derivations == ()
    assert state.compression_contracts == ()
    assert state.compression_validations == ()
    assert state.exact_compression_licenses == ()
    assert state.compression_applications == ()
    assert state.retained_state_views == ()

    expected_export = (
        b"\n".join(
            (
                canonical_json_bytes(
                    {
                        "format": "rci.event-stream.v1",
                        "stream_id": manifest["stream_id"],
                        "version": manifest["event_count"],
                    }
                ),
                *stored_lines,
            )
        )
        + b"\n"
    )
    store = SQLiteEventStore(tmp_path / "g2b-compatibility.sqlite3")
    store.append(manifest["stream_id"], 0, events)
    assert store.export_stream(manifest["stream_id"]) == expected_export
    assert store.rebuild_state(manifest["stream_id"], use_snapshot=False) == state
