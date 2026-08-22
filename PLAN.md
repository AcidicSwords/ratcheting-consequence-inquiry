# RCI v0.5 implementation plan

## Status and authority

This document is the approved engineering architecture and delivery sequence for
`RCI_Project_Spec.tex` v0.5. The specification defines RCI semantics; this plan fixes
implementation choices, trust boundaries, dependencies, and milestone gates. The active
Goal fixes the current completion boundary. Ambiguities are recorded in
`docs/requirements-matrix.md` and, when a decision is required, `docs/adr/`; code does
not silently amend either authority.

Historical drafts in `docs/spec/sources/` are provenance, not live instructions.

## Locked product decisions

- Python 3.12 research SDK and headless Typer CLI, packaged with `uv`/PEP 621.
- Pydantic v2 strict frozen records, stdlib SQLite in WAL mode, and content-addressed
  filesystem artifacts.
- pytest, Hypothesis, Ruff, mypy, Apache-2.0, and Windows/Linux GitHub Actions.
- Local single-user operation first. UI, HTTP service, PostgreSQL, distribution,
  deployment, and releases are later Goals.
- Manual and scripted generators are blocking-test authorities. OpenAI and Z3 are
  optional extras; neither is required for deterministic replay or reference examples.
- Docker supplies a pinned Linux parity environment and later isolated native adapters;
  a local Docker daemon is not a base requirement.
- Model output and reification are proposals, never warrant. A checked witness warrants
  only its exact scoped existential; exhaustive UNSAT is hard only over a declared
  closed finite universe; Z3-only UNSAT is `solver_trusted` and soft.
- Unknown is a valid terminal result. Timeout, transport failure, unsupported
  capability, logical unknown, checker indeterminacy, and exhausted search stay distinct.

## Architecture

### Pure event spine

```text
decide(state, command) -> events
evolve(state, event) -> state
EventStore.append(stream, expected_sequence, events)
plan_next(state) -> StepPlan
```

Reducers perform no I/O and generate no clocks, IDs, randomness, or provider metadata.
Every external operation starts from a committed effect request. Replay folds stored
events only and never performs effects.

The SQLite ledger plus content-addressed artifacts is durable authority. Append uses
`BEGIN IMMEDIATE`, an expected stream sequence, unique event/entity IDs, and a single
writer path per inquiry. A CAS artifact is published and verified before an event may
reference it; an orphan artifact is recoverable, a dangling reference is forbidden.
Snapshots and projections pin stream sequence and schema/policy versions and are fully
deletable/rebuildable. Projection rows and checkpoints commit together.

All event types carry an explicit version. The greenfield database begins at schema v1.
Reserve an upcaster registry and fail closed on unknown versions; do not invent legacy
migrations before real legacy data exists.

### Aggregate, realized history, configuration, and retained state

```text
event prefix --Phi_agg--> InquiryState (replay-complete authority)
                              |
                              | binding-specific rho_B
                              v
                        realized history --p_B--> configuration
                              |
                              | independently validated q_H
                              v
                        retained consequence state
```

Ledger sequence never implies realized succession. Bindings declare carrier roles,
history derivation, configuration projection, protected consequence equality, and
admitted continuation. `InquiryState`, `ProbeTrace`, `RetentionPackage`, and
`MemoryPatchCandidate` are not certified retained state. A history representation is
called recursively executable only after every operation in its declared continuation
family descends lawfully. The aggregate remains complete and is never compressed.

### Logical ownership

- `M_E` owns episodic records and artifact references, not copies of ledger events.
- `M_S` owns immutable `LemmaVersion` semantic records.
- `M_P` owns admitted procedures, probes, contracts, and method manifests.
- `M_L` owns G2A retention packages, provisional recovery-route descriptions,
  reacquisition scaffolds/protocols, and recovery observations. G3 adds licensed
  capability views, residue, and compression-application references.
- `W` owns support environments/routes, dependency boundaries, checks, nogoods, and
  warrant decisions.
- `A` owns effect requests, attempts, route snapshots, raw returns, decode outcomes, and
  candidate reconstructions.
- `Pi` owns sealed predictions and warranted mismatch records.

Active theory, probe views, semantic fields, reopening views, ancestry indexes, and
compression-debt summaries are deterministic projections.

### Effect, return, and checking lifecycle

