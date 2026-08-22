# Proposed Goal G2A: Deterministic retrieval, reconstruction, and recovery

Create this Goal without a token budget.

## Target

Build and verify RCI v0.3.1 milestone G2A as defined by `PLAN.md` and ADR-0009.

Follow the root `AGENTS.md`. Treat `RCI_Project_Spec.tex` as semantic authority,
`PLAN.md` as approved architecture and sequence, this active Goal as the
completion boundary, and `docs/requirements-matrix.md` as the honest coverage
ledger. G2A and G2B are internal delivery gates under stable requirement RCI-058;
do not renumber requirements or claim the deferred G2B slice.

Preserve the verified G1 baseline and deliver a deterministic, offline-first G2A
slice with:

1. **Structural retrieval and reconstruction**
   - Strict frozen versioned `RetrievalQuery`, `RetrievalHit`, and
     `RetrievalResult` records plus a versioned structural retrieval policy.
   - Deterministic matching over owned typed references, exact rank components,
     stable-ID tie breaking, scope/binding isolation, deduplication, bounds, and
     stale-reference rejection. Add no embeddings or retrieval dependency.
   - Ambiguous reconstruction remains an ordered candidate set. Retrieval and
     reconstruction become neither history, knowledge, support, nor warrant;
     model relevance cannot suppress a result or inquiry.

2. **Non-compressive retention relations**
   - A `RetentionPackage` that references separate provisional, unlicensed
     `DirectUseRoute`, `ReconstructionRoute`, `ConsequenceEvaluationRoute`, and
     `ReacquisitionRoute` records, plus a `ReacquisitionScaffold`.
   - Keep direct use, reconstruction without substantial new evidence, direct
     consequence evaluation, and reacquisition with new evidence or practice
     distinct. Generated reconstruction detail cannot become historical fact.
   - A G2A route is a candidate description, not a protected capability. Do not
     create or imply a `RecoveryLicense`; route licensing begins in G3A.

3. **Measured reacquisition**
   - Versioned `RecoveryProtocol`, typed `CostAxis`/`CostVector`, immutable
     `RecoveryObservation`, derived `RecoveryFrontier`, and provisional
     `RecoveryComparison` records.
   - Pin the same target competence, circuit universe, binding, horizon,
     evaluator, evidence access, budget, protocol, and comparison policy for
     baseline and retained observations.
   - Require matching named axes with exact nonnegative values. Advantage is a
     checked strict Pareto improvement: all retained costs no worse and at least
     one strictly better. Incomparable vectors, eventual success alone, or pin
     mismatch establish no advantage.
   - Independent checking makes a comparison provisional/soft only. It cannot
     self-warrant, promote a hard lemma, or create a recovery license.

4. **Resumable parent/child inquiry saga**
   - Add `ReacquisitionRequested` and `ReacquisitionInquiryLinked` records and
     corresponding new version-1 event kinds without changing G1 event schemas.
   - Reuse the existing persisted effect/request/attempt/return protocol.
     Parent request, child inquiry creation, and parent linkage are separately
     resumable; every partial prefix remains open rather than fabricating
     success.
   - Advance snapshot/projection schema versions only where needed, rebuild old
     derived state, and prove archived G1 streams replay with unchanged G1
     semantics.

5. **SDK, CLI, and finite reference evidence**
   - SDK operations for deterministic retrieval, retention registration,
     reacquisition start/link, recovery observation, and frontier comparison.
   - CLI `memory retrieve`, `recovery start`, `recovery inspect`, and
     `recovery compare`, all with canonical JSON output.
   - A paired circuit fixture where the retained branch stores cues, probe order,
     boundaries, and failures but not the target answer; the baseline has no
     scaffold; both use the same finite evidence universe and target competence.
   - The positive fixture shows strict Pareto improvement in logical
     probe/effect cost with no worse declared axis. Negative fixtures reject
     eventual-success-only, incomparable, protocol-mismatched, and
     evaluator-mismatched claims.

## Completion gate

Preserve and pass the complete frozen G1 gate:

```text
uv lock --check
uv sync --dev
uv run python -c "import rci"
uv run pytest -q -m "not optional"
uv sync --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/rci tests
uv run pytest -q
uv run pytest -q tests/acceptance
uv run rci --help
uv build
```

Also pass this focused G2A acceptance command, identically recorded in
`AGENTS.md`, `PLAN.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
```

Blocking evidence additionally covers retrieval permutation stability,
scope/binding isolation, exact deduplication, bounds, stale-reference rejection,
ambiguous reconstruction, route no-collapse, generated-detail containment,
crash/resume at every parent/child saga boundary, exact frontier comparison,
checker independence and non-promotion, G1 replay compatibility, both existing
reference conclusions, and unchanged backlog authority.

## Explicit exclusions

Do not implement or claim conformance for G2B consolidation,
reconsolidation, semantic-field evaluation, learned probes or automata; any hard
recovery licence or finding that retained learning has been established;
compression, exact quotient, or the linear theorem; CHC/PDR; controller
synthesis; multi-backend evidence; UI, servers, deployment, release, or the
opaque controlled-memory end-to-end benchmark. Preserve those requirements for
later Goals.

Missing OpenAI, Z3, Docker, GPU, live services, and later research capabilities
do not block G2A.
