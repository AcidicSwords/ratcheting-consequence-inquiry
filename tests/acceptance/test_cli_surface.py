"""The documented CLI groups are discoverable from the installed entry point."""

import json
from pathlib import Path

from typer.testing import CliRunner

from rci import RCI
from rci.cli import app


def test_root_and_governance_command_groups_are_discoverable() -> None:
    runner = CliRunner()
    root_help = runner.invoke(app, ["--help"])

    assert root_help.exit_code == 0
    for command in (
        "start",
        "step",
        "run",
        "resume",
        "inspect",
        "answer",
        "replay",
        "export",
        "contracts",
        "eval",
        "db",
        "backlog",
        "memory",
        "recovery",
        "compression",
    ):
        assert command in root_help.stdout

    backlog_help = runner.invoke(app, ["backlog", "--help"])
    assert backlog_help.exit_code == 0
    assert "reconcile" in backlog_help.stdout

    memory_help = runner.invoke(app, ["memory", "--help"])
    recovery_help = runner.invoke(app, ["recovery", "--help"])
    assert memory_help.exit_code == recovery_help.exit_code == 0
    assert "retrieve" in memory_help.stdout
    for command in ("start", "inspect", "compare"):
        assert command in recovery_help.stdout

    compression_help = runner.invoke(app, ["compression", "--help"])
    assert compression_help.exit_code == 0
    for command in ("fixture", "inspect"):
        assert command in compression_help.stdout
    parity = runner.invoke(app, ["compression", "fixture", "unary-parity"])
    assert parity.exit_code == 0
    assert '"verdict":"valid"' in parity.stdout

    references = runner.invoke(app, ["eval", "references"])
    assert references.exit_code == 0
    assert '"all_expected_findings_hold":true' in references.stdout


def test_cli_and_sdk_share_the_complete_offline_lifecycle(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    export_path = tmp_path / "inquiry.jsonl"
    runner = CliRunner()

    started = runner.invoke(app, ["start", "cli-parity", "--root", str(root)])
    planned = runner.invoke(app, ["step", "cli-parity", "--root", str(root)])
    paused = runner.invoke(app, ["run", "cli-parity", "--root", str(root)])
    answered = runner.invoke(
        app,
        ["answer", "cli-parity", "opaque answer", "--root", str(root)],
    )
    inspected = runner.invoke(app, ["inspect", "cli-parity", "--root", str(root)])
    resumed = runner.invoke(app, ["resume", "cli-parity", "--root", str(root)])
    replayed = runner.invoke(app, ["replay", "cli-parity", "--root", str(root)])
    stopped = runner.invoke(app, ["step", "cli-parity", "--root", str(root)])
    exported = runner.invoke(
        app,
        [
            "export",
            "cli-parity",
            "--output",
            str(export_path),
            "--root",
            str(root),
        ],
    )

    for result in (
        started,
        planned,
        paused,
        answered,
        inspected,
        resumed,
        replayed,
        stopped,
        exported,
    ):
        assert result.exit_code == 0, result.output
    assert json.loads(started.stdout)["sequence"] == 2
    assert json.loads(planned.stdout)["status"] == "needs_input"
    assert json.loads(paused.stdout)["request_id"] == json.loads(planned.stdout)["request_id"]
    assert json.loads(answered.stdout)["sequence"] == 11
    assert json.loads(inspected.stdout) == json.loads(resumed.stdout) == json.loads(replayed.stdout)
    assert json.loads(stopped.stdout)["status"] == "satisfied"
    assert export_path.read_bytes() == RCI(root).export("cli-parity")
