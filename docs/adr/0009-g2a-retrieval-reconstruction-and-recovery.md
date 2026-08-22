# ADR-0009: G2A deterministic retrieval, reconstruction, and recovery

- Status: Accepted
- Date: 2026-08-22
- Requirements: RCI-024, RCI-047, RCI-049, RCI-058, RCI-065--RCI-067
- Amends: ADR-0006

## Context

RCI-058 groups retrieval, reconstruction, consolidation, reconsolidation,
retention, semantic-field evaluation, learned probes, and reacquisition into G2.
That surface is too broad for one useful failure boundary. The first executable
slice needs to prove deterministic retrieval and measured recovery without also
allowing consolidation, learned procedures, compression, or a recovery claim to
authorize itself.

ADR-0006 also says that every recovery route carries a `RecoveryLicense`, while
RCI-059 assigns route-specific license enforcement to G3A. Treating a G2 route
candidate as already licensed would therefore claim a G3 capability early.

## Decision

RCI-058 is delivered through two internal gates without changing its stable
requirement ID:

- **G2A** implements deterministic structural retrieval, candidate
  reconstruction, non-compressive retention registration, reacquisition as an
  ordinary child inquiry, and checked recovery observations/comparisons.
- **G2B** later implements consolidation, reconsolidation, semantic-field
  evaluation, and candidate learned probes/automata.

G2A has these ownership boundaries:

- `M_L` owns registered `RetentionPackage`, provisional route descriptions,
  `ReacquisitionScaffold`, `RecoveryProtocol`, and recovery observations.
- Existing `A` records continue to own effect requests, attempts, returns, and
  decodes used by a reacquisition inquiry.
- Parent/child saga events own request and linkage facts; derived saga status and
  recovery frontiers are rebuildable views.
- Retrieval and reconstruction outputs are immutable candidates. They are not
  episodic history, semantic knowledge, support, warrant, or promotion.

The public G2A route records are deliberately **provisional and unlicensed**.
`DirectUseRoute`, `ReconstructionRoute`, `ConsequenceEvaluationRoute`, and
`ReacquisitionRoute` describe distinct candidate recovery relations. In
particular, `ReconstructionRoute` is not the licensed G3
`ObjectRegenerationRoute`. An unlicensed route cannot be selected as a protected
retention capability, cannot satisfy RCI-049, and cannot establish that retained
learning exists. G3A introduces and enforces `RecoveryLicense` and the licensed
capability view required by RCI-049 and RCI-067. This paragraph supersedes only
the premature licensing sentence in ADR-0006; its no-collapse and benchmark
decisions remain accepted.

Retrieval is a pure structural match over owned typed references. A versioned
policy defines exact rank components, bounds, scope/binding compatibility,
deduplication, and stale-reference rejection. Results order by those exact
components and stable IDs. Floating relevance scores, embeddings, model
relevance, and a new retrieval dependency are excluded.

Recovery observations pin target competence, finite universe, binding, horizon,
evaluator, evidence access, budget, protocol, and comparison policy. Cost axes
are typed and named; values are exact and nonnegative. A retained observation
strictly Pareto-dominates a baseline only when their pins and axes match, every
retained cost is no worse, and at least one is strictly better. Incomparable
vectors establish no advantage. `RecoveryFrontier` is the derived nondominated
set. An independently checked `RecoveryComparison` remains provisional/soft: it
cannot create hard warrant, promote a lemma, or mint a `RecoveryLicense`.

Reacquisition reuses the existing event/effect protocol. A parent request, child
inquiry creation, and parent linkage form an append-only resumable saga. Any
partial prefix remains open. A timeout, crash, missing link, or eventual success
cannot fabricate advantage.

G2A adds new event kinds at schema version 1 and does not alter any G1 event
schema. Folded-state, snapshot, and projection schemas may advance. Unsupported
derived snapshots are discarded and rebuilt from the ledger; archived G1 event
streams must still replay with unchanged G1 semantics.

## Consequences

ADR-0011 adds a permanent boundary: `RetentionPackage` is not
`S_H`. G3 must link the unchanged package and provisional routes to an exact
compression application and route-specific recovery license through new
records; it must not retrofit fields into sealed G2A records.

- Retrieval/recovery behavior is deterministic, dependency-free, and suitable
  for native Windows/Linux blocking tests.
- The circuit can measure a scaffold advantage without storing the target answer
  or claiming a licensed memory capability.
- Partial reacquisition work is inspectable and resumable rather than coerced
  into success or failure.
- Consolidation, learned probes, compression, and recovery licensing retain
  independent later gates.

## Verification

G2A acceptance covers retrieval permutation stability, isolation, deduplication,
bounds, and stale references; ambiguous reconstruction; route separation;
parent/child crash-resume prefixes; exact Pareto comparison and pin mismatch;
non-promotion; the paired circuit fixture; and replay of archived G1 streams.
The focused command is:

```text
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
```
