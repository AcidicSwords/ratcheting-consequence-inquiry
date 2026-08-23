# RCI repository instructions

## Authority

Work as a repository-grounded coding agent.

1. Direct user instructions control requested intent within runtime authority.
2. `RCI_Project_Spec.tex` v0.5 is the semantic authority.
3. `PLAN.md` fixes approved architecture, defaults, and sequencing.
4. The active Goal fixes the current completion boundary.
5. `docs/requirements-matrix.md` and `docs/adr/` record reconciliation and deferral.
6. Code, tests, and returns are implementation evidence; they never silently amend the
   specification.

Files under `docs/spec/sources/` are preserved historical inputs, not live instructions.
When authorities appear to conflict, localize the conflict, preserve established
invariants, record the resolution or open ambiguity, and do not make a broader semantic
decision merely to make code pass.

## Recursive coding ratchet

Use this internally without narrating it mechanically:

`CONTRACT -> LOCATE -> BISECT -> ATTACK -> CHANGE -> VERIFY -> LEARN -> RECUR`

- Define the observable consequence and governing invariant.
- Inspect the actual code/data/path before editing.
- Isolate the smallest consequence-changing boundary.
- Seek a counterexample or alternate route.
- Make the smallest coherent reversible change.
- Run the strongest direct check plus relevant regressions.
- Preserve the learned boundary in a type, test, ADR, or requirement row.
- Continue with the smallest consequential residual inside the active Goal.

Preserve unrelated user work. Prefer read-only discovery, `rg`, explicit argv, and
batched independent checks. Never weaken an invariant, fabricate evidence, or declare
impossibility from timeout, failed search, or unavailable capability.

## Stack and repository conventions

- Python 3.12, `uv`, PEP 621, `src/rci`, Pydantic v2, Typer, stdlib SQLite.
- pytest, Hypothesis, Ruff, mypy, Apache-2.0, Windows/Linux GitHub Actions.
- Optional `openai` and pinned `z3-solver` extras. Base install, examples, replay, and
  blocking tests require no network, credentials, Docker, OpenAI, or Z3.
- Local single-user SDK/CLI first. UI, HTTP, PostgreSQL, distributed operation,
  deployment, and releases require later Goals.
- Docker is supplementary. Do not make a running local daemon a base requirement.
- Add dependencies only for an implemented capability whose contract cannot be met by
  the standard library or current dependencies. Record consequential choices in an ADR.
- Do not commit secrets, local databases, caches, generated evidence, unsanitized
  provider returns, or large runtime artifacts.
- Create future-phase packages only when implemented; no passing stubs or false
  conformance.

## Core architecture

```text
decide(state, command) -> events
evolve(state, event) -> state
EventStore.append(stream, expected_sequence, events)
plan_next(state) -> StepPlan
```

- Records/events are strict, frozen, tagged, and versioned.
- Reducers perform no I/O and generate no time, IDs, randomness, or provider metadata.
- The SQLite append-only ledger plus content-addressed artifacts is durable authority.
  Memory graphs, active theory, snapshots, indexes, semantic fields, and reports are
  projections.
- SQLite uses WAL, `BEGIN IMMEDIATE`, expected stream sequences, unique IDs, and one
  writer path per inquiry. Projection checkpoint and rows commit together.
- CAS bytes publish and verify before a ledger event references them. Replay never
  invokes effects and deterministic export must be byte-equivalent.
- External work begins only from a persisted effect request. Delivery is at-least-once;
  each attempt has exactly one terminal outcome; each logical request accepts at most
  one resolution.
- Keep plan disposition, attempt presentation, capture, raw return, decode, checker
  verdict, warrant decision, and promotion separate.
- Unknown event/schema versions fail closed. Add real upcasters when real compatibility
  data exists; do not invent legacy migrations in the greenfield schema.

Logical ownership is single-writer in the folded state:

- `M_E`: episodic records/artifact refs.
- `M_S`: semantic lemma versions.
- `M_P`: admitted procedures/probes/contracts/methods.
- `M_L`: G2A retention packages, provisional route/scaffold/protocol records, and
  recovery observations; licensed capabilities, residue, and compression remain G3.