```text
StepPlanRecorded
  -> EffectRequested
  -> NoAttemptDisposition or zero/more (EffectAttemptPlanned -> EffectAttemptStarted)
  -> one EffectAttemptOutcome per started attempt
  -> optional immutable ExternalReturn owned by Returned
  -> DecodeOutcome
  -> optional EvidenceRecorded
  -> CheckerVerdictRecorded
  -> WarrantDecisionRecorded
  -> at most one EffectResultAccepted per request
  -> optional LemmaPromoted
```

`NoAttempt` is a plan disposition. Attempt outcomes are `NotPresented`,
`PresentationUnknown`, `CaptureFailed`, `Cancelled`, or `Returned`. A timeout may leave
presentation unknown and never proves non-presentation. Each attempt has one terminal
outcome; retries may create several attempts, while the logical request accepts at most
one result.

Returned bytes are immutable CAS artifacts. JSON null, empty bytes, empty string, zero,
and false remain distinct. Decode is a strict union of `Decoded`, `Malformed`,
`Unsupported`, and `Failed`; checking is `Valid`, `Invalid`, `Indeterminate`, `Timeout`,
`Unsupported`, or `Failed`. Decoding, checking, warrant classification, and promotion
are separate events. Late/duplicate returns may be retained as rejected evidence but
cannot replace an accepted resolution.

Effect routes split an allowlisted, versioned `RouteDefinition` from the resolved
per-attempt `RouteSnapshot`. The snapshot records addressed source, redacted endpoint,
adapter/backend versions, execution-environment fingerprint, request digest, and ordered
transform manifest. Credentials are never stored. Source-reported identity belongs to
the return, not the route.

### Claims, support, and warrant

`Claim` remains provisional. Promotion creates a linked `LemmaVersion`, support route,
and L3 `ActiveLemmaView`; it never mutates the claim into a fact.

```text
SupportEnvironment {
  assumptions, scope, binding_revision, universe,
  independent_realizability_check_ref
}

SupportRoute {
  conclusion, environment_ref, required_dependencies,
  open_dependencies, justification_refs, certificate_check_ref,
  warrant_refs, provenance_refs
}
```

The dependency boundary is route-specific. Hard support requires independently checked
environment realizability; lack of a known contradiction is insufficient. Minimal
supports form subset antichains only within the same conclusion, scope, binding,
applicability, and policy versions. Dominated routes remain in history. A warranted
nogood invalidates every environment containing it.

Ordinary positive support is grounded and acyclic. An ungrounded self-supporting cycle
remains open. A mathematical cyclic proof must be validated by an explicitly named
independent checker and is represented as a checked certificate leaf, never as a support
graph cycle. Semantic-version ancestry is separately acyclic.

Hard promotion is exact, scoped, guarded, dependency-closed, independently checked,
policy-authorized, and cycle-free. Guard, support-route, and nogood standing changes
are append-only events; scope, binding, universe, and policy are exact inputs to the
pure theory selector. Mismatched pins deactivate the view and prior pins reopen it
without rewriting prior facts or creating a writable active-theory store.

Opaque L0 prose can conflict only through explicit proposition identity, polarity,
role, bound referents, and scope. Semantic contradiction, entailment, equivalence,
necessity, sufficiency, generalization, or control requires validated reification or
checked domain evidence. Every proposed necessity, sufficiency, or prerequisite opens
its corresponding counterexample/alternate-route attack in the identical scope.

### Questions, orchestration, and semantic field

Question contracts are code-registered typed behavior with immutable versioned data
templates. They declare referents, preconditions, total L0 binding, lawful updates, and
follow-ups. Templates and generated payloads are inert data and cannot execute code,
tools, SQL, commands, or policy.

The complete catalog is retained as data, but only explicit profiles are schedulable.
`core-v1` contains obligation characterization, same-class variation, minimal boundary
crossing, factor proposal, necessity/sufficiency counterexamples, conflict localization,
and residual characterization. Later profiles remain inactive until their semantics and
tests exist. Generated contracts/probes are candidates until admitted by a versioned
human/controller policy.

The deterministic scheduler deduplicates obligations by kind, normalized bound args,
scope fingerprint, and binding revision. The attempt key additionally includes contract
ID/version. It orders ready work by invariant/warrant-conflict safety, explicit priority,
dependency depth, creation sequence, then stable ID. Defaults: 100 reducer steps, three
attempts per attempt key, and 60 seconds per external effect.

