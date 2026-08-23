# Active Goal G3K-E: Executable succession-arrangement kernel

- Status: active
- Authority: RCI v0.6, PLAN, ADR-0018
- Anchor: `d6e101bb01271179f3416c3ecc61082bcdb6b873`
- Token budget: none

## Sealed relation

Current: G3K-S has normalized the semantic distinction among binding-derived realized
effect/return succession, typed arrangement, and candidate recognition, but those
relations have no executable typed kernel or durable owned interaction lifecycle.

Desired: a dependency-free `rci.calculus` implements strict finite interfaces, typed
represented effects and returns, arrangements, static relational lowerings, question
frames, checked answer-conditioned guarded programs, candidate-only recognition, and
checked persistence/reopening. Additive version-1 events own candidate programs,
admission decisions, occurrences, checked frame observations, and selected
continuations. Folded state advances to v7 and rebuilds v1--v6 from the unchanged
ledger. Legacy `QuestionContract` remains exactly readable through conservative
compatibility adapters or explicit projection failure.

Separator: the focused fixture must distinguish arrangement composition from realized
succession; execute `Vis(e,kappa)` only through an existing persisted effect request;
preserve partial, exterior, malformed, operational, and checker stages; make binary
crossing involutive; keep recognized fragments inert; reopen a broken fold; reproduce
the two G3K-S incumbent failures; and replay byte-equivalently without self-authority.

Preserve: RCI-001--RCI-079 dispositions, sealed event bytes and meanings, all eight
`core-v1` render/bind behaviors, G2B/G3Q/G3G admission boundaries, aggregate/history/
retained-state separation, effect stage separation, `Unknown`, every predecessor gate,
and the absence of arbitrary code, tool, source, Git, warrant, review, or promotion
authority in grammar records.

## Focused gate

```text
uv run pytest -q tests/acceptance/test_effect_distinction_question_grammar.py
```