- `W`: support environments/routes/dependencies/checks/nogoods/warrant.
- `A`: effects/attempts/routes/raw returns/decodes/reconstructions.
- `Pi`: prediction seals and warranted mismatches.

Do not create a second authoritative history or writable active-theory store.

The authoritative aggregate fold and retained-state representation are different:

```text
event prefix -> InquiryState -> binding-derived realized history
                             -> configuration projection
                             -> independently validated retained state
```

- Never infer realized succession from ledger sequence.
- Never infer a carrier role from a Python class name or the word `state`.
- `InquiryState` is replay-complete aggregate state, not compressed retained state.
- `ProbeTrace` is one comparable observational subtrace, not realized history.
- `RetentionPackage` is a provisional package, not a sufficiency proof or license.
- `MemoryPatchCandidate` repairs semantic memory, not a G3 representation map.
- A history quotient is executable state only after every declared continuation descends.
- Representation/path residue and open support dependency remain distinct.

## Effect and evidence rules

- `NoAttempt` is a plan disposition, not an attempt outcome.
- Attempt outcomes are `NotPresented`, `PresentationUnknown`, `CaptureFailed`,
  `Cancelled`, or `Returned`. Timeout may leave presentation unknown.
- Preserve exact returned bytes. JSON null, empty bytes, empty string, zero, and false
  are distinct.
- Decode is `Decoded | Malformed | Unsupported | Failed`.
- Check is `Valid | Invalid | Indeterminate | Timeout | Unsupported | Failed`.
- A backend cannot independently warrant its own answer merely by reporting success.
- Route definitions are allowlisted/versioned; each attempt persists a resolved route
  snapshot with redacted endpoint, versions, environment/request digests, and actual
  transform order. Never persist credentials.
- Late/duplicate returns can be preserved as rejected evidence but cannot supersede an
  accepted result.

## Semantic, support, and warrant rules

- Questions and generated payloads create typed provisional claims, never facts.
- Arbitrary empty, Unicode, binary, contradictory, malformed-looking, or
  prompt-injection payloads remain inert L0 data.
- Opaque prose cannot establish semantic contradiction, entailment, necessity,
  sufficiency, equivalence, generalization, impossibility, or control.
- L0 conflict requires explicit proposition identity, polarity, role, bound referents,
  and scope. Conflict is localized and non-explosive.
- Every proposed necessity, sufficiency, or prerequisite opens its counterexample or
  alternate-route attack unless identically discharged.
- Descriptive factorization, prediction, correlation, and may-reachability cannot create
  a control certificate.
- Support dependency boundaries are route-specific. Hard support requires an
  independently checked realizability verdict for its environment; no known
  contradiction is insufficient.
- Minimal supports are antichains only inside an identical conclusion/scope/binding/
  applicability/policy class. Preserve dominated routes historically.
- Ungrounded self-support remains open. Reject positive support and semantic ancestry
  cycles atomically. A checked cyclic mathematical argument is a certificate leaf, not
  a support-graph cycle.
- Hard promotion is exact, scoped, guarded, dependency-closed, independently checked,
  provenance-preserving, policy-authorized, and cycle-free.
- Promotion creates a linked lemma/L3 view; it never mutates an L0-L2 claim.
- Guard, support, or policy invalidation deactivates active effects without erasing
  history. Append suspension, supersession, or reopening.
- Model output and reification provide no warrant. A checked witness can hard-warrant
  only its exact scoped existential. Exhaustive UNSAT is hard only over a declared
  closed finite universe. Z3-only UNSAT is `solver_trusted` and soft.
- Timeout, failure, unsupported capability, indeterminacy, and exhausted search never
  prove impossibility, necessity, equivalence, or control. `Unknown` is lawful.

## Questions and cognitive spine

Question contracts are typed code with versioned inert templates. They may not import
code, execute tools/commands/SQL, or select arbitrary policy. Only allowlisted registry
entries run. Store the full catalog as data, but schedule only profiles whose capability
and tests exist. Generated contracts/probes are inert candidates until admitted by a
versioned human/controller policy.