The semantic field is a derived, probe-conditioned generator view with active,
undetermined, and warranted-irrelevant regions. A model's relevance judgment never
suppresses inquiry. Fresh observation may withhold prior answers until the external
return is captured; comparison happens afterward.

### Cognitive spine and G2 recovery slices

The verified G1 slice implements stable versioned recurrent-probe identity,
ordered comparable `ProbeTrace`, optional immutable prediction sealed before an attempt,
raw return capture, candidate decode/reconstruction, independently warranted
`SemanticDelta`, and separate episodic and semantic projections. Prediction never
rewrites the return; return never rewrites prediction; reconstruction is neither history
nor knowledge.

Verified G2A adds deterministic structural retrieval, explicit reconstruction candidates,
non-compressive retention registration, and measured reacquisition. Active G2B owns
consolidation, reconsolidation, semantic-field evaluation, and learned-probe admission;
self-cleaning and mature retention economics remain later work.

Retention is relational rather than a nominal memory-object type. Keep four recovery
relations distinct: present use, reconstruction without substantial new evidence,
direct consequence evaluation, and reacquisition using new evidence/practice. Failure
of recall is not evidence that prior learning left no retained scaffold. A reacquisition
claim must compare a pinned retained-state recovery frontier with an appropriate pinned
baseline; eventual success alone does not establish an advantage. Cost is a binding-
defined vector and remains Pareto-ordered unless the binding warrants a scalarization.

Learning may survive as cues, probes, representations, methods, boundaries, failures,
prerequisites, search order, or provenance that deform later inquiry. Reopening may
reactivate, reconstruct, launch reacquisition, or retrieve provenance. Forgetting is a
reduction in protected future recovery capacity, not synonymous with deleting content.

G2A retrieval is a pure structural match over owned typed references. A versioned policy
pins scope and binding compatibility, exact rank components, stable-ID tie breaking,
deduplication, bounds, and stale-reference rejection. It uses no embedding, floating
relevance score, model suppression, network, or new dependency. Ambiguous reconstruction
remains an ordered candidate set.

A reacquisition request creates a resumable parent/child inquiry saga through new
version-1 events. The parent request, child creation, and parent linkage remain separate;
every partial prefix is open. Runtime work reuses the existing persisted effect protocol.
G1 event schemas do not change. Folded-state, snapshot, and projection schemas may
advance, while unsupported derived snapshots rebuild from the ledger and archived G1
streams retain their G1 meaning.

Recovery observations pin target competence, finite universe, binding, horizon,
evaluator, evidence access, budget, protocol, and comparison policy. `CostVector` uses
matching named axes and exact nonnegative values. Strict Pareto advantage requires every
retained cost to be no worse and at least one to be better; incomparable vectors establish
no advantage. `RecoveryFrontier` is derived. An independently checked
`RecoveryComparison` is provisional/soft and creates no hard lemma or license.

### Consequence quotient and compression

Core semantics permanently distinguish exact consequence quotient from licensed
approximation, source reconstruction error from consequence loss, and object regeneration
from direct consequence evaluation.

```text
QUOTIENT -> REPARAMETERIZE -> APPROXIMATE -> RESIDUE -> REOPEN
```

G2A implements `RetentionPackage`, `DirectUseRoute`, `ReconstructionRoute`,
`ConsequenceEvaluationRoute`, `ReacquisitionRoute`, `ReacquisitionScaffold`,
`RecoveryProtocol`, recovery observations, and a derived `RecoveryFrontier`. Its route
records are provisional, unlicensed descriptions and cannot be selected as protected
capabilities. `ReconstructionRoute` is not the G3 licensed `ObjectRegenerationRoute`.
This staged interpretation is fixed by ADR-0009 and prevents ADR-0006's earlier wording
from pulling `RecoveryLicense` into G2A.

G3 implements `CompressionContract`, `CompressionValidation`,
`ExactCompressionLicense`, `ApproximateCompressionLicense`, `CompressionApplication`,
licensed `ObjectRegenerationRoute` and other capability views, `RecoveryLicense`, and
`ConsequenceEstimate`. Combined capability is derived from licensed routes, not stored as
an optional-field mode bag. A license pins the protected horizon,
scope/binding/distribution versions, equivalence or separating loss, bound semantics,
confidence, resource/recovery budgets, baseline, validation, support, residual/fallback,
and reopening policy. A license references warrant; it is not its own warrant.
Compression may preserve a licensed path to reacquisition rather than immediate recall,
but only when future consequence fidelity and recovery cost remain inside the explicit
license.

