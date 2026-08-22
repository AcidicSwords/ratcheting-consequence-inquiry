"""Canonical encoding for persisted records, fingerprints, and exports."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, TypeAdapter

from rci.core.events import DomainEvent
from rci.core.state import InquiryState
from rci.core.upcasting import upcast_event_payload

_EVENT_ADAPTER: TypeAdapter[DomainEvent] = TypeAdapter(DomainEvent)


def canonical_json_bytes(value: BaseModel | dict[str, Any] | list[Any]) -> bytes:
    """Serialize JSON-compatible data without whitespace or key-order ambiguity."""

    material: Any = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        material,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def encode_event(event: DomainEvent) -> bytes:
    return canonical_json_bytes(event)


def decode_event(data: bytes) -> DomainEvent:
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError("persisted event must be a JSON object")
    upcast_payload = upcast_event_payload(payload)
    return _EVENT_ADAPTER.validate_json(canonical_json_bytes(upcast_payload), strict=True)


def encode_state(state: InquiryState) -> bytes:
    return canonical_json_bytes(state)


def decode_state(data: bytes) -> InquiryState:
    return InquiryState.model_validate_json(data, strict=True)