The semantic field is a derived probe-conditioned view. Model-inferred relevance or
irrelevance cannot suppress inquiry. Recurrent probe identity pins contract/version,
binding, scope, and comparison policy, not wording alone. When isolation is required,
capture fresh observation before exposing prior returns.

A prediction used for mismatch analysis is sealed before the attempt and immutable.
Raw return, decoded result, reconstruction, episodic record, and semantic knowledge are
different records. Only an independently warranted `SemanticDelta` changes semantic
memory. G2A adds deterministic structural retrieval, candidate reconstruction,
non-compressive retention registration, and measured reacquisition. Consolidation,
reconsolidation, semantic-field evaluation, and learned-probe candidates are G2B.

Keep present use, reconstruction, direct consequence evaluation, and reacquisition
distinct. Failure of recall does not prove absence of retained learning. A reacquisition
advantage requires a checked comparison with a pinned baseline and binding-defined cost
frontier; eventual relearning alone is insufficient. Do not force a universal scalar
cost. Reopening may reactivate, reconstruct, initiate relearning, or retrieve provenance.

For G2A, retrieval is deterministic structural matching over owned typed references.
Rank by exact policy components and stable IDs; enforce scope/binding isolation,
deduplication, bounds, and stale-reference rejection. Do not add embeddings, floating
relevance scores, model suppression, or a retrieval dependency. Retrieval and ambiguous
reconstruction remain candidates, never history, knowledge, support, or warrant.

G2A recovery routes are provisional and unlicensed. Keep `DirectUseRoute`,
`ReconstructionRoute`, `ConsequenceEvaluationRoute`, and `ReacquisitionRoute` separate;
none establishes a protected retention capability. `RecoveryLicense` and licensed
`ObjectRegenerationRoute` enforcement begin in G3. Cost comparisons require identical
competence/universe/binding/horizon/evaluator/evidence/budget/protocol/policy pins,
matching named axes, and exact nonnegative values. Strict Pareto advantage means all
costs no worse and at least one better; incomparable vectors establish no advantage.
Even an independently checked comparison is provisional/soft and cannot promote or
license itself.

## Recursive project inquiry

G3R treats repository development as a typed RCI binding. Keep theory, question/probe
repertoire, method repertoire, representation, Goal decomposition, and implementation
successors distinct; a failure in one category does not authorize mutation in another.

- Begin each cycle from an exact clean `ProjectAnchor`. Repository history remains Git;
  the RCI ledger records project-inquiry evidence and never becomes a second source
  history.
- Record a limitation only when two states across the claimed boundary have different
  protected consequences. General dissatisfaction and novelty are not limitations.
- Generated question contracts are inert until admitted by the versioned
  `recursive-project-v1` policy. They require typed referents, at least two distinct
  consequential returns, comparison semantics, consumers, and falsifying attacks.
- G3Q compiles an admitted candidate only into a derived, deterministic, data-only
  registry projection pinned to its clean anchor, exact decision, compiler/policy,
  binding, scope, horizon, and comparison semantics. It opens an ordinary obligation;
  an unmatched return opens a typed residual and never grants warrant.
- The selected G3G boundary may compile an exact admitted project return into an inert
  Goal candidate only from owned anchor/limitation/frontier/candidate records and
  versioned acceptance/mutation registries. Returned prose never becomes argv, a path,
  policy, evidence, warrant, or authority. Generation, admission, Goal sealing,
  actualization, review, and promotion remain separate.
- A generated Goal candidate cannot weaken or replace a predecessor gate. Its acceptance
  profile must retain the complete incumbent gate and add one focused discriminator. Its
  mutation profile cannot overlap live authorities, `.github`, Git metadata, credentials,
  runtime policy, release, or deployment surfaces. Underdetermined input returns
  `Unknown`; manual Goal authoring remains an explicit external bypass.
- Method candidates name the native relation, primary sources, assumptions,
  applicability checks, license, and missing adapter. Admission never installs code or
  grants authority.
