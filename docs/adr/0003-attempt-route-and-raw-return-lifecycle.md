# ADR-0003: Attempt, return route, and raw-return lifecycle

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-017–RCI-023

## Context

Earlier drafts blurred a requested external action, an execution attempt, a
transport outcome, the returned bytes, and their interpretation. That permits
timeouts to masquerade as logical results and allows retries to overwrite
actuality.

## Decision

External work begins only after replay-owned `StepPlanRecorded` and
`EffectRequested` events. One request may have multiple delivery attempts. A
planned attempt must be explicitly started before execution and every started
attempt ends in exactly one typed outcome: `NotPresented`,
`PresentationUnknown`, `CaptureFailed`, `Cancelled`, or `Returned`, with closed
reason enums. `NoAttempt` is a plan disposition and never invents an attempt.
At most one decoded result is accepted for a request; duplicate or late
deliveries remain in attempt history but cannot replace that acceptance.

A returned attempt uses a snapshot of a versioned allowlisted `RouteDefinition`.
Its distinct `ExternalReturn` preserves exact captured bytes in CAS before
decoding. Decode outcome, inert evidence, independent checker verdict, warrant
decision, effect-result acceptance, and semantic promotion remain separate
records/events. Absent, null, empty, false, malformed, and undecodable payloads
stay distinct.

Prediction seals must precede the relevant attempt; mismatch requires a genuine
decoded return. Replay folds recorded events and never invokes an adapter.

## Consequences

- At-least-once execution is compatible with deterministic, idempotent
  acceptance.
- Transport failure and timeout cannot prove semantic or logical propositions.
- New return formats are added as registered routes rather than ad hoc parsing.
- Raw evidence remains available after decoders evolve.

## Verification

Test crash points around request/start/return/accept, retry cardinality,
first-acceptance wins, duplicate and late returns, timeout versus unknown,
fail-closed decoder errors, raw-byte preservation, and zero adapter calls during
replay.
