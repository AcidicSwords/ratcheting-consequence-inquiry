"""SQLite WAL event ledger with optimistic stream sequencing."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, Field

from rci.core.errors import InvalidTransitionError
from rci.core.events import DomainEvent
from rci.core.model import ArtifactRef, FrozenModel, Identifier, Sha256Digest
from rci.core.replay import rebuild_projection, replay
from rci.core.serialization import (
    canonical_json_bytes,
    decode_event,
    decode_state,
    encode_event,
    encode_state,
    sha256_digest,
)
from rci.core.state import InquiryState, initial_state
from rci.core.transitions import evolve
from rci.persistence.artifacts import ArtifactStore
from rci.persistence.errors import (
    DuplicateEventError,
    IntegrityError,
    OptimisticConcurrencyError,
    SnapshotConflictError,
    UnsupportedSchemaVersionError,
)

DATABASE_SCHEMA_VERSION = 1


def _iter_artifact_refs(value: object) -> Iterator[ArtifactRef]:
    if isinstance(value, ArtifactRef):
        yield value
        return
    if isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            yield from _iter_artifact_refs(getattr(value, field_name))
        return
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_artifact_refs(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from _iter_artifact_refs(item)


class StoredEvent(FrozenModel):
    stream_id: Identifier
    sequence: int = Field(ge=1)
    event_digest: Sha256Digest
    event: DomainEvent


class StreamSlice(FrozenModel):
    stream_id: Identifier
    version: int = Field(ge=0)
    events: tuple[StoredEvent, ...]


class SnapshotRecord(FrozenModel):
    stream_id: Identifier
    sequence: int = Field(ge=1)
    state_digest: Sha256Digest
    state: InquiryState


class ProjectionCheckpoint(FrozenModel):
    projection_name: Identifier
    projection_schema_version: Identifier
    stream_id: Identifier
    sequence: int = Field(ge=0)
    payload_digest: Sha256Digest
    payload: bytes


class SQLiteEventStore:
    """An append-only per-stream ledger.

    Each append opens a new connection, starts ``BEGIN IMMEDIATE``, compares the exact
    expected stream sequence, writes the complete batch, and commits atomically. SQLite
    may execute work at least once outside this store; immutable request/result identities
    and the aggregate transitions enforce acceptance cardinality.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        artifact_store: ArtifactStore | None = None,
        busy_timeout_ms: int = 5_000,
    ) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_store = artifact_store
        self.busy_timeout_ms = busy_timeout_ms
        self._bootstrap()

    def _validate_artifacts(self, value: object) -> None:
        if self.artifact_store is None:
            return
        for artifact in _iter_artifact_refs(value):
            self.artifact_store.verify(artifact)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms:d}")
        return connection

    def _fold_committed_stream(
        self,
        connection: sqlite3.Connection,
        stream_id: str,
        version: int,
    ) -> InquiryState:
        """Validate and fold one stream on the append transaction's connection.

        Append must not trust a caller-supplied event batch merely because its bytes are
        well formed. Reading and folding the committed prefix after ``BEGIN IMMEDIATE``
        gives lifecycle validation the same serialization boundary as the eventual
        inserts, without opening a second connection or invoking any effect.
        """

        rows = connection.execute(
            """
            SELECT stream_id, sequence, event_id, event_type, event_schema_version,
                   event_bytes, event_digest
            FROM events
            WHERE stream_id = ?
            ORDER BY sequence ASC
            """,
            (stream_id,),
        ).fetchall()
        committed = tuple(self._decode_row(row) for row in rows)
        expected_sequences = tuple(range(1, version + 1))
        actual_sequences = tuple(item.sequence for item in committed)
        if actual_sequences != expected_sequences:
            raise IntegrityError("event stream contains a sequence gap")
        self._validate_artifacts(committed)
        try:
            state = replay(item.event for item in committed)
        except InvalidTransitionError as error:
            raise IntegrityError("committed event stream violates its lifecycle") from error
        if state.sequence != version:
            raise IntegrityError("committed event fold does not match the stream version")
        if version and state.inquiry_id != stream_id:
            raise IntegrityError("committed event fold belongs to a different stream")
        return state

    def _bootstrap(self) -> None:
        with self._connect() as connection:
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if schema_version > DATABASE_SCHEMA_VERSION:
                raise UnsupportedSchemaVersionError(
                    f"database schema {schema_version} is newer than supported "
                    f"schema {DATABASE_SCHEMA_VERSION}"
                )

            journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0])
            if journal_mode.lower() != "wal":
                raise IntegrityError(f"SQLite refused WAL mode and returned {journal_mode!r}")

            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS streams (
                        stream_id TEXT PRIMARY KEY NOT NULL,
                        version INTEGER NOT NULL CHECK (version >= 0)
                    );

                    CREATE TABLE IF NOT EXISTS events (
                        stream_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL CHECK (sequence >= 1),
                        event_id TEXT NOT NULL UNIQUE,
                        event_type TEXT NOT NULL,
                        event_schema_version INTEGER NOT NULL,
                        event_bytes BLOB NOT NULL,
                        event_digest TEXT NOT NULL,
                        PRIMARY KEY (stream_id, sequence),
                        FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
                    );

                    CREATE TABLE IF NOT EXISTS snapshots (
                        stream_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL CHECK (sequence >= 1),
                        state_bytes BLOB NOT NULL,
                        state_digest TEXT NOT NULL,
                        PRIMARY KEY (stream_id, sequence),
                        FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
                    );

                    CREATE TABLE IF NOT EXISTS projection_checkpoints (
                        projection_name TEXT NOT NULL,
                        projection_schema_version TEXT NOT NULL,
                        stream_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL CHECK (sequence >= 0),
                        payload_bytes BLOB NOT NULL,
                        payload_digest TEXT NOT NULL,
                        PRIMARY KEY (
                            projection_name, projection_schema_version, stream_id, sequence
                        )
                    );

                    CREATE TRIGGER IF NOT EXISTS events_forbid_update
                    BEFORE UPDATE ON events
                    BEGIN
                        SELECT RAISE(ABORT, 'event ledger is append-only');
                    END;

                    CREATE TRIGGER IF NOT EXISTS events_forbid_delete
                    BEFORE DELETE ON events
                    BEGIN
                        SELECT RAISE(ABORT, 'event ledger is append-only');
                    END;

                    CREATE TRIGGER IF NOT EXISTS snapshots_forbid_update
                    BEFORE UPDATE ON snapshots
                    BEGIN
                        SELECT RAISE(ABORT, 'snapshots are immutable');
                    END;
                    """
                )
                connection.execute(f"PRAGMA user_version = {DATABASE_SCHEMA_VERSION:d}")
                connection.commit()
            except BaseException:
                connection.rollback()
                raise

    def journal_mode(self) -> str:
        with self._connect() as connection:
            return str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    def stream_version(self, stream_id: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT version FROM streams WHERE stream_id = ?",
                (stream_id,),
            ).fetchone()
        return 0 if row is None else int(row["version"])

    def append(
        self,
        stream_id: str,
        expected_sequence: int,
        events: Sequence[DomainEvent],
    ) -> int:
        if expected_sequence < 0:
            raise ValueError("expected sequence cannot be negative")
        if any(event.inquiry_id != stream_id for event in events):
            raise ValueError("every event inquiry id must match its stream id")
        event_ids = [event.event_id for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise DuplicateEventError("an append batch contains duplicate event ids")
        self._validate_artifacts(events)

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT version FROM streams WHERE stream_id = ?",
                (stream_id,),
            ).fetchone()
            current = 0 if row is None else int(row["version"])
            if current != expected_sequence:
                raise OptimisticConcurrencyError(
                    f"stream {stream_id!r} is at sequence {current}, "
                    f"not expected sequence {expected_sequence}"
                )

            # Validate the committed prefix and every proposed transition before any
            # ledger row is inserted. This keeps malformed/out-of-order lifecycle
            # events from becoming durable histories that only fail later during replay.
            candidate_state = self._fold_committed_stream(connection, stream_id, current)
            for event in events:
                candidate_state = evolve(candidate_state, event)

            if row is None and events:
                connection.execute(
                    "INSERT INTO streams(stream_id, version) VALUES (?, 0)",
                    (stream_id,),
                )

            next_sequence = current
            for event in events:
                next_sequence += 1
                event_bytes = encode_event(event)
                connection.execute(
                    """
                    INSERT INTO events(
                        stream_id,
                        sequence,
                        event_id,
                        event_type,
                        event_schema_version,
                        event_bytes,
                        event_digest
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stream_id,
                        next_sequence,
                        event.event_id,
                        event.kind,
                        event.schema_version,
                        event_bytes,
                        sha256_digest(event_bytes),
                    ),
                )

            if events:
                connection.execute(
                    "UPDATE streams SET version = ? WHERE stream_id = ? AND version = ?",
                    (next_sequence, stream_id, current),
                )
                if connection.execute("SELECT changes()").fetchone()[0] != 1:
                    raise OptimisticConcurrencyError("stream version changed during append")
            # Recheck immediately before commit so a missing or modified referenced artifact
            # cannot knowingly enter the durable ledger.
            self._validate_artifacts(events)
            connection.commit()
            return next_sequence
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if "event_id" in str(error) or "UNIQUE" in str(error):
                raise DuplicateEventError("event identity already exists") from error
            raise IntegrityError(f"SQLite rejected the append: {error}") from error
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _decode_row(row: sqlite3.Row) -> StoredEvent:
        event_bytes = bytes(row["event_bytes"])
        expected_digest = str(row["event_digest"])
        actual_digest = sha256_digest(event_bytes)
        if actual_digest != expected_digest:
            raise IntegrityError(f"event digest mismatch at {row['stream_id']}:{row['sequence']}")
        event = decode_event(event_bytes)
        if event.event_id != row["event_id"] or event.kind != row["event_type"]:
            raise IntegrityError("event index metadata does not match immutable event bytes")
        if event.schema_version != row["event_schema_version"]:
            raise IntegrityError("event schema index does not match immutable event bytes")
        if event.inquiry_id != row["stream_id"]:
            raise IntegrityError("event stream index does not match immutable event bytes")
        return StoredEvent(
            stream_id=str(row["stream_id"]),
            sequence=int(row["sequence"]),
            event_digest=expected_digest,
            event=event,
        )

    def load_stream(self, stream_id: str, *, after_sequence: int = 0) -> StreamSlice:
        if after_sequence < 0:
            raise ValueError("after sequence cannot be negative")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT version FROM streams WHERE stream_id = ?",
                (stream_id,),
            ).fetchone()
            version = 0 if row is None else int(row["version"])
            if after_sequence > version:
                raise IntegrityError(
                    f"requested events after {after_sequence}, beyond stream version {version}"
                )
            rows = connection.execute(
                """
                SELECT stream_id, sequence, event_id, event_type, event_schema_version,
                       event_bytes, event_digest
                FROM events
                WHERE stream_id = ? AND sequence > ?
                ORDER BY sequence ASC
                """,
                (stream_id, after_sequence),
            ).fetchall()

        decoded = tuple(self._decode_row(item) for item in rows)
        self._validate_artifacts(decoded)
        expected_sequences = tuple(range(after_sequence + 1, version + 1))
        actual_sequences = tuple(item.sequence for item in decoded)
        if actual_sequences != expected_sequences:
            raise IntegrityError("event stream contains a sequence gap")
        return StreamSlice(stream_id=stream_id, version=version, events=decoded)

    def export_stream(self, stream_id: str) -> bytes:
        """Return deterministic JSON Lines without adding export-time metadata."""

        stream = self.load_stream(stream_id)
        lines = [
            canonical_json_bytes(
                {
                    "format": "rci.event-stream.v1",
                    "stream_id": stream.stream_id,
                    "version": stream.version,
                }
            )
        ]
        lines.extend(
            canonical_json_bytes(
                {
                    "event": json.loads(encode_event(stored.event)),
                    "event_digest": stored.event_digest,
                    "sequence": stored.sequence,
                }
            )
            for stored in stream.events
        )
        return b"\n".join(lines) + b"\n"

    def save_snapshot(self, stream_id: str, state: InquiryState) -> SnapshotRecord:
        if state.inquiry_id != stream_id or state.sequence < 1:
            raise ValueError("snapshot state must belong to a started stream")
        if state.sequence > self.stream_version(stream_id):
            raise ValueError("snapshot sequence is ahead of its event stream")
        self._validate_artifacts(state)
        expected = replay(
            item.event for item in self.load_stream(stream_id).events[: state.sequence]
        )
        if expected != state:
            raise IntegrityError("snapshot does not equal replay at its sequence")

        state_bytes = encode_state(state)
        digest = sha256_digest(state_bytes)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT state_bytes, state_digest
                FROM snapshots
                WHERE stream_id = ? AND sequence = ?
                """,
                (stream_id, state.sequence),
            ).fetchone()
            if existing is not None:
                bytes_changed = bytes(existing["state_bytes"]) != state_bytes
                digest_changed = existing["state_digest"] != digest
                if bytes_changed or digest_changed:
                    raise SnapshotConflictError(
                        "snapshot sequence already stores different state bytes"
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO snapshots(stream_id, sequence, state_bytes, state_digest)
                    VALUES (?, ?, ?, ?)
                    """,
                    (stream_id, state.sequence, state_bytes, digest),
                )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return SnapshotRecord(
            stream_id=stream_id,
            sequence=state.sequence,
            state_digest=digest,
            state=state,
        )

    def load_latest_snapshot(self, stream_id: str) -> SnapshotRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT stream_id, sequence, state_bytes, state_digest
                FROM snapshots
                WHERE stream_id = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (stream_id,),
            ).fetchone()
        if row is None:
            return None
        state_bytes = bytes(row["state_bytes"])
        digest = sha256_digest(state_bytes)
        if digest != row["state_digest"]:
            raise IntegrityError("snapshot bytes do not match their digest")
        state = decode_state(state_bytes)
        if state.inquiry_id != stream_id or state.sequence != row["sequence"]:
            raise IntegrityError("snapshot metadata does not match its state bytes")
        self._validate_artifacts(state)
        return SnapshotRecord(
            stream_id=stream_id,
            sequence=int(row["sequence"]),
            state_digest=str(row["state_digest"]),
            state=state,
        )

    def rebuild_state(self, stream_id: str, *, use_snapshot: bool = True) -> InquiryState:
        snapshot = self.load_latest_snapshot(stream_id) if use_snapshot else None
        state = initial_state() if snapshot is None else snapshot.state
        stream = self.load_stream(stream_id, after_sequence=state.sequence)
        rebuilt = replay((item.event for item in stream.events), state=state)
        if rebuilt.sequence != stream.version:
            raise IntegrityError("rebuilt state sequence does not equal stream version")
        return rebuilt

    def save_projection_checkpoint(
        self,
        projection_name: str,
        projection_schema_version: str,
        stream_id: str,
        sequence: int,
        payload: bytes,
    ) -> ProjectionCheckpoint:
        if type(payload) is not bytes:
            raise TypeError("projection checkpoints require exact bytes")
        if not projection_schema_version:
            raise ValueError("projection schema version is required")
        if sequence < 0 or sequence > self.stream_version(stream_id):
            raise ValueError("projection sequence is outside the event stream")
        digest = sha256_digest(payload)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT payload_bytes, payload_digest
                FROM projection_checkpoints
                WHERE projection_name = ? AND projection_schema_version = ?
                  AND stream_id = ? AND sequence = ?
                """,
                (projection_name, projection_schema_version, stream_id, sequence),
            ).fetchone()
            if existing is not None:
                bytes_changed = bytes(existing["payload_bytes"]) != payload
                digest_changed = existing["payload_digest"] != digest
                if bytes_changed or digest_changed:
                    raise SnapshotConflictError(
                        "projection checkpoint identity stores different bytes"
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO projection_checkpoints(
                        projection_name, projection_schema_version, stream_id, sequence,
                        payload_bytes, payload_digest
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        projection_name,
                        projection_schema_version,
                        stream_id,
                        sequence,
                        payload,
                        digest,
                    ),
                )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return ProjectionCheckpoint(
            projection_name=projection_name,
            projection_schema_version=projection_schema_version,
            stream_id=stream_id,
            sequence=sequence,
            payload_digest=digest,
            payload=payload,
        )

    def load_latest_projection_checkpoint(
        self,
        projection_name: str,
        projection_schema_version: str,
        stream_id: str,
    ) -> ProjectionCheckpoint | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT projection_name, projection_schema_version, stream_id, sequence,
                       payload_bytes, payload_digest
                FROM projection_checkpoints
                WHERE projection_name = ? AND projection_schema_version = ? AND stream_id = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (projection_name, projection_schema_version, stream_id),
            ).fetchone()
        if row is None:
            return None
        payload = bytes(row["payload_bytes"])
        digest = sha256_digest(payload)
        if digest != row["payload_digest"]:
            raise IntegrityError("projection checkpoint bytes do not match their digest")
        return ProjectionCheckpoint(
            projection_name=str(row["projection_name"]),
            projection_schema_version=str(row["projection_schema_version"]),
            stream_id=str(row["stream_id"]),
            sequence=int(row["sequence"]),
            payload_digest=str(row["payload_digest"]),
            payload=payload,
        )

    def rebuild_projection[ProjectionT](
        self,
        stream_id: str,
        *,
        initial: ProjectionT,
        apply: Callable[[ProjectionT, DomainEvent], ProjectionT],
    ) -> ProjectionT:
        stream = self.load_stream(stream_id)
        return rebuild_projection(
            (item.event for item in stream.events),
            initial=initial,
            apply=apply,
        )
