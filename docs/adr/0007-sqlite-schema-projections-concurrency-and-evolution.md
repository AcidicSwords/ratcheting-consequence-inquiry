# ADR-0007: SQLite schema, projections, concurrency, and evolution

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-012–RCI-016

## Context

The offline-first reference system needs crash-safe ordering and deterministic
replay on Windows and Linux without a server database. SQLite supplies the
required transaction boundary, but only if stream sequencing, schema evolution,
and derived state are explicit.

## Decision

Use the standard-library SQLite driver in WAL mode. An event append transaction
checks `expected_sequence`, inserts an ordered batch, and advances the stream
atomically. There is one logical writer per inquiry; concurrent stale writers
receive a typed optimistic-concurrency failure. Effect result acceptance uses
the same transaction boundary.

Bootstrap is idempotent and records a schema version. Unknown future schema,
event, snapshot, or projection versions fail closed. G1 proves the initial
schema and replay format; cross-version upcasters and compatibility migrations
are implemented only in a later hardening Goal, but event envelopes and
manifests reserve explicit version fields now.

Projections are disposable and checkpoint their schema version plus last event
sequence. Snapshots record stream sequence, fold/schema version, state digest,
and referenced artifact digests; invalid snapshots are ignored and rebuilt.
Deterministic export orders records canonically and excludes runtime timestamps
from semantic equality.

## Consequences

- No PostgreSQL or distributed coordinator is needed for the first milestone.
- Stale writes cannot silently fork an inquiry.
- Initial delivery does not pretend to support migrations it has not tested.
- Rebuild remains the recovery path for derived data.

## Verification

Test idempotent bootstrap, unknown-version rejection, two-connection optimistic
races, atomic multi-event append, rollback on failure, WAL reopen/crash cases,
projection rebuild, snapshot rejection, and byte-identical canonical export.
