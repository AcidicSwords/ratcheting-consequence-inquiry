"""Frozen compatibility corpus from the sealed G1 event shapes."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from rci.core.replay import replay
from rci.core.serialization import canonical_json_bytes, decode_event, encode_event
from rci.persistence import SQLiteEventStore

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "g1"
G2A_STATE_COLLECTIONS = (
    "direct_use_routes",
    "reconstruction_routes",
    "consequence_evaluation_routes",
    "reacquisition_routes",
    "reacquisition_scaffolds",
    "recovery_protocols",
    "retention_packages",
    "retrieval_policies",
    "retrieval_queries",
    "retrieval_results",
    "reacquisition_requests",
    "reacquisition_inquiry_links",
    "recovery_observations",
    "recovery_comparisons",
)


def test_archived_g1_stream_decodes_replays_and_reexports_byte_identically(
    tmp_path: Path,
) -> None:
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_bytes())
    fixture = FIXTURE_ROOT / manifest["fixture"]
    fixture_bytes = fixture.read_bytes()
    assert sha256(fixture_bytes).hexdigest() == manifest["fixture_sha256"]

    lines = fixture_bytes.splitlines()
    header = json.loads(lines[0])
    assert canonical_json_bytes(header) == lines[0]
    assert header == {
        "format": "rci.event-stream.v1",
        "stream_id": manifest["stream_id"],
        "version": manifest["event_count"],
    }

    events = []
    for expected_sequence, line in enumerate(lines[1:], start=1):
        stored = json.loads(line)
        assert stored["sequence"] == expected_sequence
        event_bytes = canonical_json_bytes(stored["event"])
        assert sha256(event_bytes).hexdigest() == stored["event_digest"]
        event = decode_event(event_bytes)
        assert encode_event(event) == event_bytes
        events.append(event)

    assert [event.kind for event in events] == manifest["event_kinds"]
    state = replay(events)
    assert state.inquiry_id == manifest["stream_id"]
    assert state.sequence == manifest["event_count"]
    assert state.claims[0].payload == "archived g1 opaque answer"
    obligation_status = state.current_obligation_status(state.obligations[0].id)
    assert obligation_status is not None
    assert obligation_status.value == "satisfied"

    g1_projection = state.model_dump(
        mode="json",
        include=set(manifest["g1_state_fields"]),
    )
    assert (
        sha256(canonical_json_bytes(g1_projection)).hexdigest()
        == manifest["g1_state_projection_sha256"]
    )
    assert all(getattr(state, field_name) == () for field_name in G2A_STATE_COLLECTIONS)

    store = SQLiteEventStore(tmp_path / "compatibility.sqlite3")
    store.append(manifest["stream_id"], 0, events)
    assert store.export_stream(manifest["stream_id"]) == fixture_bytes
    assert store.rebuild_state(manifest["stream_id"], use_snapshot=False) == state
