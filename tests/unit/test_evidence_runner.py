from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

import rci.evaluation.runner as runner_module
from rci.evaluation import (
    CapturedInput,
    DockerEvidenceBackend,
    EvidenceRunner,
    EvidenceRunRequest,
    EvidenceRunResult,
    EvidenceRunStatus,
)


class _RecordingIsolatedBackend:
    network_isolated = True

    def __init__(self) -> None:
        self.workspace: Path | None = None
        self.observed = b""

    def execute(
        self,
        request: EvidenceRunRequest,
        captured_workspace: Path,
    ) -> EvidenceRunResult:
        self.workspace = captured_workspace
        self.observed = (captured_workspace / "case" / "input.bin").read_bytes()
        (captured_workspace / "backend-scratch").write_bytes(b"isolated")
        return EvidenceRunResult(
            status=EvidenceRunStatus.COMPLETED,
            exit_code=0,
            stdout=b"ok",
        )


def test_runner_uses_ephemeral_captured_workspace(tmp_path: Path) -> None:
    live_source = tmp_path / "source.py"
    live_source.write_text("unchanged")
    backend = _RecordingIsolatedBackend()

    result = EvidenceRunner(backend).run(
        EvidenceRunRequest(
            argv=("checker", "--input", "/evidence/case/input.bin"),
            inputs=(CapturedInput(relative_path="case/input.bin", content=b"exact\x00bytes"),),
        )
    )

    assert result.status is EvidenceRunStatus.COMPLETED
    assert backend.observed == b"exact\x00bytes"
    assert backend.workspace is not None
    assert not backend.workspace.exists()
    assert live_source.read_text() == "unchanged"


def test_runner_rejects_nonisolated_backend() -> None:
    backend = _RecordingIsolatedBackend()
    backend.network_isolated = False
    with pytest.raises(ValueError, match="network denial"):
        EvidenceRunner(backend)


@pytest.mark.parametrize("path", ("../secret", "/absolute", "C:/secret", "a\\b"))
def test_captured_paths_fail_closed(path: str) -> None:
    with pytest.raises(ValidationError):
        CapturedInput(relative_path=path, content=b"x")


def test_request_bounds_inputs_and_argument_material() -> None:
    with pytest.raises(ValidationError, match="16 MiB"):
        EvidenceRunRequest(
            argv=("checker",),
            inputs=tuple(
                CapturedInput(relative_path=f"case-{index}", content=b"x" * 4_194_304)
                for index in range(5)
            ),
        )
    with pytest.raises(ValidationError, match="argument vector"):
        EvidenceRunRequest(argv=("x" * 4096,) * 17)


def test_docker_plan_has_only_captured_mount_and_hardening_flags(tmp_path: Path) -> None:
    digest = "a" * 64
    backend = DockerEvidenceBackend(
        image=f"registry.example/rci-checker@sha256:{digest}",
        allowed_commands=("checker",),
    )
    request = EvidenceRunRequest(argv=("checker", "--case", "/evidence/input.json"))

    argv = backend.docker_argv(request, tmp_path.resolve())

    assert argv[0:2] == ("docker", "run")
    assert argv[argv.index("--network") + 1] == "none"
    assert argv[argv.index("--name") + 1].startswith("rci-evidence-")
    assert "--read-only" in argv
    assert argv[argv.index("--cap-drop") + 1] == "ALL"
    assert argv[argv.index("--user") + 1] == "65532:65532"
    assert all("docker.sock" not in item for item in argv)
    assert "--env" not in argv
    assert "--env-file" not in argv
    mounts = [argv[index + 1] for index, value in enumerate(argv) if value == "--mount"]
    assert mounts == [f"type=bind,src={tmp_path.resolve()},dst=/evidence,readonly"]


def test_docker_image_and_command_must_be_allowlisted(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pinned"):
        DockerEvidenceBackend(image="python:3.12", allowed_commands=("python",))
    backend = DockerEvidenceBackend(
        image=f"example/checker@sha256:{'0' * 64}",
        allowed_commands=("checker",),
    )
    with pytest.raises(ValueError, match="allowlisted"):
        backend.docker_argv(EvidenceRunRequest(argv=("sh", "-c", "whoami")), tmp_path)


def test_missing_docker_is_typed_nonblocking(tmp_path: Path) -> None:
    backend = DockerEvidenceBackend(
        image=f"example/checker@sha256:{'0' * 64}",
        allowed_commands=("checker",),
        docker_executable="definitely-missing-rci-docker",
    )
    result = backend.execute(EvidenceRunRequest(argv=("checker",)), tmp_path)
    assert result.status is EvidenceRunStatus.UNSUPPORTED
    assert result.diagnostic == "Docker CLI is unavailable"


def test_timeout_forces_container_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_bounded(
        argv: tuple[str, ...],
        *,
        timeout_seconds: int,
        max_output_bytes: int,
    ) -> runner_module._BoundedProcessResult:
        del timeout_seconds, max_output_bytes
        calls.append(tuple(argv))
        if "run" in argv:
            return runner_module._BoundedProcessResult(
                exit_code=None,
                stdout=b"",
                stderr=b"",
                timed_out=True,
            )
        return runner_module._BoundedProcessResult(
            exit_code=0,
            stdout=b"",
            stderr=b"",
        )

    monkeypatch.setattr(shutil, "which", lambda _executable: "docker")
    monkeypatch.setattr(runner_module, "_run_bounded_process", fake_bounded)
    backend = DockerEvidenceBackend(
        image=f"example/checker@sha256:{'0' * 64}",
        allowed_commands=("checker",),
    )
    result = backend.execute(EvidenceRunRequest(argv=("checker",)), tmp_path.resolve())

    assert result.status is EvidenceRunStatus.TIMEOUT
    cleanup = calls[-1]
    assert cleanup[0:3] == ("docker", "rm", "--force")
    assert cleanup[3].startswith("rci-evidence-")


@pytest.mark.parametrize(
    "command",
    (
        "git",
        "docker",
        "gh",
        "twine",
        "uv",
        "pip",
        "bash",
        "pwsh.exe",
        "kubectl",
        "release-tool",
        "project-builder",
    ),
)
def test_docker_backend_rejects_mutation_packaging_and_release_ports(command: str) -> None:
    with pytest.raises(ValueError, match=r"forbidden|mutation/release"):
        DockerEvidenceBackend(
            image=f"example/checker@sha256:{'1' * 64}",
            allowed_commands=(command,),
        )


@pytest.mark.parametrize("action", ("push", "--deploy", "release", "--install=yes"))
def test_docker_backend_rejects_forbidden_action_arguments(
    tmp_path: Path,
    action: str,
) -> None:
    backend = DockerEvidenceBackend(
        image=f"example/checker@sha256:{'2' * 64}",
        allowed_commands=("rci-checker",),
    )
    with pytest.raises(ValueError, match="forbidden evidence action"):
        backend.docker_argv(
            EvidenceRunRequest(argv=("rci-checker", action)),
            tmp_path,
        )
