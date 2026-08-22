"""Capability-bounded execution for repository evidence.

The blocking suite exercises this port with an in-memory backend. The production
backend is deliberately Docker-only: a normal host subprocess cannot honestly promise
network denial or containment from the live source tree on both Windows and Linux.
Docker availability is optional and an unavailable daemon is a typed, non-blocking
result.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from collections.abc import Sequence
from enum import StrEnum
from hashlib import sha256
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import IO, Annotated, Protocol

from pydantic import Field, field_validator, model_validator

from rci.core.model import FrozenModel, NonEmptyText


class EvidenceRunStatus(StrEnum):
    COMPLETED = "completed"
    NONZERO_EXIT = "nonzero_exit"
    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output_limit"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class CapturedInput(FrozenModel):
    """One explicitly supplied file for the isolated input workspace."""

    relative_path: NonEmptyText
    content: Annotated[bytes, Field(max_length=4_194_304)]

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        candidate = PurePosixPath(value)
        if candidate.is_absolute() or not candidate.parts:
            raise ValueError("captured input paths must be relative")
        if any(part in {"", ".", ".."} for part in candidate.parts):
            raise ValueError("captured input paths cannot traverse the workspace")
        if "\\" in value or ":" in value or "\x00" in value:
            raise ValueError("captured input paths must use safe POSIX components")
        return value


class EvidenceRunRequest(FrozenModel):
    """A finite command over captured inputs, never a shell program string."""

    argv: Annotated[tuple[NonEmptyText, ...], Field(min_length=1, max_length=128)]
    inputs: Annotated[tuple[CapturedInput, ...], Field(max_length=256)] = ()
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_output_bytes: int = Field(default=1_048_576, ge=1, le=16_777_216)

    @model_validator(mode="after")
    def validate_request(self) -> EvidenceRunRequest:
        if any("\x00" in item for item in self.argv):
            raise ValueError("arguments cannot contain NUL")
        if sum(len(item.encode()) for item in self.argv) > 65_536:
            raise ValueError("the combined argument vector is too large")
        if sum(len(item.content) for item in self.inputs) > 16_777_216:
            raise ValueError("captured inputs exceed the aggregate 16 MiB budget")
        paths = [item.relative_path for item in self.inputs]
        if len(paths) != len(set(paths)):
            raise ValueError("captured input paths must be unique")
        return self


class EvidenceRunResult(FrozenModel):
    status: EvidenceRunStatus
    exit_code: int | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    diagnostic: str | None = None

    @model_validator(mode="after")
    def validate_result(self) -> EvidenceRunResult:
        process_statuses = {EvidenceRunStatus.COMPLETED, EvidenceRunStatus.NONZERO_EXIT}
        if self.status in process_statuses:
            if self.exit_code is None:
                raise ValueError("completed process results require an exit code")
        elif self.exit_code is not None:
            raise ValueError("non-process results cannot claim an exit code")
        return self


class EvidenceBackend(Protocol):
    """Execution mechanism that receives only the isolated captured workspace."""

    @property
    def network_isolated(self) -> bool: ...

    def execute(
        self,
        request: EvidenceRunRequest,
        captured_workspace: Path,
    ) -> EvidenceRunResult: ...


class EvidenceRunner:
    """Materialize inputs in a fresh directory and delegate to an isolated backend."""

    def __init__(self, backend: EvidenceBackend) -> None:
        if not backend.network_isolated:
            raise ValueError("evidence backends must enforce network denial")
        self._backend = backend

    def run(self, request: EvidenceRunRequest) -> EvidenceRunResult:
        with TemporaryDirectory(prefix="rci-evidence-") as temporary:
            workspace = Path(temporary).resolve()
            workspace.chmod(0o755)
            for item in request.inputs:
                destination = (workspace / Path(*PurePosixPath(item.relative_path).parts)).resolve()
                if workspace not in destination.parents:
                    raise ValueError("captured input escaped the temporary workspace")
                destination.parent.mkdir(parents=True, exist_ok=True)
                current = destination.parent
                while current != workspace:
                    current.chmod(0o755)
                    current = current.parent
                destination.write_bytes(item.content)
                destination.chmod(0o644)
            return self._backend.execute(request, workspace)


class _BoundedProcessResult(FrozenModel):
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool = False
    output_exceeded: bool = False


def _run_bounded_process(
    argv: Sequence[str],
    *,
    timeout_seconds: int,
    max_output_bytes: int,
) -> _BoundedProcessResult:
    """Run explicit argv while limiting wall time and combined captured output."""

    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "")},
        shell=False,
    )
    if process.stdout is None or process.stderr is None:  # pragma: no cover - Popen contract
        process.kill()
        raise RuntimeError("failed to create bounded output pipes")

    lock = threading.Lock()
    chunks: dict[str, list[bytes]] = {"stdout": [], "stderr": []}
    captured = 0
    exceeded = False

    def drain(name: str, pipe: IO[bytes]) -> None:
        nonlocal captured, exceeded
        while True:
            data = pipe.read(65_536)
            if not data:
                return
            with lock:
                remaining = max_output_bytes - captured
                if remaining > 0:
                    kept = data[:remaining]
                    chunks[name].append(kept)
                    captured += len(kept)
                if len(data) > remaining:
                    exceeded = True
                    process.kill()
                    return

    threads = (
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    )
    for thread in threads:
        thread.start()

    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait()
    finally:
        for thread in threads:
            thread.join(timeout=5)

    return _BoundedProcessResult(
        exit_code=None if timed_out or exceeded else process.returncode,
        stdout=b"".join(chunks["stdout"]),
        stderr=b"".join(chunks["stderr"]),
        timed_out=timed_out,
        output_exceeded=exceeded,
    )


class DockerEvidenceBackend:
    """Run a digest-pinned image with a read-only captured-input mount.

    The class offers no generic mount, environment, socket, or host-workspace option.
    The container has no network, runs nonroot with a read-only root filesystem, drops
    all capabilities, and emits its only result through bounded stdout/stderr.
    """

    _FORBIDDEN_EXECUTABLES = frozenset(
        {
            "ansible",
            "aws",
            "az",
            "bash",
            "busybox",
            "cmd",
            "curl",
            "docker",
            "fish",
            "flit",
            "gcloud",
            "gh",
            "git",
            "hatch",
            "helm",
            "kubectl",
            "make",
            "npm",
            "npx",
            "pip",
            "pip3",
            "pnpm",
            "poetry",
            "powershell",
            "pwsh",
            "python",
            "python3",
            "rsync",
            "scp",
            "sh",
            "ssh",
            "terraform",
            "twine",
            "uv",
            "wget",
            "yarn",
            "zsh",
        }
    )
    _FORBIDDEN_ACTIONS = frozenset(
        {
            "build",
            "checkout",
            "commit",
            "deploy",
            "install",
            "merge",
            "package",
            "publish",
            "push",
            "release",
            "uninstall",
            "upload",
        }
    )

    def __init__(
        self,
        *,
        image: str,
        allowed_commands: Sequence[str],
        docker_executable: str = "docker",
        memory_limit: str = "512m",
        cpu_limit: str = "1.0",
        pids_limit: int = 128,
    ) -> None:
        name, separator, digest = image.rpartition("@sha256:")
        if not name or not separator or len(digest) != 64:
            raise ValueError("Docker evidence images must be pinned by sha256 digest")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ValueError("Docker image digest must be lowercase hexadecimal") from error
        if digest != digest.lower():
            raise ValueError("Docker image digest must be lowercase hexadecimal")
        if not allowed_commands or any(not item for item in allowed_commands):
            raise ValueError("at least one nonempty allowed command is required")
        for command in allowed_commands:
            self._validate_executable(command)
        if pids_limit < 1:
            raise ValueError("pids_limit must be positive")
        self.image = image
        self.allowed_commands = frozenset(allowed_commands)
        self.docker_executable = docker_executable
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.pids_limit = pids_limit

    @classmethod
    def _normalized_executable(cls, command: str) -> str:
        normalized = PurePosixPath(command.replace("\\", "/")).name.lower()
        return normalized.removesuffix(".exe")

    @classmethod
    def _validate_executable(cls, command: str) -> None:
        executable = cls._normalized_executable(command)
        if executable in cls._FORBIDDEN_EXECUTABLES:
            raise ValueError(f"forbidden evidence executable: {executable}")
        if any(action in executable for action in cls._FORBIDDEN_ACTIONS):
            raise ValueError("evidence executable names cannot expose mutation/release actions")

    @classmethod
    def _validate_argv(cls, argv: Sequence[str]) -> None:
        cls._validate_executable(argv[0])
        for argument in argv[1:]:
            token = argument.lower().lstrip("-").split("=", 1)[0]
            if token in cls._FORBIDDEN_ACTIONS:
                raise ValueError(f"forbidden evidence action argument: {token}")

    @property
    def network_isolated(self) -> bool:
        return True

    @staticmethod
    def _container_name(captured_workspace: Path) -> str:
        digest = sha256(str(captured_workspace).encode()).hexdigest()[:24]
        return f"rci-evidence-{digest}"

    def docker_argv(
        self,
        request: EvidenceRunRequest,
        captured_workspace: Path,
    ) -> tuple[str, ...]:
        if request.argv[0] not in self.allowed_commands:
            raise ValueError(f"command is not allowlisted: {request.argv[0]}")
        self._validate_argv(request.argv)
        return (
            self.docker_executable,
            "run",
            "--rm",
            "--pull",
            "never",
            "--name",
            self._container_name(captured_workspace),
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges=true",
            "--user",
            "65532:65532",
            "--memory",
            self.memory_limit,
            "--cpus",
            self.cpu_limit,
            "--pids-limit",
            str(self.pids_limit),
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount",
            f"type=bind,src={captured_workspace},dst=/evidence,readonly",
            "--workdir",
            "/tmp",
            self.image,
            *request.argv,
        )

    def execute(
        self,
        request: EvidenceRunRequest,
        captured_workspace: Path,
    ) -> EvidenceRunResult:
        if shutil.which(self.docker_executable) is None:
            return EvidenceRunResult(
                status=EvidenceRunStatus.UNSUPPORTED,
                diagnostic="Docker CLI is unavailable",
            )
        try:
            daemon_probe = _run_bounded_process(
                (
                    self.docker_executable,
                    "version",
                    "--format",
                    "{{.Server.Version}}",
                ),
                timeout_seconds=min(request.timeout_seconds, 5),
                max_output_bytes=4096,
            )
            if (
                daemon_probe.timed_out
                or daemon_probe.output_exceeded
                or daemon_probe.exit_code != 0
            ):
                return EvidenceRunResult(
                    status=EvidenceRunStatus.UNSUPPORTED,
                    diagnostic="Docker daemon is unavailable",
                )
            process = _run_bounded_process(
                self.docker_argv(request, captured_workspace),
                timeout_seconds=request.timeout_seconds,
                max_output_bytes=request.max_output_bytes,
            )
        except OSError as error:
            return EvidenceRunResult(
                status=EvidenceRunStatus.UNSUPPORTED,
                diagnostic=f"Docker execution unavailable: {type(error).__name__}",
            )
        if process.timed_out or process.output_exceeded:
            _run_bounded_process(
                (
                    self.docker_executable,
                    "rm",
                    "--force",
                    self._container_name(captured_workspace),
                ),
                timeout_seconds=10,
                max_output_bytes=4096,
            )
        if process.timed_out:
            return EvidenceRunResult(
                status=EvidenceRunStatus.TIMEOUT,
                stdout=process.stdout,
                stderr=process.stderr,
                diagnostic="evidence command exceeded its wall-time budget",
            )
        if process.output_exceeded:
            return EvidenceRunResult(
                status=EvidenceRunStatus.OUTPUT_LIMIT,
                stdout=process.stdout,
                stderr=process.stderr,
                diagnostic="evidence command exceeded its combined output budget",
            )
        if process.exit_code is None:  # pragma: no cover - internal result invariant
            return EvidenceRunResult(
                status=EvidenceRunStatus.FAILED,
                diagnostic="bounded process ended without an exit status",
            )
        return EvidenceRunResult(
            status=(
                EvidenceRunStatus.COMPLETED
                if process.exit_code == 0
                else EvidenceRunStatus.NONZERO_EXIT
            ),
            exit_code=process.exit_code,
            stdout=process.stdout,
            stderr=process.stderr,
        )
