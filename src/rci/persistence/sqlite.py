"""SQLite WAL event ledger with optimistic stream sequencing."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, Field

from rci.claims.models import ObligationStatus
from rci.core.errors import InvalidTransitionError
from rci.core.events import (
    DomainEvent,
    InquiryStarted,
    ReacquisitionInquiryLinked,
    ReacquisitionRequested,
    RecoveryObservationRecorded,
)
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
from rci.memory.models import ReacquisitionChildManifest, ReacquisitionRequest
from rci.persistence.artifacts import ArtifactStore
from rci.persistence.errors import (
    DuplicateEventError,
    IntegrityError,
    OptimisticConcurrencyError,
    SagaIntegrityError,
    SnapshotConflictError,
    UnsupportedSchemaVersionError,
)

DATABASE_SCHEMA_VERSION = 2
FOLDED_STATE_SCHEMA_VERSION = "rci.inquiry-state.v3"
_REBUILDABLE_FOLDED_STATE_SCHEMAS = frozenset({"rci.inquiry-state.v1", "rci.inquiry-state.v2"})
EVENT_PREFIX_DIGEST_VERSION = "rci.event-prefix.v1"


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
    fold_schema_version: Identifier
    source_event_digest: Sha256Digest
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

    def _load_prefix_on_connection(
        self,
        connection: sqlite3.Connection,
        stream_id: str,
        through_sequence: int,
    ) -> tuple[StoredEvent, ...]:
        row = connection.execute(
            "SELECT version FROM streams WHERE stream_id = ?",
            (stream_id,),
        ).fetchone()
        if row is None or int(row["version"]) < through_sequence:
            raise SagaIntegrityError("reacquisition child prefix is absent or incomplete")
        rows = connection.execute(
            """
            SELECT stream_id, sequence, event_id, event_type, event_schema_version,
                   event_bytes, event_digest
            FROM events
            WHERE stream_id = ? AND sequence <= ?
            ORDER BY sequence ASC
            """,
            (stream_id, through_sequence),
        ).fetchall()
        stored = tuple(self._decode_row(item) for item in rows)
        if tuple(item.sequence for item in stored) != tuple(range(1, through_sequence + 1)):
            raise SagaIntegrityError("reacquisition child prefix contains a sequence gap")
        self._validate_artifacts(stored)
        return stored

    @staticmethod
    def _prefix_digest(
        stream_id: str,
        events: Sequence[StoredEvent],
        sequence: int,
    ) -> Sha256Digest:
        material = {
            "event_digests": [item.event_digest for item in events[:sequence]],
            "format": EVENT_PREFIX_DIGEST_VERSION,
            "sequence": sequence,
            "stream_id": stream_id,
        }
        return sha256_digest(canonical_json_bytes(material))

    def _validate_reacquisition_link(
        self,
        connection: sqlite3.Connection,
        event: ReacquisitionInquiryLinked,
        parent_state: InquiryState,
    ) -> None:
        link = event.link
        request = next(
            (item for item in parent_state.reacquisition_requests if item.id == link.request_id),
            None,
        )
        if request is None:
            raise SagaIntegrityError("reacquisition link has no owned parent request")
        prefix = self._load_prefix_on_connection(
            connection,
            link.child_inquiry_id,
            link.child_prefix_sequence,
        )
        start = prefix[0]
        if not isinstance(start.event, InquiryStarted):
            raise SagaIntegrityError(
                "reacquisition child prefix does not begin with InquiryStarted"
            )
        context_digest = sha256_digest(canonical_json_bytes(start.event.context))
        if (
            start.sequence != link.child_start_sequence
            or start.event.event_id != link.child_start_event_id
            or start.event_digest != link.child_start_event_digest
            or start.event.manifest_artifact != link.child_manifest_artifact
            or start.event.manifest_artifact != request.child_manifest_artifact
            or start.event.policy_version != request.child_policy_version
            or context_digest != link.child_context_digest
            or context_digest != request.child_context_digest
            or self._prefix_digest(link.child_inquiry_id, prefix, link.child_prefix_sequence)
            != link.child_prefix_digest
        ):
            raise SagaIntegrityError(
                "reacquisition child prefix does not match its pinned request and link proof"
            )
        self._validate_child_manifest(request, start.event)

    def _load_child_manifest(self, request: ReacquisitionRequest) -> ReacquisitionChildManifest:
        if self.artifact_store is None:
            raise SagaIntegrityError("reacquisition requires a configured artifact store")
        artifact = request.child_manifest_artifact
        try:
            manifest_bytes = self.artifact_store.get_bytes(artifact)
            manifest = ReacquisitionChildManifest.model_validate_json(
                manifest_bytes,
                strict=True,
            )
            self.artifact_store.verify(manifest.inquiry_manifest_artifact)
            return manifest
        except (ValueError, TypeError) as error:
            raise SagaIntegrityError("reacquisition child manifest is malformed") from error

    def _validate_request_manifest(self, event: ReacquisitionRequested) -> None:
        request = event.request
        manifest = self._load_child_manifest(request)
        if (
            manifest.parent_inquiry_id,
            manifest.request_id,
            manifest.child_inquiry_id,
            manifest.pins,
            manifest.context_digest,
            manifest.policy_version,
            manifest.inquiry_manifest_artifact,
        ) != (
            request.parent_inquiry_id,
            request.id,
            request.child_inquiry_id,
            request.pins,
            request.child_context_digest,
            request.child_policy_version,
            request.child_inquiry_manifest_artifact,
        ):
            raise SagaIntegrityError("reacquisition manifest differs from its parent request")

    def _validate_child_manifest(
        self,
        request: ReacquisitionRequest,
        start: InquiryStarted,
    ) -> None:
        manifest = self._load_child_manifest(request)
        pins = manifest.pins
        context = start.context
        if context is None or (
            manifest.parent_inquiry_id,
            manifest.request_id,
            manifest.child_inquiry_id,
            manifest.context_digest,
            manifest.policy_version,
            pins,
            manifest.inquiry_manifest_artifact,
        ) != (
            request.parent_inquiry_id,
            request.id,
            request.child_inquiry_id,
            request.child_context_digest,
            request.child_policy_version,
            request.pins,
            request.child_inquiry_manifest_artifact,
        ):
            raise SagaIntegrityError("reacquisition child manifest does not match the request")
        if (
            context.scope_fingerprint,
            context.binding_revision,
            context.protected_horizon_id,
            context.finite_universe_hash,
        ) != (
            pins.scope_fingerprint,
            pins.binding_revision,
            pins.protected_horizon_id,
            pins.finite_universe_hash,
        ):
            raise SagaIntegrityError("reacquisition child context differs from recovery pins")

    def _validate_recovery_observation(
        self,
        connection: sqlite3.Connection,
        event: RecoveryObservationRecorded,
        committed_parent_state: InquiryState,
    ) -> None:
        observation = event.observation
        request = next(
            (
                item
                for item in committed_parent_state.reacquisition_requests
                if item.id == observation.reacquisition_request_id
            ),
            None,
        )
        link = next(
            (
                item
                for item in committed_parent_state.reacquisition_inquiry_links
                if item.request_id == observation.reacquisition_request_id
            ),
            None,
        )
        if request is None or link is None:
            raise SagaIntegrityError("recovery observation requires a durably linked child inquiry")
        prefix = self._load_prefix_on_connection(
            connection,
            observation.child_inquiry_id,
            observation.child_prefix_sequence,
        )
        if (
            self._prefix_digest(
                observation.child_inquiry_id,
                prefix,
                observation.child_prefix_sequence,
            )
            != observation.child_prefix_digest
        ):
            raise SagaIntegrityError("recovery observation child prefix digest is invalid")
        try:
            child_state = replay(item.event for item in prefix)
        except InvalidTransitionError as error:
            raise SagaIntegrityError(
                "recovery observation child prefix is not replayable"
            ) from error
        known_effect_ids = {
            item.request.id
            for item in child_state.effect_requests
            if item.accepted_result is not None
        }
        known_probe_ids = {item.id for item in child_state.probe_observations}
        if not set(observation.effect_request_ids) <= known_effect_ids:
            raise SagaIntegrityError(
                "recovery observation names an absent or unresolved child effect request"
            )
        if not set(observation.logical_probe_ids) <= known_probe_ids:
            raise SagaIntegrityError("recovery observation names an absent child probe event")
        if not child_state.obligations or any(
            child_state.current_obligation_status(item.id) is not ObligationStatus.SATISFIED
            for item in child_state.obligations
        ):
            raise SagaIntegrityError("recovery observation child inquiry is unfinished")

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

            if schema_version == 1:
                self._migrate_v1_to_v2(connection)
                schema_version = DATABASE_SCHEMA_VERSION

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
                        fold_schema_version TEXT NOT NULL,
                        source_event_digest TEXT NOT NULL,
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

    @staticmethod
    def _migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
        """Replace disposable v1 snapshots while preserving authoritative rows.

        G1 snapshots did not pin their folded-state schema or source event prefix.
        They are derived acceleration data, so the only sound migration is to discard
        them and rebuild from the unchanged ledger. Events, streams, and versioned
        projection checkpoints remain byte-for-byte untouched.
        """

        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute("DROP TRIGGER IF EXISTS snapshots_forbid_update")
            connection.execute("ALTER TABLE snapshots RENAME TO snapshots_v1")
            connection.execute(
                """
                CREATE TABLE snapshots (
                    stream_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL CHECK (sequence >= 1),
                    fold_schema_version TEXT NOT NULL,
                    source_event_digest TEXT NOT NULL,
                    state_bytes BLOB NOT NULL,
                    state_digest TEXT NOT NULL,
                    PRIMARY KEY (stream_id, sequence),
                    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
                )
                """
            )
            connection.execute("DROP TABLE snapshots_v1")
            connection.execute(
                """
                CREATE TRIGGER snapshots_forbid_update
                BEFORE UPDATE ON snapshots
                BEGIN
                    SELECT RAISE(ABORT, 'snapshots are immutable');
                END
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
            committed_state = self._fold_committed_stream(connection, stream_id, current)
            candidate_state = committed_state
            for event in events:
                if isinstance(event, ReacquisitionRequested):
                    self._validate_request_manifest(event)
                if isinstance(event, ReacquisitionInquiryLinked):
                    self._validate_reacquisition_link(connection, event, committed_state)
                if isinstance(event, RecoveryObservationRecorded):
                    self._validate_recovery_observation(connection, event, committed_state)
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

    def stream_prefix_digest(
        self,
        stream_id: str,
        *,
        through_sequence: int | None = None,
    ) -> Sha256Digest:
        """Digest one immutable ordered stream prefix without export-time metadata."""

        stream = self.load_stream(stream_id)
        sequence = stream.version if through_sequence is None else through_sequence
        if sequence < 0 or sequence > stream.version:
            raise ValueError("stream prefix sequence is outside the event stream")
        return self._prefix_digest(stream_id, stream.events, sequence)

    def save_snapshot(self, stream_id: str, state: InquiryState) -> SnapshotRecord:
        if state.inquiry_id != stream_id or state.sequence < 1:
            raise ValueError("snapshot state must belong to a started stream")
        if state.sequence > self.stream_version(stream_id):
            raise ValueError("snapshot sequence is ahead of its event stream")
        self._validate_artifacts(state)
        stream = self.load_stream(stream_id)
        expected = replay(item.event for item in stream.events[: state.sequence])
        if expected != state:
            raise IntegrityError("snapshot does not equal replay at its sequence")

        state_bytes = encode_state(state)
        digest = sha256_digest(state_bytes)
        source_event_digest = self.stream_prefix_digest(
            stream_id,
            through_sequence=state.sequence,
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT fold_schema_version, source_event_digest, state_bytes, state_digest
                FROM snapshots
                WHERE stream_id = ? AND sequence = ?
                """,
                (stream_id, state.sequence),
            ).fetchone()
            if existing is not None:
                existing_schema = str(existing["fold_schema_version"])
                if existing_schema in _REBUILDABLE_FOLDED_STATE_SCHEMAS:
                    connection.execute(
                        "DELETE FROM snapshots WHERE stream_id = ? AND sequence = ?",
                        (stream_id, state.sequence),
                    )
                    existing = None
                elif existing_schema != FOLDED_STATE_SCHEMA_VERSION:
                    raise UnsupportedSchemaVersionError(
                        f"snapshot fold schema {existing_schema!r} is unsupported"
                    )
            if existing is not None:
                source_changed = str(existing["source_event_digest"]) != source_event_digest
                bytes_changed = bytes(existing["state_bytes"]) != state_bytes
                digest_changed = existing["state_digest"] != digest
                if source_changed or bytes_changed or digest_changed:
                    raise SnapshotConflictError(
                        "snapshot sequence already stores different state bytes"
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO snapshots(
                        stream_id, sequence, fold_schema_version, source_event_digest,
                        state_bytes, state_digest
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stream_id,
                        state.sequence,
                        FOLDED_STATE_SCHEMA_VERSION,
                        source_event_digest,
                        state_bytes,
                        digest,
                    ),
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
            fold_schema_version=FOLDED_STATE_SCHEMA_VERSION,
            source_event_digest=source_event_digest,
            state_digest=digest,
            state=state,
        )

    def load_latest_snapshot(self, stream_id: str) -> SnapshotRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT stream_id, sequence, fold_schema_version, source_event_digest,
                       state_bytes, state_digest
                FROM snapshots
                WHERE stream_id = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (stream_id,),
            ).fetchone()
        if row is None:
            return None
        fold_schema_version = str(row["fold_schema_version"])
        if fold_schema_version != FOLDED_STATE_SCHEMA_VERSION:
            if fold_schema_version in _REBUILDABLE_FOLDED_STATE_SCHEMAS:
                return None
            raise UnsupportedSchemaVersionError(
                f"snapshot fold schema {fold_schema_version!r} is unsupported"
            )
        state_bytes = bytes(row["state_bytes"])
        digest = sha256_digest(state_bytes)
        if digest != row["state_digest"]:
            raise IntegrityError("snapshot bytes do not match their digest")
        try:
            state = decode_state(state_bytes)
        except ValueError as error:
            raise IntegrityError("snapshot state bytes are not a supported folded state") from error
        if state.inquiry_id != stream_id or state.sequence != row["sequence"]:
            raise IntegrityError("snapshot metadata does not match its state bytes")
        source_event_digest = self.stream_prefix_digest(
            stream_id,
            through_sequence=state.sequence,
        )
        if source_event_digest != row["source_event_digest"]:
            raise IntegrityError("snapshot source prefix does not match the event ledger")
        expected = replay(
            item.event for item in self.load_stream(stream_id).events[: state.sequence]
        )
        if expected != state:
            raise IntegrityError("snapshot state does not equal its event prefix")
        self._validate_artifacts(state)
        return SnapshotRecord(
            stream_id=stream_id,
            sequence=int(row["sequence"]),
            fold_schema_version=fold_schema_version,
            source_event_digest=source_event_digest,
            state_digest=str(row["state_digest"]),
            state=state,
        )

    def rebuild_state(self, stream_id: str, *, use_snapshot: bool = True) -> InquiryState:
        try:
            snapshot = self.load_latest_snapshot(stream_id) if use_snapshot else None
        except (IntegrityError, UnsupportedSchemaVersionError):
            # Snapshots are disposable. The authoritative ledger is validated again
            # below, so only genuinely derived-state damage is ignored here.
            snapshot = None
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
