from pathlib import Path

import pytest

from rci.core import CapturedPayload
from rci.persistence import ArtifactIntegrityError, ArtifactStore


def test_cas_preserves_exact_bytes_and_deduplicates(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")
    line_feed = store.put_bytes(b"answer\n", media_type="text/plain")
    carriage_return = store.put_bytes(b"answer\r\n", media_type="text/plain")

    assert line_feed.digest != carriage_return.digest
    assert store.put_bytes(b"answer\n").digest == line_feed.digest
    assert store.get_bytes(line_feed) == b"answer\n"


def test_cas_rejects_coercion_and_detects_tampering(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")
    with pytest.raises(TypeError):
        store.put_bytes(bytearray(b"not-exact"))  # type: ignore[arg-type]

    artifact = store.put_bytes(b"original")
    store.path_for(artifact).write_bytes(b"tampered")
    with pytest.raises(ArtifactIntegrityError):
        store.get_bytes(artifact)


def test_null_empty_string_zero_false_and_empty_bytes_remain_distinct(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")
    raw_values = {
        "empty_bytes": b"",
        "json_null": b"null",
        "empty_string": b'""',
        "zero": b"0",
        "false": b"false",
    }
    references = {name: store.put_bytes(value) for name, value in raw_values.items()}

    assert len({reference.digest for reference in references.values()}) == len(raw_values)
    assert {
        name: store.get_bytes(reference) for name, reference in references.items()
    } == raw_values
    native_null = CapturedPayload(kind="null")
    encoded_json_null = CapturedPayload(kind="bytes", artifact=references["json_null"])
    assert native_null != encoded_json_null
