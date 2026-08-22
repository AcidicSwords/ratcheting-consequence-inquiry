# Proposed Goal G2B: Consolidation, reconsolidation, and probe learning

Create this Goal without a token budget.

## Target

Build and verify RCI v0.3.1 milestone G2B as defined by `PLAN.md` and ADR-0010.

Follow root `AGENTS.md`. Treat `RCI_Project_Spec.tex` as semantic authority,
`PLAN.md` as approved architecture and sequence, this Goal as the completion boundary,
and `docs/requirements-matrix.md` as the coverage ledger. Preserve sealed G1/G2A and
complete only the remaining RCI-058 slice.

Deliver:

1. Deterministic `consolidation-interleave-v1` checkpoints over exact owned recent
   episodes, older exceptions, and accepted counterexamples. One episode cannot
   self-consolidate. A proposal creates only an ordinary provisional generalization,
   candidate support/applicability boundary, and explicit attack/dependency obligations.
2. Versioned `MemoryPatchCandidate` and `ReconsolidationLink` repair. Mismatch may propose
   but cannot select a repair. Checked application appends successor lemma and correction,
   preserves the predecessor, keeps ancestry acyclic, and transports every unresolved
   dependency unless exact hard evidence discharges it.
3. Derived `conservative-question-field-v1` fields with stable priority and a 32-item
   bound. Overflow stays undetermined and creates a residual. Irrelevance requires active
   exact hard consequence-null warrant plus reopening. Evaluation is independently
   recomputed diagnostic evidence; model relevance cannot suppress inquiry.
4. `RepresentationGap`, `LearnedProbeCandidate`, `ProbeEvaluationProtocol`,
   `ProbeEvaluation`, and `ProbeAdmissionDecision` using inert
   `learned-recurrent-probe@1.0.0`, deterministic `finite-stratified-holdout-v1`, positive
   nonredundant holdout discrimination, completed attacks, independent checks, and
   `g2b-probe-admission-v1`. Generated probes cannot self-check, self-admit, bypass generic
   admission, create lemmas/licences/control, or gain global scheduling authority.
5. New version-1 G2B event kinds, folded-state schema v3, deterministic snapshot rebuild,
   and sealed G1/G2A replay/schema compatibility. Add SDK operations and canonical-JSON
   CLI commands under `memory`, `field`, and `probes`.

Use the finite circuit to prove older-counterexample interleaving, ordinary-warrant
generalization, immutable repair, conservative field coverage, and checked admission of a
nonredundant backup-power probe that changes later inquiry.

## Completion gate

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
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py
uv run rci --help
uv build
```

The G2B focused command must appear identically in AGENTS, PLAN, this Goal, CI, and
verification. Completion also requires all five protected hosted Windows/Linux/extras/
Docker checks and the post-merge `main` workflow.

## Explicit exclusions

Do not implement recovery licensing, retained-learning certification, self-cleaning or
compression economics, exact/approximate compression, the linear quotient engine, native
adapters, AALpy or learned automata, CHC/PDR, controller synthesis, multi-backend warrant,
UI, servers, deployment, releases, or the opaque controlled-memory end-to-end benchmark.
Missing optional or live capabilities do not block G2B.
