# ADR-0002: Ledger/CAS authority and logical memory ownership

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-011–RCI-016, RCI-024

## Context

The cognitive drafts distinguish episodic, semantic, procedural, and latent
memory. The repair delta also requires one authority for state. Implementing each
memory as an independently writable store would permit contradictory histories
and make deterministic replay impossible.

## Decision

The append-only SQLite ledger and content-addressed artifact store are the only
durable authorities. `M_E`, `M_S`, `M_P`, `M_L`, warrant (`W`), attempt
(`A`), and prediction (`Pi`) are canonical logical owners inside the folded
event-sourced state:

```text
decide(state, command) -> events
evolve(state, event) -> state
```

Each semantic object has one logical owner. Other subtrees hold typed IDs, never
writable copies. Active theory, indexes, reports, scheduler queues, ancestry
graphs, and memory views are rebuildable projections. Snapshots are performance
hints and must be checked against ledger sequence and schema.

Large/raw payloads live in CAS; events contain digest references and required
metadata. Reducers do no I/O and generate no IDs, clocks, randomness, or provider
metadata.

## Consequences

RCI v0.4 and ADR-0011 clarify that the replay-complete `InquiryState` produced by
the aggregate fold is not a consequence-sufficient retained state. A
binding-derived history and licensed G3 representation are derived/recorded
semantic structures; neither replaces the ledger or aggregate.

- Cognitive “memory” does not create parallel databases or a second truth.
- Event replay can reconstruct every authoritative state transition.
- Deleting projections or snapshots cannot delete semantic history.
- CAS tampering and missing artifacts fail closed.

## Verification

Property-test reducer purity and replay equivalence. Test projection rebuild,
snapshot rejection/rebuild, artifact digest verification, and absence of
duplicated mutable semantic records.
