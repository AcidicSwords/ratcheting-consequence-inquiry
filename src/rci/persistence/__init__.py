"""Durable event and artifact persistence."""

from rci.persistence.artifacts import ArtifactStore
from rci.persistence.errors import (
    ArtifactIntegrityError,
    DuplicateEventError,
    IntegrityError,
    OptimisticConcurrencyError,
    PersistenceError,
    SagaIntegrityError,
    SnapshotConflictError,
    UnsupportedSchemaVersionError,
)
from rci.persistence.sqlite import (
    DATABASE_SCHEMA_VERSION,
    EVENT_PREFIX_DIGEST_VERSION,
    FOLDED_STATE_SCHEMA_VERSION,
    ProjectionCheckpoint,
    SnapshotRecord,
    SQLiteEventStore,
    StoredEvent,
    StreamSlice,
)

__all__ = [
    "DATABASE_SCHEMA_VERSION",
    "EVENT_PREFIX_DIGEST_VERSION",
    "FOLDED_STATE_SCHEMA_VERSION",
    "ArtifactIntegrityError",
    "ArtifactStore",
    "DuplicateEventError",
    "IntegrityError",
    "OptimisticConcurrencyError",
    "PersistenceError",
    "ProjectionCheckpoint",
    "SQLiteEventStore",
    "SagaIntegrityError",
    "SnapshotConflictError",
    "SnapshotRecord",
    "StoredEvent",
    "StreamSlice",
    "UnsupportedSchemaVersionError",
]
