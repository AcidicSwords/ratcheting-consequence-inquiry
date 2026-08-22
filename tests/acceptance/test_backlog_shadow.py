"""Golden governed-backlog acceptance trace."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from rci.cli import app

CONFIG = """\
schema_version = 1

[backlog]
mode = "shadow"
automated_apply = false
automated_close = false
allowed_effects = ["create", "dedupe", "rank", "block"]
proposal_only_effects = ["close"]

[evidence]
network = false
timeout_seconds = 60
max_output_bytes = 1048576
capture_temporary_workspace = true

[authority]
source_writes = false
git_mutation = false
policy_edits = false
packaging = false
deployment = false
release = false
"""


def _root(tmp_path: Path) -> Path:
    runtime = tmp_path / ".rci"
    runtime.mkdir()
    (runtime / "config.toml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "evidence.txt").write_text("checked evidence\n", encoding="utf-8")
    return tmp_path


def test_shadow_reconciliation_is_deterministic_and_does_not_create_runtime_state(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    runner = CliRunner()
    args = [
        "backlog",
        "reconcile",
        "--title",
        "Preserve replay determinism",
        "--status",
        "checked_open",
        "--evidence-file",
        "evidence.txt",
        "--root",
        str(root),
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == second.exit_code == 0
    assert first.stdout == second.stdout
    assert not (root / ".rci" / "state.sqlite3").exists()
    trace = json.loads(first.stdout)
    assert trace["mode"] == "shadow"
    assert trace["applied_effect_ids"] == []
    assert [effect["kind"] for effect in trace["effects"]] == ["create", "rank"]


def test_apply_is_allowlisted_and_close_remains_proposal_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "backlog",
            "reconcile",
            "--title",
            "Candidate closure",
            "--status",
            "checked_closable",
            "--evidence-file",
            "evidence.txt",
            "--apply",
            "--root",
            str(root),
        ],
    )

    assert result.exit_code == 0, result.output
    trace = json.loads(result.stdout)
    effects = {effect["id"]: effect for effect in trace["effects"]}
    proposed_close_ids = {
        effect_id for effect_id, effect in effects.items() if effect["kind"] == "close"
    }
    assert proposed_close_ids
    assert proposed_close_ids == set(trace["proposal_only_effect_ids"])
    assert proposed_close_ids.isdisjoint(trace["applied_effect_ids"])
    assert {effects[item]["kind"] for item in trace["applied_effect_ids"]} == {
        "create",
        "rank",
    }
    assert (root / ".rci" / "state.sqlite3").exists()


def test_checked_status_cannot_be_asserted_without_captured_evidence(tmp_path: Path) -> None:
    root = _root(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "backlog",
            "reconcile",
            "--title",
            "Unsupported assertion",
            "--status",
            "checked_open",
            "--root",
            str(root),
        ],
    )

    assert result.exit_code != 0
    # Rich wraps error panels to the detected terminal width.  Keep the
    # behavioral assertion stable in narrow hosted-CI consoles.
    assert "checked status" in result.output
    assert "requires" in result.output
    assert "--evidence-file" in result.output
    assert not (root / ".rci" / "state.sqlite3").exists()


def test_repeated_apply_appends_only_the_novel_deduplication_effect(tmp_path: Path) -> None:
    root = _root(tmp_path)
    runner = CliRunner()
    args = [
        "backlog",
        "reconcile",
        "--title",
        "Stable finding",
        "--status",
        "checked_open",
        "--evidence-file",
        "evidence.txt",
        "--apply",
        "--root",
        str(root),
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    third = runner.invoke(app, args)

    assert first.exit_code == second.exit_code == third.exit_code == 0
    first_trace = json.loads(first.stdout)
    second_trace = json.loads(second.stdout)
    third_trace = json.loads(third.stdout)
    assert {effect["kind"] for effect in first_trace["effects"]} == {"create", "rank"}
    assert {effect["kind"] for effect in second_trace["effects"]} == {"dedupe", "rank"}
    assert len(second_trace["applied_effect_ids"]) == 1
    assert third_trace["applied_effect_ids"] == []
    assert third_trace["mode"] == "shadow"
    assert third_trace["apply_requested"] is True