- Compare successors by exact preservation, typed gain, and comparable exact costs.
  Keep an explicit frontier when candidates are incomparable. Select the smallest
  reversible candidate with a lawful discriminator or return `Unknown`.
- Seal `ImplementationGoalContract` before implementation. It pins current/desired
  behavior, separator, expected returns, protected predecessors, gate digests, mutation
  bounds, rollback, and reopening; returns cannot rewrite it to make a candidate pass.
- Candidate development happens externally in an isolated branch/worktree at the exact
  anchor. RCI records evidence but has no source-writing, arbitrary-command, Git,
  credential, policy, merge, release, deployment, or authority-expansion port.
- Replacement requires passing exact-head evidence, fresh review by a context distinct
  from the developer, predecessor preservation, typed gain, and protected CI. A merge
  is an externally observed promotion, never a reducer side effect.
- Evolve CI by dual gate: add and pass the successor beside the incumbent before any
  later reviewed cleanup removes the incumbent.
- Append cycle checkpoints and immutable cycle reports. Stop on no consequential
  residue, no discriminator, repeated blocker, stale/invalid/indeterminate evidence, or
  required authority expansion; return `Unknown` instead of relaxing the Goal.

## Phase discipline

G1, G2A, G2B, G3A-H, G3R, G3Q, and G3G are sealed verified baselines. The post-G3Q recursive
frontier selection is protected at exact selection anchor
`60ff25635f94fb004e6419a09293c5e0fc023074`; G3G was promoted through protected main at
`5f48d397030b6a063fdca19e51b70a824096e564`. G3V was attempted from
`b6069c0a58a669eed21005bada407eff1828071a` and stopped indeterminate at candidate
`a425f4b0dfa5b2c52a67df87d460f25e4e825518`: its closed profile passed, but fresh
distinct-context semantic review was unavailable. It is unmerged and unpromoted;
RCI-079 remains deferred and unverified. No successor Goal is active until a new
frontier decision and explicit activation occur.
G3R added the recursive project-inquiry and candidate-development protocol described in
ADR-0012 and ADR-0013 without altering predecessor event schemas. G3A-H added explicit carrier
roles, binding-derived realized history, exact history-state factorization and
continuation checks, exact compression/recovery licensing, path residue, representation
succession, and generic reopening described in `PLAN.md` and ADR-0011. G3Q adds only
confined, independently admitted, data-only generated question scheduling. G3G adds
deterministic inert Goal-candidate compilation plus separate admission under ADR-0014.
G3A-L and the other nondominated successors remain deferred rather than rejected.

- `core-v1` schedules obligation characterization, same-class variation, minimal
  boundary crossing, factor proposal, necessity/sufficiency counterexamples, conflict
  localization, and residual characterization.
- Phase 2 may schedule warrant/localization/generalization and prerequisite/
  actualization attacks after their implementations exist.
- Phase 2 formal syntax is a serialized Boolean/finite-enum AST: literals, symbol refs,
  equality, negation, conjunction, disjunction, implication, equivalence. No arbitrary
  code or quantifiers. Keep an independent interpreter/exhaustive enumerator beside the
  optional Z3 translator.
- G2B admitted a learned probe only after deterministic holdout, redundancy,
  protected-behavior, attack, and controller-policy checks. Learned automata remain
  unnecessary. Exact/approximate compression, licensed recovery routes, and the linear
  consequence quotient are G3. G3A-H precedes the SymPy linear binding in G3A-L.
  CHC/PDR is G4, control G5,
  multi-backend warrant G6, and the complete opaque-controlled-memory benchmark plus
  hardening/release is G7.
- Future findings enter the requirements matrix/backlog without expanding the Goal.

G2A adds new version-1 event kinds without changing any G1 event schema. Parent
reacquisition request, child inquiry creation, and parent linkage form a resumable saga;
every partial prefix stays open. Bump folded-state/snapshot/projection schemas only when
needed, rebuild incompatible derived state from the ledger, and preserve archived G1
stream semantics.

