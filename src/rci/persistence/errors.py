"""Typed persistence and integrity failures."""


class PersistenceError(RuntimeError):
    """Base class for durable-store failures exposed to callers."""


class OptimisticConcurrencyError(PersistenceError):
    """A stream append used a sequence other than the current sequence."""


class DuplicateEventError(PersistenceError):
    """An immutable event identity already exists in the ledger."""


class IntegrityError(PersistenceError):
    """Persisted bytes no longer match their recorded digest or metadata."""


class SagaIntegrityError(IntegrityError):
    """A cross-stream saga fact lacks its exact immutable counterpart."""


class ArtifactIntegrityError(IntegrityError):
    """Content-addressed artifact material is absent, truncated, or changed."""


class SnapshotConflictError(PersistenceError):
    """A snapshot sequence was reused for different aggregate bytes."""


class UnsupportedSchemaVersionError(PersistenceError):
    """The database or persisted record uses an unknown future schema."""
