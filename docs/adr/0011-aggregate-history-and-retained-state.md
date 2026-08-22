# ADR-0011: Aggregate, realized history, and retained consequence state

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-002, RCI-008, RCI-023, RCI-024, RCI-047–RCI-050,
  RCI-054, RCI-059, RCI-065–RCI-071

## Context

The sealed G1/G2 implementation has a replay-complete event aggregate,
recurrent-probe traces, provisional retention packages, semantic repair records,
and learned-probe admission. The pre-v0.4 compression plan did not state sharply
enough which carrier a quotient consumed. This allowed the word “state” to blur
four different roles: authoritative aggregate, realized interaction history,
configuration projection, and consequence-sufficient retained state.

## Decision

The immutable ledger and CAS remain durable authority. Repeated `evolve` is the
authoritative aggregate fold and `InquiryState` is its codomain. A binding may
derive realized interaction history through a versioned partial relation and
may project that history to a configuration. Neither relation is inferred from
ledger sequence or class names.

A G3 retained representation consumes an explicitly declared source carrier and
is validated only relative to a pinned horizon, consequence equality, and scope.
For a history-state claim, consequence factorization and continuation descent
are independently checked. The deterministic `evolve` reducer and any
retained-state update function are different operations.

The following never collapse by convention:

```text
aggregate fold != retained-state representation
configuration projection != history quotient
ProbeTrace != realized history
RetentionPackage != licensed retained state
MemoryPatchCandidate != representation refinement
PathResidue != open support dependency
```

The existing G2 retention package and routes remain provisional and unchanged.
G3 joins them to an independently validated compression application and a
standing route-specific recovery license through new records.

Representation replacement is not last-write-wins. A strict successor preserves
every still-valid protected predecessor competence, has a typed strict gain, and
has independent standing warrant. Independently invalid claims may receive an
exact warranted disposition. Scope tradeoffs and mutual non-dominance remain an
explicit frontier.

## Consequences

- G1/G2 event classes and meanings do not change.
- New G3 contracts must name source/target carrier roles and schemas.
- `InquiryState` remains complete even when a retained representation removes
  protected-irrelevant history distinctions.
- Answer sufficiency cannot be advertised as recursively executable state
  without continuation compatibility.
- G3A is split internally: history-state foundations precede the exact linear
  binding.
- The unary parity fixture is finite-state over an unbounded unary-history
  carrier; exactness uses transition congruence, not bounded sampling.

## Verification

Governance checks require RCI-001–RCI-071 parity and frozen G1/G2 schemas. G3A-H
acceptance must prove the parity and order-sensitive fixtures, stage separation,
carrier rejection, continuation failure, residue/reopening, representation
frontier behavior, and replay compatibility.

