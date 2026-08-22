# ADR-0006: Recovery relations and future opaque benchmark

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-047, RCI-049, RCI-058–RCI-060, RCI-065–RCI-068

## Context

The retention note shows that failed recall does not erase retained learning: a
past state may still make later learning cheaper or safer. The opaque controlled
memory note is a strong end-to-end test, but importing its game/memory details as
core primitives would overfit the architecture and silently expand G1.

## Decision

Present use, reconstruction, direct consequence evaluation, and reacquisition
are independent route relations. A `RetentionPackage` may expose any subset.
Every route carries a `RecoveryLicense`. A `ReacquisitionScaffold` may retain
cues, probes, representations, methods, boundaries, failures, prerequisites,
and provenance, but recovery advantage requires checked comparison with a pinned
baseline and cost frontier. No universal scalarization is assumed. Forgetting is
reduced future recovery capacity; reopening may initiate relearning.

G2 makes retention, scaffold activation, and reacquisition inquiry executable.
G3 integrates route-specific recovery licences with compression, residue, and
frontier budgets. G1 provides only reusable event/effect/probe foundations.

The opaque controlled-memory environment is a staged G7 benchmark binding, not a
core primitive or current test. Earlier Goals may verify individual
prerequisites. A future Predictive State Representation/system-identification
adapter is preferred to inventing hidden state. The linear consequence theorem
applies only after a warranted vector representation and linear protected query
family exist.

## Consequences

Under RCI v0.4, these route relations may consume a licensed history-state
representation, but a retained package or route declaration alone remains
neither that representation nor its license. Competence equivalence is
binding-typed and is identified with history consequence equivalence only when
the binding declares the same carrier.

- Memory can be evaluated without equating it with recall or historical object
  identity.
- Reacquisition claims remain empirical, scoped, and reproducible.
- Raw-byte environments cannot bypass actuality, warrant, or control boundaries.
- G1 remains finite and credential-free.

## Verification

G2/G3 tests will pin baseline, protocol, evaluator, cost dimensions, and
frontier ordering; demonstrate useful and non-useful scaffolds; and test
reopening into relearning. G7 will stage the opaque benchmark progression and
transfer conditions. None of these is a G1 blocking test.
