"""Typer command surface mirroring the public SDK lifecycle."""

from __future__ import annotations

import json
import os
import stat
import sys
import tomllib
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any

import typer

from rci.backlog import (
    BacklogEffectKind,
    BacklogFinding,
    BacklogItem,
    BacklogPolicy,
    EvidenceStatus,
    apply_effects,
    reconcile,
)
from rci.bindings import circuit_demonstration, route_demonstration
from rci.evaluation import evaluate_cases
from rci.persistence import DATABASE_SCHEMA_VERSION
from rci.questions.catalog import CATALOG_V0_3
from rci.sdk import RCI

app = typer.Typer(no_args_is_help=True, help="Ratcheting Consequence Inquiry")
contracts_app = typer.Typer(no_args_is_help=True, help="Question contract catalog")
evaluation_app = typer.Typer(no_args_is_help=True, help="Offline evaluation")
database_app = typer.Typer(no_args_is_help=True, help="Local event database")
backlog_app = typer.Typer(no_args_is_help=True, help="Governed backlog reconciliation")
app.add_typer(contracts_app, name="contracts")
app.add_typer(evaluation_app, name="eval")
app.add_typer(database_app, name="db")
app.add_typer(backlog_app, name="backlog")

_MAX_WORKSPACE_FILES = 10_000
_MAX_WORKSPACE_FILE_BYTES = 16 * 1024 * 1024
_MAX_WORKSPACE_BYTES = 64 * 1024 * 1024
_READ_CHUNK_BYTES = 1024 * 1024
_WINDOWS_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sdk(root: Path) -> RCI:
    return RCI(root)