The Phase 3A linear binding uses the corrected theorems:

- for a query family `Q`, exact equivalence is difference in `span(Q)^perp`;
- for finite second moment `M_Q = E[q q^T]`, almost-sure equivalence is difference in
  `ker(M_Q)`;
- the exact quotient is `R^d / ker(M_Q) ~= im(M_Q)`, represented by projection or `M_Q x`;
- `rank(M_Q)` is the minimum *linear encoder* dimension, not unrestricted bit complexity;
- finite probe weights must be positive; vector-output operators require finite expected
  squared Frobenius norm;
- old-invisible structure reopens when `ker(M_t)` is not a subset of `ker(M_{t+1})`;
- numerical near-zero singular values are approximate evidence, never exact nullity;
- eigenspace sensitivity does not solve optimal bit allocation;
- reopening without retained residue or reacquisition returns Unknown.

Use the second moment rather than centered covariance unless the mean is known zero.
Task-based/indirect rate-distortion supplies approximate-compression terminology. EDEN,
DRIVE, TurboQuant, and QJL are catalogued native candidates, not RCI primitives.

## Repository shape

```text
src/rci/
  core/ persistence/ questions/ claims/ orchestration/
  formal/ warrant/ probes/ generators/ backends/ bindings/
  memory/ recovery/ evaluation/ backlog/ cli/
tests/
  unit/ property/ model/ integration/ replay/ acceptance/ evaluation/ security/
examples/
docs/
  spec/sources/ adr/ goals/ architecture.md requirements-matrix.md verification.md
```

Create packages only when implemented. No later-phase passing stubs.

## Delivery gates

### G0 — governance normalization

Archive/hash all source drafts; publish v0.3.1, source manifest, architecture, ADRs,
requirements matrix, verification record, PLAN, AGENTS, and the G1 Goal artifact.
Initialize Git, Apache-2.0 licensing, ignore policy, and tracked human-owned
`.rci/config.toml`.

### G1 — Foundation, specification Phases 1–2, and cognitive spine

Deliver packaging/CI/CLI; pure state/events; SQLite/CAS/snapshots/projections; question,
claim, conflict, obligation, and scheduler kernel; manual/scripted generators; safe L0;
restricted Boolean/finite-enum AST; exhaustive checker and optional Z3; support routes,
warrant, guards, and active theory; recurrent probes/predictions/attempts/raw returns/
reconstruction/SemanticDelta; deterministic circuit and route fixtures; and shadow-only
backlog dogfooding.

The circuit enumerates eight states for
`lamp_on = switch_closed AND (main_power OR backup_power)`: backup power refutes
main-power necessity, an open switch refutes available-power sufficiency, and exhaustive
closed-world checking establishes switch-closed necessity.

The route binding uses `start -> gate -> target` and
`start -> bypass -> {target, dead_end}`. The bypass refutes gate prerequisite; its
nondeterminism yields may-reachability and never must-control.

### G2A — deterministic retrieval, reconstruction, and recovery (verified)

Deliver strict `RetrievalQuery`/`RetrievalHit`/`RetrievalResult` records, a versioned
structural policy, ambiguous candidate reconstruction, and non-compressive
`RetentionPackage` registration with separate provisional direct-use, reconstruction,
direct-consequence, and reacquisition routes. Add a `ReacquisitionScaffold`, a resumable
parent/child inquiry saga, exact typed multidimensional cost observations, a derived
Pareto frontier, and independently checked but soft recovery comparisons.

The SDK exposes retrieval, retention registration, reacquisition start/link, observation,
and comparison. The CLI adds canonical-JSON `memory retrieve`, `recovery start`,
`recovery inspect`, and `recovery compare`. The paired circuit reference stores cues,
probe order, boundaries, and failures without storing the target answer and compares it
with a no-scaffold baseline under identical competence, universe, binding, horizon,
evaluator, evidence access, budget, protocol, and comparison policy.

G2A adds only new event kinds; G1 event schemas are immutable. Snapshot/projection
versions advance when required and old derived state rebuilds. Archived G1 streams must
replay with unchanged G1 semantics. Recovery routes remain provisional and unlicensed;
no comparison can create warrant or a `RecoveryLicense`.

### G2B — consolidation and learned-probe candidates (verified)

