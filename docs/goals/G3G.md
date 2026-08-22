# Goal G3G: Confined implementation-Goal synthesis

- Status: sealed and verified under the distinct no-budget G3G Goal
- Selection anchor: protected `main` at
  `60ff25635f94fb004e6419a09293c5e0fc023074`
- Development anchor: protected `main` after selection evidence closeout at
  `defeb5c2dad32b86cc1861d4f3c35522a3f0497f`
- Promotion boundary: implementation began only from the exact development anchor,
  merged through protected pull request 12 as
  `5f48d397030b6a063fdca19e51b70a824096e564`, and preserves the selection anchor as
  immutable decision provenance
- Authority: RCI v0.5, PLAN, ADR-0012 through ADR-0014, and
  `frontier-post-g3q-v1`
- Token budget: none

## Current and desired relation

Current: G3Q can schedule an admitted project question and route its provisional return
to a typed downstream obligation. G3R can seal an `ImplementationGoalContract`, but an
external orchestrator must manually translate the return and selected frontier candidate
into every Goal field.

Desired: an exact owned admitted return, clean anchor, consequential limitation, ready
frontier, and selected candidate deterministically compile to one inert
`ImplementationGoalCandidate`. A separate versioned controller decision may admit the
candidate into the existing immutable Goal seal. No generated payload chooses commands,
paths, policy, evidence, warrant, review, execution, or promotion.

## Separator

Before G3G, two independently admitted return classes may open distinct downstream
obligations but neither can produce an auditable Goal candidate. After G3G, an exact
`goal-derivation-required` return for the selected frontier member produces one canonical
candidate whose acceptance and mutation surfaces come only from allowlisted registries.
The alternate `method-transport-required` return produces a different downstream state,
and unmatched, stale, foreign, ambiguous, or `Unknown` input produces no Goal candidate.

## Required implementation

- Add strict frozen version-1 `ImplementationGoalCandidate` and
  `GoalAdmissionDecision` records and only the new event/command kinds required to own
  them. Do not mutate any sealed G1 through G3Q event schema or meaning.
- Compile from the exact owned question candidate/decision/compiled contract, accepted
  decode, provisional source claim, and generated downstream obligation, plus
  `ProjectAnchor`, `CapabilityLimitation`, ready `CapabilityFrontier`, and its exact
  selected `CapabilitySuccessorCandidate`. All return-class and source links must agree.
- Pin source fingerprints, compiler/controller policies, scope/binding/horizon, anchor,
  limitation, frontier, selected candidate, gate registry, mutation registry, rollback,
  reopening, and all derived Goal fields.
- Source acceptance commands only from a versioned allowlist. Preserve the complete
  incumbent gate and add exactly one bounded focused discriminator; free-form return data
  cannot introduce argv, shell syntax, environment expansion, or a weaker gate.
- Source mutation roots only from a versioned allowlist. Reject absolute paths,
  traversal, overlaps with forbidden authority roots, and any source/Git/
  policy/credential/release/deployment expansion.
- Keep candidate generation, admission, Goal sealing, candidate actualization,
  development evidence, independent review, successor decision, and external promotion
  as separate stages.
- Expose deterministic SDK and canonical-JSON CLI inspection/recording without adding an
  execution port.

## Acceptance

```text
uv run pytest -q tests/acceptance/test_goal_synthesis.py
```

Acceptance must cover exact return-to-candidate derivation, permutation stability,
two-return downstream distinction, exact anchor/frontier/candidate/context pins,
stale/foreign/ambiguous/Unknown inertness, command and path injection containment,
predecessor-gate non-weakening, forbidden-root isolation, one total admission decision,
no self-admission/seal/execution/warrant/promotion, replay/export identity, archived
G1-G3Q compatibility, and canonical CLI/SDK parity.

## Exclusions

No general autonomous planner, free-form Goal generation, model-ranked roadmap, method
installation, arbitrary command execution, source-writing port, Git/worktree actuator,
credential or policy access, merge/release/deployment authority, G3A-L/SymPy, G3B, G3C,
G4, G5, G6, or G7.

## Stop and reopening

Return `Unknown` if exact owned records plus the allowlisted profiles cannot determine a
Goal without inventing semantic content. Roll back if any predecessor gate or authority
boundary weakens. Reopen when an admitted project return lawfully requires a Goal shape,
acceptance mechanism, or mutation surface outside the confined registries.