def _workspace_digest(root: Path) -> str:
    """Hash governed workspace inputs without including mutable RCI runtime state."""

    workspace = Path(os.path.abspath(root))
    excluded_parts = {
        ".git",
        ".mypy_cache",
        ".pytest-tmp",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "artifacts",
        "build",
        "dist",
        "exports",
        "projections",
    }
    try:
        root_stat = os.lstat(workspace)
    except OSError as error:
        raise ValueError("workspace root is unavailable") from error
    if (
        stat.S_ISLNK(root_stat.st_mode)
        or bool(getattr(root_stat, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT)
        or not stat.S_ISDIR(root_stat.st_mode)
    ):
        raise ValueError("workspace root must be a real, non-reparse directory")

    files: list[tuple[Path, Path, os.stat_result]] = []
    pending: list[tuple[Path, Path]] = [(workspace, Path())]
    while pending:
        directory, parent_relative = pending.pop()
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(scanner, key=lambda item: item.name)
        except OSError as error:
            raise ValueError("workspace traversal failed closed") from error
        child_directories: list[tuple[Path, Path]] = []
        for entry in entries:
            relative = parent_relative / entry.name
            parts = relative.parts
            if any(part in excluded_parts or part.startswith(".pytest-tmp") for part in parts):
                continue
            if parts and parts[0] == ".rci" and relative.as_posix() != ".rci/config.toml":
                continue
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise ValueError("workspace entry changed during traversal") from error
            if entry.is_symlink() or bool(
                getattr(entry_stat, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT
            ):
                raise ValueError(f"workspace links and reparse points are forbidden: {relative}")
            entry_path = Path(entry.path)
            try:
                entry_stat = os.stat(entry_path, follow_symlinks=False)
            except OSError as error:
                raise ValueError("workspace entry changed during traversal") from error
            if stat.S_ISLNK(entry_stat.st_mode) or bool(
                getattr(entry_stat, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT
            ):
                raise ValueError(f"workspace links and reparse points are forbidden: {relative}")
            if stat.S_ISDIR(entry_stat.st_mode):
                child_directories.append((entry_path, relative))
            elif stat.S_ISREG(entry_stat.st_mode):
                if entry_stat.st_size > _MAX_WORKSPACE_FILE_BYTES:
                    raise ValueError(f"workspace file exceeds the per-file bound: {relative}")
                files.append((entry_path, relative, entry_stat))
                if len(files) > _MAX_WORKSPACE_FILES:
                    raise ValueError("workspace exceeds the governed file-count bound")
            else:
                raise ValueError(f"workspace contains a non-regular entry: {relative}")
        pending.extend(reversed(child_directories))

    digest = sha256()
    total_bytes = 0
    for path, relative, expected_stat in sorted(
        files,
        key=lambda item: item[1].as_posix(),
    ):
        relative_bytes = relative.as_posix().encode("utf-8")
        digest.update(len(relative_bytes).to_bytes(8, "big"))
        digest.update(relative_bytes)
        digest.update(expected_stat.st_size.to_bytes(8, "big"))
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError as error:
            raise ValueError(f"workspace file could not be opened safely: {relative}") from error
        try:
            opened_stat = os.fstat(descriptor)
            expected_identity = (
                expected_stat.st_dev,
                expected_stat.st_ino,
                expected_stat.st_mode,
                expected_stat.st_size,
                expected_stat.st_mtime_ns,
            )
            opened_identity = (
                opened_stat.st_dev,
                opened_stat.st_ino,
                opened_stat.st_mode,
                opened_stat.st_size,
                opened_stat.st_mtime_ns,
            )
            if not stat.S_ISREG(opened_stat.st_mode) or opened_identity != expected_identity:
                raise ValueError(f"workspace file changed before capture: {relative}")
            captured = 0
            while chunk := os.read(descriptor, _READ_CHUNK_BYTES):
                captured += len(chunk)
                total_bytes += len(chunk)
                if captured > _MAX_WORKSPACE_FILE_BYTES or total_bytes > _MAX_WORKSPACE_BYTES:
                    raise ValueError("workspace exceeds the governed byte bound")
                digest.update(chunk)
            closed_stat = os.fstat(descriptor)
            closed_identity = (
                closed_stat.st_dev,
                closed_stat.st_ino,
                closed_stat.st_mode,
                closed_stat.st_size,
                closed_stat.st_mtime_ns,
            )
            if captured != expected_stat.st_size or closed_identity != expected_identity:
                raise ValueError(f"workspace file changed during capture: {relative}")
        finally:
            os.close(descriptor)
    return digest.hexdigest()


def _read_bounded_regular_file(path: Path, *, max_bytes: int) -> bytes:
    """Capture one explicitly selected file without following a reparse boundary."""

    absolute = Path(os.path.abspath(path))
    try:
        expected = os.lstat(absolute)
    except OSError as error:
        raise ValueError("evidence file is unavailable") from error
    if (
        stat.S_ISLNK(expected.st_mode)
        or bool(getattr(expected, "st_file_attributes", 0) & _WINDOWS_REPARSE_POINT)
        or not stat.S_ISREG(expected.st_mode)
    ):
        raise ValueError("evidence file must be regular and cannot be a link or reparse point")
    if expected.st_size > max_bytes:
        raise ValueError("checked evidence exceeds the G1 1 MiB capture limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise ValueError("evidence file could not be opened safely") from error
    try:
        opened = os.fstat(descriptor)
        expected_identity = (
            expected.st_dev,
            expected.st_ino,
            expected.st_mode,
            expected.st_size,
            expected.st_mtime_ns,
        )
        opened_identity = (
            opened.st_dev,
            opened.st_ino,
            opened.st_mode,
            opened.st_size,
            opened.st_mtime_ns,
        )
        if not stat.S_ISREG(opened.st_mode) or opened_identity != expected_identity:
            raise ValueError("evidence file changed before capture")
        chunks: list[bytes] = []
        captured = 0
        while chunk := os.read(descriptor, min(_READ_CHUNK_BYTES, max_bytes + 1)):
            chunks.append(chunk)
            captured += len(chunk)
            if captured > max_bytes:
                raise ValueError("checked evidence exceeds the G1 1 MiB capture limit")
        closed = os.fstat(descriptor)
        closed_identity = (
            closed.st_dev,
            closed.st_ino,
            closed.st_mode,
            closed.st_size,
            closed.st_mtime_ns,
        )
        if captured != expected.st_size or closed_identity != expected_identity:
            raise ValueError("evidence file changed during capture")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


@app.command()
def start(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root", help="Repository root")] = Path("."),
) -> None:
    """Start or idempotently reopen an inquiry."""

    typer.echo(_json(_sdk(root).start(inquiry_id)))


@app.command()
def step(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Advance one deterministic orchestration step."""

    typer.echo(_json(_sdk(root).step(inquiry_id)))


@app.command("run")
def run_inquiry(
    inquiry_id: str,
    max_steps: Annotated[int, typer.Option("--max-steps", min=1, max=100)] = 100,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Run until input, satisfaction, Unknown, or the bounded step limit."""

    typer.echo(_json(_sdk(root).run(inquiry_id, max_steps=max_steps)))


@app.command()
def resume(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    typer.echo(_json(_sdk(root).resume(inquiry_id)))


@app.command()
def inspect(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    typer.echo(_json(_sdk(root).inspect(inquiry_id)))


@app.command()
def answer(
    inquiry_id: str,
    answer_text: Annotated[str, typer.Argument(help="Opaque L0 answer text")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    typer.echo(_json(_sdk(root).submit_answer(inquiry_id, answer_text)))


@app.command()
def replay(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    typer.echo(_json(_sdk(root).replay(inquiry_id)))


@app.command("export")
def export_inquiry(
    inquiry_id: str,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    payload = _sdk(root).export(inquiry_id)
    if output is None:
        sys.stdout.buffer.write(payload)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    typer.echo(str(output.resolve()))


@contracts_app.command("list")
def list_contracts(profile: str = "core-v1", version: str = "1.0.0") -> None:
    contracts = CATALOG_V0_3.schedulable_contracts(profile, version)
    typer.echo(
        _json(
            {
                "catalog_digest": CATALOG_V0_3.digest,
                "contracts": [contract.model_dump(mode="json") for contract in contracts],
            }
        )
    )


@evaluation_app.command("run")
def run_evaluation() -> None:
    """Run the deterministic built-in corpus (empty until fixtures are selected)."""

    typer.echo(_json(evaluate_cases(())))


@evaluation_app.command("references")
def run_reference_demonstrations() -> None:
    """Emit deterministic findings for the two G1 finite reference bindings."""

    circuit = circuit_demonstration()
    routes = route_demonstration()
    typer.echo(
        _json(
            {
                "circuit": circuit.model_dump(mode="json"),
                "route_graph": routes.model_dump(mode="json"),
                "all_expected_findings_hold": (
                    circuit.expected_findings_hold and routes.expected_findings_hold
                ),
            }
        )
    )


@database_app.command("info")
def database_info(
    inquiry_id: str | None = None,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    sdk = _sdk(root)
    payload: dict[str, object] = {
        "schema_version": DATABASE_SCHEMA_VERSION,
        "journal_mode": sdk.events.journal_mode(),
        "path": str(sdk.events.path),
    }
    if inquiry_id is not None:
        payload["stream_version"] = sdk.events.stream_version(inquiry_id)
    typer.echo(_json(payload))


@database_app.command("verify")
def database_verify(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    sdk = _sdk(root)
    state = sdk.replay(inquiry_id)
    typer.echo(_json({"verified": True, "sequence": state.sequence}))


def _backlog_policy(root: Path) -> BacklogPolicy:
    path = root.resolve() / ".rci" / "config.toml"
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    backlog = data.get("backlog", {})
    if backlog.get("mode") != "shadow" or backlog.get("automated_apply") is not False:
        raise typer.BadParameter("G1 requires shadow mode with automated_apply=false")
    allowed = frozenset(BacklogEffectKind(value) for value in backlog["allowed_effects"])
    proposal_only = frozenset(
        BacklogEffectKind(value) for value in backlog["proposal_only_effects"]
    )
    return BacklogPolicy(
        allowed_apply_effects=allowed,
        proposal_only_effects=proposal_only,
    )


def _load_backlog_items(
    sdk: RCI, inquiry_id: str
) -> tuple[tuple[BacklogItem, ...], frozenset[str]]:
    if sdk.events.stream_version(inquiry_id) == 0:
        return (), frozenset()
    state = sdk.inspect(inquiry_id)
    effects = list(state.backlog_effects)
    items: tuple[BacklogItem, ...] = ()
    historical_policy = BacklogPolicy()
    for effect in effects:
        items = apply_effects(items, (effect,), policy=historical_policy)
    return items, frozenset(effect.id for effect in effects)


@backlog_app.command("reconcile")
def reconcile_backlog(
    title: Annotated[str | None, typer.Option("--title")] = None,
    consequence: Annotated[str, typer.Option("--consequence")] = "repository-soundness",
    source: Annotated[str, typer.Option("--source")] = "manual",
    status: Annotated[EvidenceStatus, typer.Option("--status")] = EvidenceStatus.UNKNOWN,
    evidence_file: Annotated[Path | None, typer.Option("--evidence-file")] = None,
    priority: Annotated[int, typer.Option("--priority")] = 0,
    apply: Annotated[bool, typer.Option("--apply")] = False,
    inquiry_id: Annotated[str, typer.Option("--inquiry-id")] = "rci-backlog",
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Produce a golden shadow trace; explicit apply remains policy-bounded."""

    policy = _backlog_policy(root)
    database_path = root.resolve() / ".rci" / "state.sqlite3"
    sdk = _sdk(root) if database_path.exists() else None
    items: tuple[BacklogItem, ...]
    historical_effect_ids: frozenset[str]
    if sdk is None:
        items, historical_effect_ids = (), frozenset()
    else:
        items, historical_effect_ids = _load_backlog_items(sdk, inquiry_id)
    findings: tuple[BacklogFinding, ...] = ()
    if title is not None:
        checked_statuses = {
            EvidenceStatus.CHECKED_OPEN,
            EvidenceStatus.CHECKED_BLOCKED,
            EvidenceStatus.CHECKED_CLOSABLE,
        }
        evidence_digest: str | None = None
        if evidence_file is not None:
            workspace = Path(os.path.abspath(root))
            evidence_path = (
                Path(os.path.abspath(evidence_file))
                if evidence_file.is_absolute()
                else Path(os.path.abspath(workspace / evidence_file))
            )
            if not evidence_file.is_absolute() and os.path.commonpath(
                (workspace, evidence_path)
            ) != str(workspace):
                raise typer.BadParameter("relative evidence must remain inside the workspace")
            try:
                evidence_bytes = _read_bounded_regular_file(
                    evidence_path,
                    max_bytes=1_048_576,
                )
            except ValueError as error:
                raise typer.BadParameter(str(error)) from error
            evidence_digest = sha256(evidence_bytes).hexdigest()
        if status in checked_statuses and evidence_digest is None:
            raise typer.BadParameter("checked status requires --evidence-file")
        identity = sha256(f"{title}\x00{consequence}\x00{source}".encode()).hexdigest()[:16]
        findings = (
            BacklogFinding(
                id=f"finding-{identity}",
                title=title,
                protected_consequence=consequence,
                source=source,
                evidence_status=status,
                evidence_digest=evidence_digest,
                workspace_digest=_workspace_digest(root),
                priority=priority,
            ),
        )
    effects = reconcile(items, findings)
    applicable = tuple(effect for effect in effects if effect.kind in policy.allowed_apply_effects)
    novel_applicable = tuple(
        effect for effect in applicable if effect.id not in historical_effect_ids
    )
    if apply and novel_applicable:
        if sdk is None:
            sdk = _sdk(root)
        if sdk.events.stream_version(inquiry_id) == 0:
            sdk.start(inquiry_id)
        apply_effects(items, novel_applicable, policy=policy)
        sdk.append_local_effects(inquiry_id, novel_applicable)
    typer.echo(
        _json(
            {
                "mode": "applied" if apply and novel_applicable else "shadow",
                "apply_requested": apply,
                "effects": [effect.model_dump(mode="json") for effect in effects],
                "applied_effect_ids": [effect.id for effect in novel_applicable] if apply else [],
                "proposal_only_effect_ids": [
                    effect.id for effect in effects if effect.kind in policy.proposal_only_effects
                ],
            }
        )
    )


def main() -> None:
    app()


__all__ = ["app", "main"]