Use `consolidation-interleave-v1` to create explicit checkpoints selecting up to four
recent episodes, four older exceptions, and four accepted counterexamples from a pinned
source prefix. Consolidation creates ordinary claims, attacks, candidate support
boundaries, and obligations rather than semantic facts. One episode cannot self-
consolidate and available defeating material cannot be silently omitted.

Reconsolidation appends `MemoryPatchCandidate`, successor lemma, typed correction, and
`ReconsolidationLink` records while preserving predecessor history and transporting open
dependencies. `conservative-question-field-v1` derives and independently evaluates a
stable maximum 32-item field; overflow remains undetermined. `finite-stratified-holdout-
v1` and `g2b-probe-admission-v1` require positive nonredundant holdout discrimination,
protected-behavior checks, completed attacks, and controller admission before a generated
probe enters procedural memory. AALpy, learned automata, embeddings, compression,
licensing, and control remain absent.

G2A and G2B are sealed internal delivery gates under RCI-058. Their version-1 event
schemas and meanings remain immutable under v0.4.

### G3R (active) — recursive project inquiry and candidate development

- Reuse the ordinary ledger/CAS to own clean project anchors, consequential capability
  limitations, inert question/method/successor candidates, deterministic partial-order
  frontiers, sealed implementation Goals, candidate environments, exact evidence,
  independent reviews, successor/promotion decisions, checkpoints, and typed stops.
- Keep theory, question/probe, representation, method, Goal, and implementation
  succession separate. A generated question needs two consequentially distinct return
  classes and is confined to `recursive-project-v1` after admission. A method binding
  preserves primary sources, assumptions, applicability, license, and adapter status.
- Select nondominated candidates by exact preservation/gain/cost relations. Unknown or
  differently typed costs remain incomparable. Select the smallest reversible lawful
  discriminator first; otherwise return `Unknown`.
- Seal `Current`, `Desired`, `Separator`, `Preserve`, `Acceptance`, `Scope`, and
  `Assumptions` plus expected returns, mutation roots, frozen gates, rollback, and
  reopening before changing implementation.
- Develop in an isolated `codex/` branch/worktree from the exact clean anchor. Require
  fresh-context exact-head review and CI. Runtime records promotion facts but gains no
  source-writing, arbitrary-command, Git, credential, merge, deployment, or release port.
- Evolve required checks only by dual-gate overlap. Recur one bounded Goal at a time;
  stop on no residue/discriminator, three repeated blockers, invalid/indeterminate
  evidence, or required authority expansion.
- Dogfood G3R over G3A-L, regenerative question synthesis, native-method binding,
  autonomous Goal synthesis, candidate-development actuation, and G4. Seal exactly one
  next Goal without implementing it before G3R closes.

G3R adds only new version-1 event kinds. Folded state advances to v5 and v1-v4 snapshots
rebuild from unchanged authoritative events. It adds no dependency.

### G3A-H (verified)/G3A-L/G3B/G3C — retained state and compression

- G3A-H (verified): explicit carrier roles; binding-derived realized history; exact consequence
  factorization; continuation compatibility; recursive update; determination descent;
  path residue; exact compression and recovery licenses; representation succession;
  generic reopening; unary-parity and order-sensitive history fixtures. It uses current
  dependencies only.
- G3A-L: SymPy exact rational linear binding; universal/distributional/vector forms;
  positive-weight probes; linear-only minimum dimension; exact kernel reopening.
- G3B: approximate loss licenses, budgets/risk/confidence/debt composition, NumPy
  numerical candidates, and a deterministic toy quantizer/reference oracle.
- G3C: isolated native adapters. QJL is the first candidate; EDEN/DRIVE remain blocked
  pending a software license and TurboQuant pending official licensed code.

### G4/G5/G6/G7

- G4 recursive formal engine: CHC, Spacer/PDR, predecessors, inductive cuts.
- G5 control: finite actions, may/must predecessor, synthesis, feedback refinement,
  concrete strategy checking.
- G6 multi-backend warrant: proof/evidence adapters, certificate checks, discrepancies.
- G7 hardening/research release: migrations, fuzz/performance/security, replay
  compatibility, evaluation reports, the staged opaque-controlled-memory end-to-end
  benchmark, stable SDK, and release automation.

The opaque-controlled-memory benchmark is a future system witness, not a new core
primitive. It begins with known interventions, immutable opaque byte returns, and ordered
history; withholds semantic memory maps; and requires discovered temporal/derived probes,
conditional support routes, prediction seals, behavioral-state quotients, compression,
reopening, transfer, and measured reacquisition advantage. Its primary quotient is
behavioral equivalence over admitted future action-observation tests. Predictive State
Representation/system-identification machinery is a future native binding; the linear
consequence theorem becomes applicable only after the learned representation and query
family meet its assumptions. The benchmark is capability-gated across G2-G7 and never
blocks G1.

