"""Pure, code-owned event upcaster registry reserved for future schema versions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

type EventPayload = dict[str, Any]
type EventUpcaster = Callable[[EventPayload], EventPayload]
type UpcasterKey = tuple[str, int]

# G1 is greenfield, so there are deliberately no invented legacy migrations.
# Future reviewed migrations are pure code keyed by exact kind and source version;
# runtime configuration cannot extend this trust boundary.
EVENT_UPCASTERS: Mapping[UpcasterKey, EventUpcaster] = MappingProxyType({})


class UnsupportedEventSchemaVersion(ValueError):
    """No reviewed pure migration exists for a persisted event version."""


def upcast_event_payload(payload: EventPayload, *, current_version: int = 1) -> EventPayload:
    """Return a current payload or fail closed without fabricating semantics."""

    current = dict(payload)
    seen: set[UpcasterKey] = set()
    while True:
        kind = current.get("kind")
        version = current.get("schema_version")
        if not isinstance(kind, str) or type(version) is not int:
            raise UnsupportedEventSchemaVersion("event kind and integer version are required")
        if version == current_version:
            return current
        key = (kind, version)
        if key in seen:
            raise UnsupportedEventSchemaVersion("event upcaster cycle detected")
        seen.add(key)
        upcaster = EVENT_UPCASTERS.get(key)
        if upcaster is None:
            raise UnsupportedEventSchemaVersion(
                f"no reviewed upcaster for {kind!r} schema version {version}"
            )
        migrated = upcaster(dict(current))
        if migrated is current or not isinstance(migrated, dict):
            raise UnsupportedEventSchemaVersion("event upcaster must return a new mapping")
        current = migrated


__all__ = [
    "EVENT_UPCASTERS",
    "EventPayload",
    "EventUpcaster",
    "UnsupportedEventSchemaVersion",
    "upcast_event_payload",
]
