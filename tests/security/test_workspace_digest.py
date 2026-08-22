"""The backlog workspace digest is bounded and never follows ambient links."""

from __future__ import annotations

from pathlib import Path

import pytest

import rci.cli as cli


def test_workspace_digest_is_deterministic_and_excludes_runtime_state(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("answer = 42\n", encoding="utf-8")
    (tmp_path / ".rci").mkdir()
    (tmp_path / ".rci" / "config.toml").write_text("schema_version = 1\n", encoding="utf-8")
    (tmp_path / ".rci" / "state.sqlite3").write_bytes(b"runtime-one")

    first = cli._workspace_digest(tmp_path)
    (tmp_path / ".rci" / "state.sqlite3").write_bytes(b"runtime-two")
    second = cli._workspace_digest(tmp_path)

    assert first == second
    (tmp_path / "src" / "module.py").write_text("answer = 43\n", encoding="utf-8")
    assert cli._workspace_digest(tmp_path) != first


def test_workspace_digest_fails_closed_on_a_link_outside_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("must not be captured", encoding="utf-8")
    link = workspace / "linked.txt"
    try:
        link.symlink_to(outside)
    except OSError as error:  # pragma: no cover - Windows host policy dependent
        pytest.skip(f"host cannot create a file symlink: {error}")

    with pytest.raises(ValueError, match="links and reparse points"):
        cli._workspace_digest(workspace)


def test_workspace_digest_enforces_file_and_size_bounds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized = tmp_path / "oversized.bin"
    oversized.write_bytes(b"12345")
    monkeypatch.setattr(cli, "_MAX_WORKSPACE_FILE_BYTES", 4)
    with pytest.raises(ValueError, match="per-file bound"):
        cli._workspace_digest(tmp_path)

    oversized.unlink()
    (tmp_path / "one.txt").write_text("1", encoding="utf-8")
    (tmp_path / "two.txt").write_text("2", encoding="utf-8")
    monkeypatch.setattr(cli, "_MAX_WORKSPACE_FILES", 1)
    with pytest.raises(ValueError, match="file-count bound"):
        cli._workspace_digest(tmp_path)
