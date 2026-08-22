# Sealed next Goal G3Q: Regenerative question-contract synthesis

- Status: sealed next; inactive until G3R is verified and merged
- Authority: RCI v0.5, PLAN, ADR-0012, G3R frontier `frontier-g3r-roadmap-v1`
- Token budget: none

## Current and desired relation

Current: RCI can schedule allowlisted built-in contracts, admit one fixed learned-probe
shape, and record an inert `QuestionContractCandidate`, but the ordinary scheduler cannot
compile and run an admitted generated question operator.

Desired: an admitted generated question contract can enter only the confined
`recursive-project-v1` profile and deterministically open a typed project obligation,
produce inert candidate returns, and feed a downstream frontier without executing code,
selecting policy, suppressing ordinary inquiry, or promoting its own output.

## Separator

Before G3Q, admitting a valid generated contract does not make it schedulable. After
G3Q, the same exact admitted contract is selected only when its typed preconditions and
project limitation match; its two consequential return classes produce different typed
downstream obligations. An unadmitted, stale, scope-mismatched, malformed, or
single-consequence contract remains inert.

## Required implementation

- Add a versioned, data-only generated-contract compiler for the existing safe question
  AST/template boundary; no imports, arbitrary callables, tools, commands, SQL, network,
  or policy selection.
- Join `QuestionRepertoireDecision(ADMIT)` to a confined registry projection without
  changing sealed G1/G2/G3 event schemas or broadening `core-v1`.
- Extend project scheduling with exact limitation, anchor, contract version, binding,
  scope, comparison-policy, and admission-policy pins.
- Preserve built-in scheduling, learned-probe admission, ordinary unresolved
  obligations, model-irrelevance non-suppression, replay determinism, and Unknown.
- Keep generated answers provisional and route them through the existing effect,
  decode, checker, warrant, and promotion stages.
- Record a repertoire-successor decision only after nonredundancy, attack, holdout or
  finite discrimination evidence, and controller admission; generation alone is inert.

## Acceptance

```text
uv run pytest -q tests/acceptance/test_regenerative_questions.py
```

The acceptance must cover admission-to-scheduling, deterministic order, exact scope and
binding isolation, stale-policy rejection, two-return downstream divergence, malformed
and prompt-injection payload containment, non-suppression, replay/export identity,
unadmitted-candidate inertness, built-in contract non-regression, and absence of any
self-warrant or source/Git authority.

## Exclusions

No free-form generated Python, general autonomous planner, arbitrary contract profile,
model-ranked relevance, source modification port, G3A-L/SymPy, native-method adapter,
G4 formal machinery, control, release, deployment, or merge authority.
