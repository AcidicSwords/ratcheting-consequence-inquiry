# Goal G3K-E: Executable succession-arrangement kernel

- Status: stopped indeterminate
- Authority: RCI v0.6, PLAN, ADR-0018
- Anchor: `d6e101bb01271179f3416c3ecc61082bcdb6b873`
- Final candidate: `a4a769872832cbd46c7e10400e4f71195d2fb1e5`
- Token budget: none

## Sealed relation

Current: G3K-S normalized realized effect/return succession, typed arrangement, and
candidate recognition, but those relations had no executable typed kernel or durable
owned interaction lifecycle.

Desired: a dependency-free `rci.calculus` with strict finite interfaces, represented
effects and returns, arrangements, relational lowerings, checked question frames,
answer-conditioned guarded programs, conservative legacy adapters, additive version-1
events, and a rebuildable v7 folded state.

Separator: arrangement composition remains distinct from realized succession; existing
persisted effects alone actualize represented nodes; partial/exterior/indeterminate
stages remain distinct; checked answers select only their exact successor; recognition
remains inert; broken persistence reopens residue; replay remains deterministic.

Preserve: RCI-001--RCI-079, sealed predecessor event meanings, all eight `core-v1`
contracts, stage separation, `Unknown`, predecessor gates, and absence of arbitrary code,
source/Git, warrant, review, or promotion authority.

## Focused gate

```text
uv run pytest -q tests/acceptance/test_effect_distinction_question_grammar.py
```

## Disposition

Candidate `a4a769872832cbd46c7e10400e4f71195d2fb1e5` passed every local and hosted gate.
An intermediate exact-head review returned `INVALID`; its reproducible authority findings
were repaired. Fresh distinct-context review of the repair head remained unavailable, so
PR #22 was closed without merge and the candidate branch retained. G3K-E is not standing
capability. Reopening requires fresh exact-head semantic review of the retained candidate
or a newly sealed successor Goal.
