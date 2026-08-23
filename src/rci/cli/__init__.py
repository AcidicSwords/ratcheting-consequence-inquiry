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
from rci.compression import validate_order_sensitive_count, validate_unary_parity
from rci.evaluation import evaluate_cases
from rci.learning import (
    MemoryPatchCandidate,
    ProbeAdmissionDecision,
    ProbeEvaluation,
    ReconsolidationLink,
)
from rci.memory import MemoryOwner, OwnedRecordType, RecoveryBranch
from rci.persistence import DATABASE_SCHEMA_VERSION
from rci.project import (
    CandidateEnvironmentManifest,
    CapabilityLimitation,
    CapabilitySuccessorCandidate,
    DevelopmentEvidence,
    GoalAdmissionDecision,
    GoalSynthesisUnknown,
    ImplementationGoalContract,
    IndependentReview,
    MethodAdmissionDecision,
    MethodBindingCandidate,
    ProjectAnchor,
    ProjectSuccessorDecision,
    PromotionDecision,
    QuestionContractCandidate,
    QuestionRepertoireDecision,
    RecursiveCycleCheckpoint,
    RecursiveStopDisposition,
    derive_capability_frontier,
)
from rci.questions.catalog import CATALOG_V0_4
from rci.sdk import RCI
from rci.warrant import CheckReference

