"""Exact-byte SHA-256 content-addressed artifact storage."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from rci.core.model import ArtifactRef
from rci.core.serialization import sha256_digest
from rci.persistence.errors import ArtifactIntegrityError


class ArtifactStore:
    """Store immutable bytes under a digest-derived path.

    Media type is descriptive metadata and does not participate in content identity.
    No text decoding, newline conversion, or payload normalization occurs.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for_digest(self, digest: str) -> Path:
        # ArtifactRef performs the strict lowercase SHA-256 validation.
        validated = ArtifactRef(digest=digest, size=0)
        return self.root / validated.algorithm / digest[:2] / digest[2:]

    def path_for(self, artifact: ArtifactRef) -> Path:
        return self._path_for_digest(artifact.digest)

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str | None = None,
        encoding: str | None = None,
    ) -> ArtifactRef:
        if type(data) is not bytes:
            raise TypeError("ArtifactStore accepts exact bytes, not coercible byte-like values")
        artifact = ArtifactRef(
            digest=sha256_digest(data),
            size=len(data),
            media_type=media_type,
            encoding=encoding,
        )
        destination = self.path_for(artifact)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            self._verify_bytes(destination.read_bytes(), artifact)
            return artifact

        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".rci-artifact-",
                delete=False,
            ) as temporary:
                temporary.write(data)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_name = temporary.name
            os.replace(temporary_name, destination)
            temporary_name = None
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)

        self._verify_bytes(destination.read_bytes(), artifact)
        return artifact

    def get_bytes(self, artifact: ArtifactRef) -> bytes:
        path = self.path_for(artifact)
        if not path.is_file():
            raise ArtifactIntegrityError(f"artifact is missing: {artifact.digest}")
        data = path.read_bytes()
        self._verify_bytes(data, artifact)
        return data

    def verify(self, artifact: ArtifactRef) -> bool:
        self.get_bytes(artifact)
        return True

    @staticmethod
    def _verify_bytes(data: bytes, artifact: ArtifactRef) -> None:
        if len(data) != artifact.size:
            raise ArtifactIntegrityError(
                f"artifact size mismatch for {artifact.digest}: {len(data)} != {artifact.size}"
            )
        actual = sha256_digest(data)
        if actual != artifact.digest:
            raise ArtifactIntegrityError(
                f"artifact digest mismatch for {artifact.digest}: found {actual}"
            )
