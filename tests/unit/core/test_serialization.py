import json
from datetime import UTC, datetime

import pytest

from rci.core import ArtifactRef, InquiryContext, StartInquiry, decide, initial_state
from rci.core.serialization import canonical_json_bytes, decode_event, encode_event
from rci.core.upcasting import EVENT_UPCASTERS, UnsupportedEventSchemaVersion


def context() -> InquiryContext:
    return InquiryContext(
        binding_revision="binding-1",
        carrier_schema_ids=("carrier-1",),
        relation_schema_ids=("relation-1",),
        consequence_profile_id="consequence-1",
        protected_horizon_id="horizon-1",
        scope_id="scope-1",
        scope_fingerprint="2" * 64,
        catalog_manifest_digest="3" * 64,
        scheduler_policy_version="scheduler-1",
        warrant_policy_version="warrant-1",
        provenance_refs=("test",),
    )


def test_event_encoding_is_canonical_and_round_trips() -> None:
    command = StartInquiry(
        event_id="event-unicode",
        inquiry_id="inquiry-unicode",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        manifest_artifact=ArtifactRef(digest="1" * 64, size=0),
        policy_version="policy-1",
        context=context(),
    )
    event = decide(initial_state(), command)[0]
    encoded = encode_event(event)

    assert encoded == encode_event(event)
    assert decode_event(encoded) == event
    assert b" " not in encoded
    assert canonical_json_bytes({"text": "λ"}).decode("utf-8") == '{"text":"λ"}'
    assert canonical_json_bytes({"z": 1, "a": 2}) == b'{"a":2,"z":1}'


def test_unknown_event_schema_fails_closed() -> None:
    event = decide(
        initial_state(),
        StartInquiry(
            event_id="event-start",
            inquiry_id="inquiry-1",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
            manifest_artifact=ArtifactRef(digest="1" * 64, size=0),
            policy_version="policy-1",
            context=context(),
        ),
    )[0]
    payload = json.loads(encode_event(event))
    payload["schema_version"] = 2
    with pytest.raises(UnsupportedEventSchemaVersion, match="no reviewed upcaster"):
        decode_event(canonical_json_bytes(payload))

    with pytest.raises(TypeError):
        EVENT_UPCASTERS[("inquiry_started", 0)] = lambda item: item  # type: ignore[index]