## Dependencies and Docker

G1 base dependencies are Pydantic v2 and Typer; development uses pytest, Hypothesis,
Ruff, mypy, and build. `openai` and pinned `z3-solver` are optional extras. G3A-H adds no
dependency; G3A-L adds SymPy when exact linear capability is implemented; G3B adds
NumPy. Future libraries are added only with the exercised capability.

RCI owns its event protocol, reducers, support semantics, and canonical ASTs. Established
libraries own their native mathematics behind typed ports when their license, failure
semantics, and guarantees match the contract.

G1 includes a pinned Linux development/CI image, but native Windows/Linux gates remain
canonical. Native-method containers begin in G3C and run nonroot, network-disabled,
read-only, capability-dropped, resource-bounded, without Docker socket, credentials,
ledger/CAS access, or a live source mount.

## Governed dogfooding

`.rci/config.toml` is tracked human policy; `.rci/state.sqlite3`, artifacts, projections,
and exports are ignored local state. `rci backlog reconcile` is shadow/dry-run by
default. G1 manual `--apply` may append only allowlisted create, exact-dedupe, rank, and
block effects. Close is proposal-only until a later explicit human policy/Goal decision;
tests cannot grant that authority. A regression creates a linked recurrence rather than
rewriting closed history.

Evidence runners receive explicit argv, bounded time/output, a captured temporary
workspace, and no network. No source-writing, Git mutation, merge/push, policy editing,
packaging, deployment, release, or authority-expansion port exists.

## Verification

The verified G1 gate remains identical in AGENTS, this plan, and both Goal artifacts:

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

Verified G2A also requires this focused acceptance command, identically present in AGENTS,
the G2A Goal, CI, and the verification record:

```text
uv run pytest -q tests/acceptance/test_g2a_retrieval_recovery.py
```

Verified G2B also requires this focused acceptance command, identically present in AGENTS,
the G2B Goal, CI, and the verification record:

```text
uv run pytest -q tests/acceptance/test_g2b_consolidation_plasticity.py
```

Verified G3A-H additionally requires this focused acceptance command, identically present
in AGENTS, the G3A Goal, CI, and the verification record:

```text
uv run pytest -q tests/acceptance/test_g3a_history_state.py
```

Active G3R additionally requires this focused acceptance command, identically present
in AGENTS, the G3R Goal, CI, and the verification record:

```text
uv run pytest -q tests/acceptance/test_recursive_project_inquiry.py
```

Synchronization may fetch locked packages; test execution is credential-free,
network-denied, deterministic, and replay-safe. CI has independent base and all-extras
Windows/Linux lanes. Docker/GPU/live-model checks are nonblocking.

Blocking G1 evidence covers arbitrary inert payloads; reducer illegal transitions;
effect-free byte-identical replay/export; CAS tamper and crash points; SQLite OCC races;
attempt cardinality, timeout, duplicates, and first acceptance; payload null/empty/false
distinctions; decode/check/warrant separation; independently checked environment
realizability; support/ancestry cycles; guard deactivation; probe comparability and fresh
observation isolation; prediction-before-return; reconstruction/history/knowledge
separation; unwarranted relevance preservation; both reference findings; CLI/SDK parity;
and backlog non-mutation/authority limits.

Blocking G2A evidence covers retrieval permutation stability, scope/binding isolation,
deduplication, bounds, and stale references; model-relevance non-suppression; ambiguous
reconstruction; separation of all four recovery relations; generated-detail containment;
every parent/child crash-resume boundary; exact Pareto and mismatched-pin negative cases;
comparison non-promotion; the paired circuit cost improvement; archived G1 replay; both
existing reference conclusions; and unchanged backlog authority.

G3A-H adds carrier-role rejection, ledger/realized succession separation, exact
factorization, sufficiency versus coarsest claims, continuation and recursive-update
checks, determination descent, path-residue separation, license/application staging,
route-capability linking, representation frontier/ratchet behavior, generic reopening,
the two exact history fixtures, and unchanged G1/G2 replay. Later Phase 3 gates add the
linear theorem, numeric non-promotion, approximate budgets/debt, and isolated-container
adversarial tests.
