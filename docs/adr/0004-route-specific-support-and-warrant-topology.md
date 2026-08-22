# ADR-0004: Route-specific support and warrant topology

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-028–RCI-034, RCI-036

## Context

A proposition may have multiple independent support environments. Flattening
their assumptions into one guard makes loss of one route deactivate valid
alternatives. Conversely, sharing unresolved dependencies without provenance can
license a proposition through itself.

## Decision

`SupportEnvironment`, `SupportRoute`, and each route's required/open dependency
boundary are explicit immutable records. Environment realizability and route
certificates reference separately owned evidence and independent checker
verdicts. Active support is derived: at least one applicable hard-warranted route
must remain closed. Current minimal routes form a policy/scope/binding/universe
antichain; dominated routes remain immutable history and may re-enter after a
standing change. Checked defeating environments are aggregate-owned nogoods.

Hard promotion records separate `LemmaVersion`, `LemmaSupport`, and
`PromotionLink` owners; `WarrantedLemma` and L3 active theory are derived views,
and the source claim is never mutated. Positive warrant cycles and ancestry
cycles are rejected atomically under the active policy. Cyclic structures from
research drafts may be stored as inert candidate data only. Guard, support-route,
and nogood standing changes append history; exact theory-selector pins cover
scope, binding, universe, and policy. Restoration or re-selection re-evaluates
applicability without erasing provenance.

Backend output and reification are not warrants. Witness, exhaustive finite
UNSAT, and solver-trusted results keep the exact scoped policies in the root
specification.

## Consequences

- Loss of one support route does not destroy another.
- Every active hard conclusion remains auditable to independent checked support.
- Dependency residue can survive compression without being falsely discharged.

## Verification

Test alternate-route survival, antichain minimization, guard
deactivation/reactivation, nogood blocking, scope isolation, positive cycle and
ancestry-cycle rejection, and atomic rollback on failed promotion.
