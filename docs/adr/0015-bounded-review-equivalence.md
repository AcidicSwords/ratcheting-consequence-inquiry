# ADR-0015: Bounded mechanical review equivalence

- Status: accepted for active G3V implementation
- Date: 2026-08-22
- Requirements: RCI-077, RCI-078, and RCI-079

## Context

G3R correctly separates development evidence, fresh exact-head review, successor
decision, and external promotion. It currently records reviewer identity and context but
not the review relation or its declared fault coverage. Local-model availability and
format compliance have varied, so making a particular model a blocking authority would
convert an optional search method into a hidden availability dependency.

## Decision

G3V introduces a model-disconnected bounded review route:

1. A versioned `MechanicalReviewContract` pins the exact Goal, candidate environment,
   base/head commits, gate, evidence, required invariant identifiers, and a closed fault
   family.
2. A versioned `FaultObservationManifest` records the exact seeded probe and its
   evidence/reproducer digest. Pure profile logic independently recomputes the
   disposition rather than trusting a caller-supplied label.
3. Pure assessment returns `invalid` for any surviving fault, `indeterminate` for absent,
   stale, foreign, duplicate, or mismatched evidence, and at most
   `valid_within_profile` when the complete declared family is detected.
4. Unbounded semantic coverage is always `Unknown`. The assessment cannot be re-labeled
   as `IndependentReview(VALID)`, satisfy a G3R successor decision, warrant a claim, or
   authorize promotion.
5. Strict `SemanticBreakerCandidate` parsing keeps a model return inert and exact-head
   pinned. Malformed output is a typed `ModelReviewIndeterminate`; a well-formed breaker
   remains only a candidate until its reproducer becomes ordinary development evidence.

No model client, network call, dependency, command runner, source writer, Git port, or
promotion-policy substitution enters G3V. A schema-constrained Ollama adapter remains a
later method candidate behind the existing effect protocol.

## Consequences

The project gains deterministic evidence about a declared review fault family when all
models are disconnected. It does not gain proof that no unimagined semantic defect
exists. Review-route substitution may be considered only after G3V evidence exists and
requires a separate Goal and policy decision.
