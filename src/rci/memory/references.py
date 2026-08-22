"""Canonical fingerprints and fail-closed resolution for owned memory references."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rci.claims.models import content_fingerprint
from rci.memory.models import MemoryOwner, OwnedMemoryRef, OwnedRecordType


def owned_record_content_fingerprint(
    *,
    owner: MemoryOwner,
    record_type: OwnedRecordType,
    record_schema_version: int,
    record: Any,
) -> str:
    """Hash an exact record under an owner/type/schema-separated namespace."""

    if record_schema_version < 1:
        raise ValueError("owned record schema versions must be positive")
    return content_fingerprint(
        (f"rci.owned-memory-record.v1/{owner.value}/{record_type.value}/v{record_schema_version}"),
        record,
    )


def make_owned_memory_ref(
    *,
    owner: MemoryOwner,
    record_type: OwnedRecordType,
    record_id: str,
    record_schema_version: int,
    record: Any,
) -> OwnedMemoryRef:
    """Create an exact reference; identity generation remains the caller's concern."""

    return OwnedMemoryRef(
        owner=owner,
        record_type=record_type,
        record_id=record_id,
        record_schema_version=record_schema_version,
        content_fingerprint=owned_record_content_fingerprint(
            owner=owner,
            record_type=record_type,
            record_schema_version=record_schema_version,
            record=record,
        ),
    )


def validate_owned_memory_ref(reference: OwnedMemoryRef, record: Any) -> tuple[bool, str]:
    """Validate exact identity (when exposed) and content without trusting a projection."""

    exposed_identity = getattr(record, "id", None)
    if exposed_identity is None:
        exposed_identity = getattr(record, "fingerprint", None)
    if exposed_identity is not None and exposed_identity != reference.record_id:
        return False, "owned record identity does not match the reference"
    actual = owned_record_content_fingerprint(
        owner=reference.owner,
        record_type=reference.record_type,
        record_schema_version=reference.record_schema_version,
        record=record,
    )
    if actual != reference.content_fingerprint:
        return False, "owned record content fingerprint does not match the reference"
    return True, "owned record identity, type, schema, owner, and content match exactly"


def resolve_owned_memory_ref(
    reference: OwnedMemoryRef,
    *,
    owned_records: Mapping[str, Any],
) -> tuple[bool, str]:
    """Resolve by canonical typed key, then perform exact content validation."""

    record = owned_records.get(reference.key)
    if record is None:
        return False, "owned memory reference does not resolve"
    return validate_owned_memory_ref(reference, record)
