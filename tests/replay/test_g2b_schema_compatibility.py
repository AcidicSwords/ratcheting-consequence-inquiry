from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import get_args

from rci.core.events import DomainEvent

FIXTURE = Path(__file__).parents[1] / "fixtures" / "compat" / "g2b-event-schema-manifest.json"


def test_every_sealed_g1_g2_event_schema_matches_the_a5ac134_manifest() -> None:
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert manifest["anchor"] == "a5ac134981494cd126261117828140e7151eaf39"
    event_union = get_args(DomainEvent)[0]
    current: dict[str, str] = {}
    for event_class in get_args(event_union):
        kind = event_class.model_fields["kind"].default
        schema = json.dumps(
            event_class.model_json_schema(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        current[kind] = hashlib.sha256(schema).hexdigest()
        assert event_class.model_fields["schema_version"].default == 1

    # G3 may add event kinds, but every event sealed at the G2B anchor is immutable.
    assert manifest["events"].items() <= current.items()