G2B adds new version-1 event kinds without changing G1 or G2A event classes. A
consolidation checkpoint is not knowledge; a memory patch is not its own repair; a field
evaluation is not authority; and a generated probe is not procedural knowledge until the
versioned admission policy and independent checks pass. Preserve sealed G1/G2A replay.

Compression semantics are documented now but not executable in G1. Preserve exact
quotient vs approximate license, reconstruction loss vs consequence loss, object
regeneration vs direct consequence evaluation vs reacquisition, and
`QUOTIENT -> REPARAMETERIZE -> APPROXIMATE -> RESIDUE -> REOPEN`. Numerical near-zero
rank never constitutes exact evidence.

The future opaque-controlled-memory environment is a capability-gated benchmark, not a
G1 primitive. Raw byte difference is not semantic difference; correlation is not
dependency; a separator is not a unique cause; predictive state is not control; and the
linear consequence theorem applies only after a binding has established its assumptions.

## Development and verification

Inspect before editing, preserve unrelated work, make the smallest coherent change, and
run focused tests before the complete gate. Keep optional network/solver/container work
outside deterministic blocking tests. Never activate a later contract because its
catalog entry exists.

The sealed G1 gate remains identical to `PLAN.md` and both Goal artifacts:

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

The sealed G2A gate adds this focused command, identically present in `PLAN.md`,
`docs/goals/G2A.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
```

The sealed G2B gate adds this focused command, identically present in `PLAN.md`,
`docs/goals/G2B.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py
```

The sealed G3A-H gate adds this focused command, identically present in `PLAN.md`,
`docs/goals/G3A.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_g3a_history_state.py
```

The sealed G3R gate adds this focused command, identically present in `PLAN.md`,
`docs/goals/G3R.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py
```

The sealed G3Q baseline retains this focused command identically to `PLAN.md`,
`docs/goals/G3Q.md`, CI, and `docs/verification.md`:

```text
uv run pytest -q tests/acceptance/test_regenerative_questions.py
```

The sealed G3G baseline retains this focused command identically to `PLAN.md`, its Goal, CI,
and verification evidence:

```text
uv run pytest -q tests/acceptance/test_goal_synthesis.py
```

Dependency sync is bootstrap and may fetch locked packages. Test execution is
credential-free, network-denied, deterministic, and effect-free under replay. Record
exact commands/results in `docs/verification.md`. If a check cannot run, record the
limitation and leave the affected conclusion unverified.

At minimum cover reducer illegal transitions, arbitrary payload containment, mandatory
attacks, localized conflicts, support/ancestry cycles, guard deactivation, replay/export,
CAS tamper/crash points, OCC races, attempt cardinality/idempotency/timeouts, payload
null/empty distinctions, schema failure, AST exhaustive/Z3 differential behavior,
probe comparability/fresh isolation, prediction-before-return, memory separation, both
reference domains, CLI/SDK parity, and backlog authority limits. G2A additionally covers
retrieval determinism/isolation/bounds, route no-collapse, ambiguous reconstruction,
parent/child saga crash-resume, exact frontier comparison and pin mismatch,
non-promotion, the paired circuit recovery fixture, and G1 replay compatibility.

## Governed dogfooding

- `.rci/config.toml` is tracked human-owned policy. Runtime database, CAS, projections,
  and exports are ignored local state.
- `rci backlog reconcile` is dry-run by default.
- G1 manual `--apply` may append allowlisted create, exact-dedupe, rank, and block only.
  Close remains proposal-only until a later explicit human policy/Goal decision; tests
  and runtime output cannot grant authority.
- A regression creates a linked recurrence rather than rewriting closed history.
- Evidence runners use explicit argv, bounded time/output, temporary captured
  workspaces, and no network.
- No source-writing, Git mutation, merge/push, policy editing, packaging, deployment,
  release, or authority-expansion capability exists.
- RCI may propose development obligations and ADR changes but cannot self-promote,
  self-modify, or merge. Fresh independent review and protected CI remain the
  non-self evidence boundary; the development agent may act only inside a sealed Goal
  and bounded candidate environment whose promotion conditions were fixed in advance.
