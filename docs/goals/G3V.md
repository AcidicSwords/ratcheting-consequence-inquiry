# Goal G3V: Bounded review equivalence

- Status: active under a distinct no-budget Goal
- Anchor: protected `main` at `b6069c0a58a669eed21005bada407eff1828071a`
- Authority: RCI v0.5, PLAN, ADR-0012, ADR-0013, ADR-0015, and
  `post-g3g-review-frontier.md`
- Token budget: none

## Current and desired relation

Current: a malformed or unavailable secondary model lawfully yields `Indeterminate`, but
there is no typed way to establish what a deterministic review route covers while the
model is disconnected.

Desired: an exact sealed Goal, candidate environment, candidate head, gate, evidence
bundle, and versioned seeded fault family compile to a deterministic assessment. The
assessment is `invalid`, `indeterminate`, or `valid_within_profile`; it always preserves
unbounded semantic residue as `Unknown`.

## Required implementation

- Strict frozen v1 records for the mechanical contract, fault observations and manifest,
  bounded assessment, inert semantic breaker candidate, and malformed-model disposition.
- A closed `project-review-faults-v1` registry covering exact-head substitution,
  evidence substitution, self-review, stage collapse, `Unknown`-as-success, gate
  weakening, allowlist broadening, and replay/effect collapse.
- Pure permutation-stable compilation and assessment with exact IDs/fingerprints.
- Strict parsing of model JSON. Prose, code fences, extra fields, wrong commits,
  duplicated faults, and invented fault identifiers remain `Indeterminate`.
- SDK and canonical-JSON CLI inspection only. No event, snapshot, dependency, network,
  model, execution, source, Git, credential, policy, release, deployment, or promotion
  authority.

## Acceptance

```text
uv run pytest -q tests/acceptance/test_review_equivalence.py
```

Acceptance proves model-disconnected permutation stability, complete seeded-fault
detection, surviving-fault rejection, stale/foreign/duplicate/missing evidence
indeterminacy, exact Goal/environment/head/gate pins, malformed-Qwen containment,
well-formed breaker inertness, unbounded semantic `Unknown`, CLI/SDK parity, and the
inability to satisfy `IndependentReview` or promotion.

## Stop and reopening

Stop after the bounded assessment and parsing seam is verified. Do not integrate an
Ollama transport or substitute promotion review. Reopen for a surviving seeded fault, a
new reproducible breaker class, or a separately admitted policy-comparison Goal.
