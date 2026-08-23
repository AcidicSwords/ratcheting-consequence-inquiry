# ADR-0015: Bounded review equivalence remains a deferred candidate

- Status: accepted design; G3V implementation stopped indeterminate and unpromoted
- Date: 2026-08-22
- Requirements: RCI-077, RCI-078, and RCI-079

## Context

G3R separates development evidence, fresh exact-head review, successor decision, and
external promotion. Local-model availability and format compliance varied, motivating a
candidate model-disconnected review route over a closed seeded fault family.

The G3V candidate at `a425f4b0dfa5b2c52a67df87d460f25e4e825518` passed its local and
hosted mechanical gates. Fresh semantic review from a context distinct from the
developer was unavailable. The bounded profile is expressly unable to substitute for
that review, so the candidate did not satisfy its own promotion boundary.

## Decision

The bounded-review design is retained as a deferred candidate:

1. A future `MechanicalReviewContract` may pin an exact Goal, candidate environment,
   base/head commits, gate, evidence, invariants, and a closed fault family.
2. Its strongest positive result is `valid_within_profile`; unbounded semantic coverage
   remains `Unknown`.
3. Such a result cannot become an `IndependentReview`, warrant a successor, satisfy a
   fresh-review requirement, or authorize promotion.
4. Model-generated breakers remain strictly parsed inert candidates. Malformed output
   remains indeterminate.

No G3V implementation is part of the protected baseline. RCI-079 remains unverified and
deferred. Reopening requires a new Goal with fresh independent review available or a
different discriminator that does not weaken G3R.

## Consequences

The candidate branch and pull request remain as historical evidence. Its passing CI
proves only that the candidate met its executable bounded profile; it does not establish
the semantic adequacy needed for protected promotion.