app = typer.Typer(no_args_is_help=True, help="Ratcheting Consequence Inquiry")
contracts_app = typer.Typer(no_args_is_help=True, help="Question contract catalog")
evaluation_app = typer.Typer(no_args_is_help=True, help="Offline evaluation")
database_app = typer.Typer(no_args_is_help=True, help="Local event database")
backlog_app = typer.Typer(no_args_is_help=True, help="Governed backlog reconciliation")
memory_app = typer.Typer(no_args_is_help=True, help="Deterministic structural memory")
recovery_app = typer.Typer(no_args_is_help=True, help="Measured reacquisition recovery")
field_app = typer.Typer(no_args_is_help=True, help="Conservative semantic-field diagnostics")
probes_app = typer.Typer(no_args_is_help=True, help="Governed learned-probe evaluation")
compression_app = typer.Typer(no_args_is_help=True, help="Exact retained-state contracts")
project_app = typer.Typer(no_args_is_help=True, help="Recursive repository inquiry")
app.add_typer(contracts_app, name="contracts")
app.add_typer(evaluation_app, name="eval")
app.add_typer(database_app, name="db")
app.add_typer(backlog_app, name="backlog")
app.add_typer(memory_app, name="memory")
app.add_typer(recovery_app, name="recovery")
app.add_typer(field_app, name="field")
app.add_typer(probes_app, name="probes")
app.add_typer(compression_app, name="compression")
app.add_typer(project_app, name="project")

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
    contracts = CATALOG_V0_4.schedulable_contracts(profile, version)
    typer.echo(
        _json(
            {
                "catalog_digest": CATALOG_V0_4.digest,
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


@memory_app.command("retrieve")
def retrieve_memory(
    inquiry_id: str,
    query_id: Annotated[str, typer.Option("--query-id")],
    result_id: Annotated[str, typer.Option("--result-id")],
    cue: Annotated[list[str] | None, typer.Option("--cue")] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
    owner: Annotated[list[MemoryOwner] | None, typer.Option("--owner")] = None,
    record_type: Annotated[
        list[OwnedRecordType] | None,
        typer.Option("--record-type"),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Persist one exact structural retrieval and emit canonical JSON."""

    result = _sdk(root).retrieve(
        inquiry_id,
        query_id=query_id,
        result_id=result_id,
        owners=tuple(sorted(set(owner or ()), key=lambda item: item.value)),
        record_types=tuple(sorted(set(record_type or ()), key=lambda item: item.value)),
        cue_ids=tuple(cue or ()),
        tag_ids=tuple(tag or ()),
        limit=limit,
    )
    typer.echo(_json(result))


@memory_app.command("consolidate")
def consolidate_memory(
    inquiry_id: str,
    checkpoint_id: Annotated[str, typer.Option("--checkpoint-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Persist one deterministic consolidation source checkpoint."""

    checkpoint = _sdk(root).consolidation_checkpoint(
        inquiry_id,
        checkpoint_id=checkpoint_id,
    )
    typer.echo(_json(checkpoint))


@memory_app.command("patch")
def record_memory_patch(
    inquiry_id: str,
    candidate: Annotated[Path, typer.Option("--candidate")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record a validated inert memory-patch candidate from strict JSON."""

    patch = MemoryPatchCandidate.model_validate_json(candidate.read_bytes(), strict=True)
    typer.echo(_json(_sdk(root).record_memory_patch(inquiry_id, patch)))


@memory_app.command("reconsolidate")
def record_reconsolidation(
    inquiry_id: str,
    link: Annotated[Path, typer.Option("--link")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record an already checked immutable predecessor/successor repair link."""

    record = ReconsolidationLink.model_validate_json(link.read_bytes(), strict=True)
    typer.echo(_json(_sdk(root).record_reconsolidation_link(inquiry_id, record)))


@field_app.command("evaluate")
def evaluate_field(
    inquiry_id: str,
    evaluation_id: Annotated[str, typer.Option("--evaluation-id")],
    probe_fingerprint: Annotated[str, typer.Option("--probe-fingerprint")],
    safety: Annotated[list[str] | None, typer.Option("--safety")] = None,
    exception: Annotated[list[str] | None, typer.Option("--exception")] = None,
    dependency: Annotated[list[str] | None, typer.Option("--dependency")] = None,
    retrieval: Annotated[list[str] | None, typer.Option("--retrieval")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Derive, validate, and persist one bounded conservative semantic field."""

    evaluation = _sdk(root).evaluate_semantic_field(
        inquiry_id,
        evaluation_id=evaluation_id,
        probe_fingerprint=probe_fingerprint,
        safety_structure_ids=tuple(safety or ()),
        exception_structure_ids=tuple(exception or ()),
        dependency_structure_ids=tuple(dependency or ()),
        retrieval_structure_ids=tuple(retrieval or ()),
    )
    typer.echo(_json(evaluation))


@probes_app.command("evaluate")
def record_probe_evaluation(
    inquiry_id: str,
    evaluation: Annotated[Path, typer.Option("--evaluation")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record an independently checked finite holdout evaluation."""

    record = ProbeEvaluation.model_validate_json(evaluation.read_bytes(), strict=True)
    typer.echo(_json(_sdk(root).record_probe_evaluation(inquiry_id, record)))


@probes_app.command("admit")
def admit_learned_probe(
    inquiry_id: str,
    decision: Annotated[Path, typer.Option("--decision")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Apply the fixed controller policy to a recorded learned-probe decision."""

    record = ProbeAdmissionDecision.model_validate_json(decision.read_bytes(), strict=True)
    typer.echo(_json(_sdk(root).record_probe_admission(inquiry_id, record)))


@recovery_app.command("start")
def start_recovery(
    parent_inquiry_id: str,
    child_inquiry_id: Annotated[str, typer.Option("--child-inquiry-id")],
    request_id: Annotated[str, typer.Option("--request-id")],
    branch: Annotated[RecoveryBranch, typer.Option("--branch")],
    recovery_protocol_id: Annotated[str, typer.Option("--protocol-id")],
    retention_package_id: Annotated[
        str | None,
        typer.Option("--retention-package-id"),
    ] = None,
    scaffold_id: Annotated[str | None, typer.Option("--scaffold-id")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Resume a request-to-child-to-link saga and emit its parent state."""

    state = _sdk(root).start_reacquisition(
        parent_inquiry_id,
        request_id=request_id,
        child_inquiry_id=child_inquiry_id,
        branch=branch,
        recovery_protocol_id=recovery_protocol_id,
        retention_package_id=retention_package_id,
        scaffold_id=scaffold_id,
    )
    typer.echo(_json(state))


@recovery_app.command("inspect")
def inspect_recovery(
    parent_inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Emit only the immutable recovery records owned by a parent inquiry."""

    state = _sdk(root).inspect(parent_inquiry_id)
    typer.echo(
        _json(
            {
                "comparisons": [
                    item.model_dump(mode="json") for item in state.recovery_comparisons
                ],
                "links": [
                    item.model_dump(mode="json") for item in state.reacquisition_inquiry_links
                ],
                "observations": [
                    item.model_dump(mode="json") for item in state.recovery_observations
                ],
                "requests": [item.model_dump(mode="json") for item in state.reacquisition_requests],
                "sequence": state.sequence,
            }
        )
    )


@recovery_app.command("compare")
def compare_recovery(
    parent_inquiry_id: str,
    comparison_id: Annotated[str, typer.Option("--comparison-id")],
    baseline_observation: Annotated[
        list[str],
        typer.Option("--baseline-observation"),
    ],
    retained_observation: Annotated[
        list[str],
        typer.Option("--retained-observation"),
    ],
    evidence_id: Annotated[str, typer.Option("--evidence-id")],
    checker_verdict_id: Annotated[str, typer.Option("--checker-verdict-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one independently checked provisional exact-frontier comparison."""

    comparison = _sdk(root).compare_recovery(
        parent_inquiry_id,
        comparison_id=comparison_id,
        baseline_observation_ids=tuple(sorted(set(baseline_observation))),
        retained_observation_ids=tuple(sorted(set(retained_observation))),
        comparison_check=CheckReference(
            evidence_id=evidence_id,
            checker_verdict_id=checker_verdict_id,
        ),
    )
    typer.echo(_json(comparison))


@compression_app.command("inspect")
def inspect_compression(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Emit authoritative G3 records and the rebuildable retained-state view."""

    state = _sdk(root).inspect(inquiry_id)
    typer.echo(
        _json(
            {
                "applications": [
                    item.model_dump(mode="json") for item in state.compression_applications
                ],
                "carrier_manifests": [
                    item.model_dump(mode="json") for item in state.binding_carrier_manifests
                ],
                "contracts": [item.model_dump(mode="json") for item in state.compression_contracts],
                "licenses": [
                    item.model_dump(mode="json") for item in state.exact_compression_licenses
                ],
                "retained_state_views": [
                    item.model_dump(mode="json") for item in state.retained_state_views
                ],
                "sequence": state.sequence,
                "validations": [
                    item.model_dump(mode="json") for item in state.compression_validations
                ],
            }
        )
    )


@compression_app.command("fixture")
def compression_fixture(
    name: Annotated[str, typer.Argument(help="unary-parity or order-sensitive")],
    protect_parity: Annotated[bool, typer.Option("--protect-parity/--no-protect-parity")] = True,
    singleton: Annotated[bool, typer.Option("--singleton/--parity-state")] = False,
) -> None:
    """Run one deterministic exact G3A-H reference checker."""

    if name == "unary-parity":
        result = validate_unary_parity(
            protect_parity=protect_parity,
            singleton_representation=singleton,
        )
    elif name == "order-sensitive":
        result = validate_order_sensitive_count()
    else:
        raise typer.BadParameter("fixture must be unary-parity or order-sensitive")
    typer.echo(_json(result.__dict__))


@project_app.command("anchor")
def project_anchor(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one exact clean protected repository anchor."""

    anchor = ProjectAnchor.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_project_anchor(inquiry_id, anchor)
    typer.echo(_json(state.project_anchors[-1]))


@project_app.command("evaluate")
def project_evaluate(
    inquiry_id: str,
    request_id: Annotated[str, typer.Option("--request-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Derive one consequence-pinned capability evaluation without appending events."""

    typer.echo(_json(_sdk(root).evaluate_capability_request(inquiry_id, request_id)))


@project_app.command("handoff")
def project_handoff(
    inquiry_id: str,
    request_id: Annotated[str, typer.Option("--request-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Emit the bounded context-reset handoff derived from one exact episode."""

    typer.echo(_json(_sdk(root).capability_handoff(inquiry_id, request_id)))


@project_app.command("limitation")
def project_limitation(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record a preserved consequential limitation at an owned anchor."""

    limitation = CapabilityLimitation.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_capability_limitation(inquiry_id, limitation)
    typer.echo(_json(state.capability_limitations[-1]))


@project_app.command("question-candidate")
def project_question_candidate(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one inert generated question-contract candidate."""

    candidate = QuestionContractCandidate.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_question_contract_candidate(inquiry_id, candidate)
    typer.echo(_json(state.question_contract_candidates[-1]))


@project_app.command("question-decision")
def project_question_decision(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record an independently evidenced question-repertoire decision."""

    decision = QuestionRepertoireDecision.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).decide_question_repertoire(inquiry_id, decision)
    typer.echo(_json(state.question_repertoire_decisions[-1]))


@project_app.command("question-registry")
def project_question_registry(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Emit the deterministic confined registry of admitted project questions."""

    registry = _sdk(root).generated_question_registry(inquiry_id)
    typer.echo(_json([item.model_dump(mode="json") for item in registry]))


@project_app.command("question-open")
def project_question_open(
    inquiry_id: str,
    candidate_id: Annotated[str, typer.Option("--candidate-id")],
    binding: Annotated[list[str], typer.Option("--binding")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Open one exact admitted project question as an ordinary obligation."""

    bindings: dict[str, str] = {}
    for item in binding:
        name, separator, value = item.partition("=")
        if not separator or not name or not value or name in bindings:
            raise typer.BadParameter("each --binding must be one unique nonempty NAME=VALUE")
        bindings[name] = value
    state = _sdk(root).open_generated_question(
        inquiry_id,
        candidate_id=candidate_id,
        bindings=bindings,
    )
    typer.echo(_json(state.obligations[-1]))


@project_app.command("method-candidate")
def project_method_candidate(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one inert native-method binding candidate."""

    candidate = MethodBindingCandidate.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_method_binding_candidate(inquiry_id, candidate)
    typer.echo(_json(state.method_binding_candidates[-1]))


@project_app.command("method-decision")
def project_method_decision(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record an independently evidenced method-repertoire decision."""

    decision = MethodAdmissionDecision.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).decide_method_admission(inquiry_id, decision)
    typer.echo(_json(state.method_admission_decisions[-1]))


@project_app.command("frontier")
def project_frontier(
    inquiry_id: str,
    frontier_id: Annotated[str, typer.Option("--frontier-id")],
    candidate: Annotated[list[Path], typer.Option("--candidate")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record candidates and their deterministic nondominated frontier."""

    candidates = tuple(
        CapabilitySuccessorCandidate.model_validate_json(path.read_bytes(), strict=True)
        for path in candidate
    )
    sdk = _sdk(root)
    for item in candidates:
        sdk.record_capability_successor_candidate(inquiry_id, item)
    frontier = derive_capability_frontier(frontier_id=frontier_id, candidates=candidates)
    state = sdk.record_capability_frontier(inquiry_id, frontier)
    typer.echo(_json(state.capability_frontiers[-1]))


@project_app.command("goal")
def project_goal(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Seal an immutable discriminator-first implementation Goal."""

    goal = ImplementationGoalContract.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).seal_implementation_goal(inquiry_id, goal)
    typer.echo(_json(state.implementation_goals[-1]))


@project_app.command("goal-candidate")
def project_goal_candidate(
    inquiry_id: str,
    source_obligation_id: Annotated[str, typer.Option("--source-obligation-id")],
    downstream_obligation_id: Annotated[str, typer.Option("--downstream-obligation-id")],
    frontier_id: Annotated[str, typer.Option("--frontier-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Derive and record one confined inert implementation-Goal candidate."""

    sdk = _sdk(root)
    derived = sdk.derive_implementation_goal_candidate(
        inquiry_id,
        source_obligation_id=source_obligation_id,
        downstream_obligation_id=downstream_obligation_id,
        frontier_id=frontier_id,
    )
    if isinstance(derived, GoalSynthesisUnknown):
        typer.echo(_json(derived))
        raise typer.Exit(code=2)
    state = sdk.record_implementation_goal_candidate(inquiry_id, derived)
    typer.echo(_json(state.implementation_goal_candidates[-1]))


@project_app.command("goal-decision")
def project_goal_decision(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one total controller decision over an exact Goal candidate."""

    decision = GoalAdmissionDecision.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).decide_goal_admission(inquiry_id, decision)
    typer.echo(_json(state.goal_admission_decisions[-1]))


@project_app.command("goal-seal-admitted")
def project_goal_seal_admitted(
    inquiry_id: str,
    candidate_id: Annotated[str, typer.Option("--candidate-id")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Seal the immutable Goal owned by one admitted generated candidate."""

    state = _sdk(root).seal_admitted_implementation_goal(inquiry_id, candidate_id=candidate_id)
    typer.echo(_json(state.implementation_goals[-1]))


@project_app.command("candidate")
def project_candidate(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record an externally created isolated candidate environment."""

    manifest = CandidateEnvironmentManifest.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_candidate_environment(inquiry_id, manifest)
    typer.echo(_json(state.candidate_environments[-1]))


@project_app.command("evidence")
def project_evidence(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one exact-head external development return."""

    evidence = DevelopmentEvidence.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_development_evidence(inquiry_id, evidence)
    typer.echo(_json(state.development_evidence[-1]))


@project_app.command("review")
def project_review(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record a fresh exact-head independent review."""

    review = IndependentReview.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_independent_review(inquiry_id, review)
    typer.echo(_json(state.independent_reviews[-1]))


@project_app.command("successor")
def project_successor(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record the preserve/gain disposition for an exact reviewed candidate."""

    decision = ProjectSuccessorDecision.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).decide_project_successor(inquiry_id, decision)
    typer.echo(_json(state.project_successor_decisions[-1]))


@project_app.command("promote")
def project_promote(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record externally performed protected promotion; never mutate Git."""

    decision = PromotionDecision.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_promotion_decision(inquiry_id, decision)
    typer.echo(_json(state.promotion_decisions[-1]))


@project_app.command("checkpoint")
def project_checkpoint(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Append one monotone recursive-cycle checkpoint."""

    checkpoint = RecursiveCycleCheckpoint.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_recursive_cycle_checkpoint(inquiry_id, checkpoint)
    typer.echo(_json(state.recursive_cycle_checkpoints[-1]))


@project_app.command("stop")
def project_stop(
    inquiry_id: str,
    record: Annotated[Path, typer.Option("--record")],
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Record one typed bounded-recursion stop disposition."""

    disposition = RecursiveStopDisposition.model_validate_json(record.read_bytes(), strict=True)
    state = _sdk(root).record_recursive_stop_disposition(inquiry_id, disposition)
    typer.echo(_json(state.recursive_stop_dispositions[-1]))


@project_app.command("inspect")
def project_inspect(
    inquiry_id: str,
    root: Annotated[Path, typer.Option("--root")] = Path("."),
) -> None:
    """Emit only the immutable G3R project-inquiry records."""

    state = _sdk(root).inspect(inquiry_id)
    typer.echo(
        _json(
            {
                name: [item.model_dump(mode="json") for item in getattr(state, name)]
                for name in (
                    "project_anchors",
                    "capability_limitations",
                    "question_contract_candidates",
                    "question_repertoire_decisions",
                    "method_binding_candidates",
                    "method_admission_decisions",
                    "capability_successor_candidates",
                    "capability_frontiers",
                    "implementation_goals",
                    "candidate_environments",
                    "development_evidence",
                    "independent_reviews",
                    "project_successor_decisions",
                    "promotion_decisions",
                    "recursive_cycle_checkpoints",
                    "recursive_stop_dispositions",
                )
            }
        )
    )


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
