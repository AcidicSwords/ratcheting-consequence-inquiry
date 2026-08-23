# Active Goal G3K-S: Succession-arrangement semantic normalization

- Status: verified and promoted through protected main at `d6e101bb01271179f3416c3ecc61082bcdb6b873`
- Authority: RCI v0.6 candidate normalization, PLAN, ADR-0016, ADR-0018
- Anchor: `7aa670482af85a9fd554a31924dbce6a26984af4`
- Token budget: none

## Sealed relation

Current: RCI has replay authority, realized-history derivation, typed effects, questions,
checks, retained representations, and project ratchets, but the semantic root remains
distributed across these specializations. `QuestionContract` has one static inert answer
shape and static successor-rule identifiers; G3Q rejects generated successor rules and
cannot preserve a partial answer as several live cells.

Desired: RCI v0.6 normatively distinguishes linear realized effect/return succession,
typed arrangements between successive interactions, and piecewise recognition of
recurrent arrangements. Questions, open relations, Boolean formulas, and native methods
become typed front ends/specializations. No executable G3K kernel is claimed in G3K-S.

Separator: two owned incumbent bindings must reproduce (1) rejection of general
answer-conditioned continuation and (2) collapse of a genuinely partial multi-cell
answer to one unclassified residual. The specification must then define RCI-080--RCI-086
without changing any sealed event meaning or claiming those requirements verified.

Preserve: RCI-001--RCI-079 dispositions, ledger/CAS authority, aggregate/history/state
separation, effect stage separation, `Unknown`, the eight `core-v1` contracts, G2B/G3Q
admission boundaries, every predecessor gate, and no execution/warrant/review/promotion
authority for generated syntax.

## Focused gate

```text
uv run pytest -q tests/acceptance/test_g3k_semantic_normalization.py
```

G3K-E may open only after this semantic Goal is independently reviewed and promoted.
