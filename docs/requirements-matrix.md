# RCI v0.5 requirements matrix

This matrix covers every numbered requirement in `RCI_Project_Spec.tex`. G1 was
verified on 2026-08-22 by the complete frozen native gate recorded with exact
returns in `docs/verification.md`. Its sole Windows skip is preserved there: the
host lacked file-symlink privilege (`WinError 1314`), so the adversarial symlink
case remains live for Linux CI and privileged Windows while the implementation's
other link/reparse-point and bounds checks passed. G2A is sealed and verified.
G2B, G3A-H, G3R, G3Q, and G3G are sealed and verified. The post-G3Q frontier selected
confined Goal synthesis as G3G; the selection is protected at exact anchor
`60ff25635f94fb004e6419a09293c5e0fc023074`, and the implementation was promoted through
protected main as `5f48d397030b6a063fdca19e51b70a824096e564`. G3V candidate
`a425f4b0dfa5b2c52a67df87d460f25e4e825518` passed its bounded executable profile but
stopped indeterminate because fresh semantic review was unavailable; it is unmerged and
RCI-079 remains unverified. G3FO candidate
`b3cb06363ac5b8cd60c9bfbda5c3fbdd7dca72fb` likewise stopped indeterminate after its
final fresh distinct-context review was unavailable; it is unmerged and supplies no
standing failure-observation capability. ADR-0016 preserves the compositional grammar as
a candidate only; G3Q-F is not selected. G3A-L is the active no-budget Goal selected at
protected anchor `71d32346c71a26cf82a36df7e50376759bc1873b`; it remains unverified
until its exact candidate, complete gates, and fresh review pass. Later phases remain
outside the completed implementation boundary.
Later-phase rows remain deliberately **deferred**, not failed and not implemented by an
interface-shaped stub.

Status vocabulary:

- **accepted G0** — governance/specification evidence exists;
- **verified G1** — the cited implementation/evidence exists and the frozen G1
  gate passed; a bounded qualifier names the deliberately limited G1 slice and
  does not claim a later milestone;
- **verified G2A** — the cited implementation and local plus hosted
  Windows/Linux/Docker verification exist;
- **verified G2B** — local, protected pull-request, and post-merge Windows/Linux/Docker
  verification pass;
- **accepted v0.4/v0.5** — normalized semantic/architecture evidence exists while executable
  evidence remains assigned to G3A-H or later;
- **verified G3A-H** — bounded exact history-state code and local, protected
  pull-request, and protected-main post-merge evidence pass;
- **active G3A-L** — exact finite rational linear-binding work is inside the sealed Goal,
  but no implementation or verification conclusion is yet standing;
- **verified G3R** — recursive project inquiry, adversarial acceptance, exact-head
  distinct-context review, protected pull-request CI, merge, and post-merge main CI pass;
- **stopped indeterminate** — a candidate and its returns are preserved, but a required
  discriminator was unavailable and the candidate was not promoted;
- **deferred Gx** — outside the active Goal and assigned to that milestone;
- **research** — requires a later explicit Goal and warranted method choice.

## Constitution and semantic kernel

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-001 | Authority and complete traceability | accepted v0.5 | `docs/source-manifest.md`, ADR-0001, ADR-0011–0016, this matrix, and the RCI-001--RCI-079 coverage check in `docs/verification.md` |
| RCI-002 | Pinned binding, scope, guard, universe, policy, and explicit carrier roles | verified G3A-H | sealed `InquiryContext`/`Scope` remain unchanged; `BindingCarrierManifest` declares exact carrier roles without mutating `InquiryStarted` |
| RCI-003 | Questions create provisional claims, not facts | verified G1 | `QuestionContract` pins role, `AnswerShape`, `answer_schema_id`, binding policy, and lawful follow-ups; `bind_answer` fails closed on an unregistered shape/schema/policy and produces only a provisional L0 claim. `test_only_core_v1_is_schedulable_and_rendering_is_literal` and the Phase 1 vertical slice cover the typed path. |
| RCI-004 | Arbitrary payloads remain inert L0 data | verified G1 | `freeze_json`, `InertPayload`, CAS-backed bytes; `test_arbitrary_l0_payload_is_inert_and_artifacts_are_references`, `test_nested_payloads_are_snapshot_immutable`, and replay of binary L0 bytes |
| RCI-005 | Unknown and failure kinds remain distinct | verified G1 | closed effect/decode/check/result enums; `test_no_attempt_disposition_is_distinct_from_returned_null`, `test_no_attempt_and_cancelled_are_not_semantic_unknown`, `test_budget_exhaustion_is_unknown_not_impossibility`, OpenAI timeout/transport tests, and CAS null/empty distinctions |
| RCI-006 | Description/may-reachability do not imply control | verified G1 bounded seam; control deferred G5 | `RouteDemonstration`; `test_two_route_graph_proves_may_reach_but_refutes_prerequisite_control`; no G1 control-promotion contract exists |
| RCI-007 | Must/enough/prerequisite opens attack; conflicts do not explode | verified G1 | `_derive_claim_consequences` and `mandatory_attack_obligation` deduplicate by the exact explicit proposition/scope, and suppress an attack only for an exact active hard lemma; conflict consequences are localized in one atomic `ClaimAdmitted`. `test_claim_admission_atomically_opens_attacks_and_localized_conflict`, `test_modal_claim_creates_mandatory_attack`, and `test_modal_attack_closes_only_for_exact_active_hard_lemma`. |
| RCI-008 | Immutable correction/succession; ledger order is not realized succession | verified G3A-H | independently checked `RealizedHistoryDerivation` pins a verified committed prefix and binding-selected extension IDs; ledger order remains separate |
| RCI-009 | Later contracts stay inactive behind phase gates | verified G1 | ADR-0001; `QuestionCatalog.schedulable_contracts`; `test_only_core_v1_is_schedulable_and_rendering_is_literal`; later families are inert draft data only |
| RCI-010 | Active/unknown/irrelevant relevance states | verified G1 bounded view | `RelevanceStatus` keeps active, undetermined, and irrelevant distinct. `SemanticItem` requires both a warrant reference and reopening condition for irrelevance; `build_semantic_field` requires the warrant to be in the caller-resolved authorized set and the reopening condition to be pinned. The field is derived, is not stored in `InquiryState`, and has no scheduler-suppression path. `test_unknown_relevance_is_preserved_and_guarded_irrelevance_reopens`. |

## Event spine, persistence, and ownership

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-011 | Pure `decide/evolve` | verified G1 | `src/rci/core/transitions.py`; `test_models_are_strict_frozen_and_reducers_generate_nothing`; replay property tests |
| RCI-012 | Ledger/CAS are durable authority; one logical owner | verified G1 | ADR-0002; `InquiryState` owner collections; `SQLiteEventStore` and `ArtifactStore`; persistence, replay, and cognitive-owner regressions |
| RCI-013 | Replay-complete events and manifests | verified G1 | `InquiryStarted` pins the full `InquiryContext` and a CAS inquiry manifest containing the exact catalog artifact and digest; each manual question envelope pins an exact CAS contract artifact; `StepPlanRecorded`, route snapshots, warrant policy, provenance, and artifact refs remain in the event stream. The vertical slice validates the manifest/catalog artifact and exact contract replay; replay/export acceptance is byte-identical. |
| RCI-014 | Projections/snapshots are rebuildable derived state | verified G1 | `save_snapshot`, `rebuild_state`, `rebuild_projection`, and transactional projection checkpoint storage; `ProjectionCheckpoint` and its database key pin `projection_schema_version`. `test_snapshot_and_projection_are_rebuildable` verifies version-isolated checkpoints and ledger-only rebuild. |
| RCI-015 | SQLite WAL, atomic append, optimistic sequence | verified G1 | `SQLiteEventStore.append` uses `BEGIN IMMEDIATE`, expected sequence, lifecycle pre-fold, unique IDs, and rollback; `test_two_writers_race_from_the_same_expected_sequence`, failed-batch, append-only, and reopen tests |
| RCI-016 | Versioned schemas; unknown versions fail closed | verified G1 boundary; real migrations deferred G7 | schema-v1 event tags, SQLite `user_version`, and the immutable code-owned pure `EVENT_UPCASTERS` registry in `rci.core.upcasting`; the greenfield registry is intentionally empty. `test_unknown_event_schema_fails_closed` proves an unregistered future version cannot pass or mutate the registry, and `test_unknown_future_database_schema_fails_closed` covers the database boundary. |
| RCI-017 | Persist request before effect; replay is effect-free | verified G1 | OpenAI and evidence adapters require committed request plus started attempt; `test_openai_executes_only_after_start_and_captures_raw_before_decode`, persisted evidence pipeline, and cross-instance replay/export tests |
| RCI-018 | Attempt/result cardinality and idempotent acceptance | verified G1 | `EffectRequestState` plus transition guards; `test_effect_attempt_return_decode_and_accept_cardinalities`, retry property test, and `test_late_competing_return_is_durable_but_cannot_replace_first_acceptance` |
| RCI-019 | Typed `AttemptOutcome` | verified G1 | closed typed plan and attempt outcome/reason unions plus aggregate-owned `StepPlanRecorded` records. Requests must reference a persisted READY plan selecting their exact obligation/attempt key, and `NoAttemptDisposition` must reference that same owned plan; transition, OpenAI timeout/transport, replay-property, and cognitive-lifecycle tests exercise the distinctions. |
| RCI-020 | Versioned allowlisted `ReturnRoute` | verified G1 | `RouteDefinition`, `RouteRegistry`, immutable `RouteSnapshot`, redacted endpoint/environment/request digest/ordered transforms; unknown-route and request-digest integration tests |
| RCI-021 | Raw return precedes interpretation | verified G1 | `ArtifactRef` pins digest, size, media type, and encoding; `ExternalReturn` separately pins capture boundary, capture encoding, UTC capture time, attempt, route, and optional reported source identity before any decode. Exact byte and null/empty/string/zero/false tests, orphan recovery, dangling-ref rejection, tamper detection, and the vertical slice cover the lifecycle. |
| RCI-022 | Decode, check, warrant, promotion are separate | verified G1 | distinct event-owned `ExternalReturn`, `DecodeOutcome`/canonical result, inert `Evidence`, `CheckerVerdictRecord`, `WarrantDecisionRecord`, and `PromotionLink` stages. `test_evidence_check_warrant_and_promotion_are_separate_owned_stages` rejects self-authorizing/mismatched material; malformed decode/reification and exhaustive/Z3 tests cover fail-closed outcomes and soft solver-only evidence. |
| RCI-023 | Prediction seal precedes return and is a prospective consequence commitment | verified G1; accepted v0.4 interpretation | existing seal/mismatch schema already admits structured commitments and remains unchanged; temporal and actual-return tests remain authoritative |
| RCI-024 | One owner; aggregate state and retained state do not collapse | verified G3A-H | `InquiryState` remains replay-complete authority; `retained_state_views` is a deterministic join over licensed applications and cannot be written independently |

## Claims, formalization, support, and warrant

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-025 | Lifecycle, level, execution, logic, checker, warrant, promotion stay orthogonal | verified G1 | `ClaimStatus`, `ClaimAssessment`, `RepresentationLevel`, attempt/decode/canonical-result types, `CheckerVerdict`, `WarrantClass`, applicability, and promotion are separate strict concepts. `test_claim_semantic_axes_are_independent_and_l3_is_never_in_place` and the separate-owned-stages aggregate test reject axis collapse and in-place L3 mutation. |
| RCI-026 | L0 conflict only from explicit structure | verified G1 | `Claim.structural_key` and `structural_conflict`; opaque-prose non-conflict, exact structural conflict, and atomic aggregate consequence tests |
| RCI-027 | Restricted inert AST and typed reification outcomes | verified G1 | `rci.formal.ast` closed Boolean/finite-enum union; `ReificationOutcome`; fail-closed reification, interpreter/property, optional-boundary, and exhaustive/Z3 differential tests |
| RCI-028 | Explicit support environments and routes | verified G1 | `SupportEnvironment` pins normalized assumptions, scope, binding, universe, and a `CheckReference` resolved only against aggregate-owned evidence and an authorized independent checker. Promotion and active-theory selection reject missing, forged, mismatched, or unrealizable environments. |
| RCI-029 | Open dependencies are route-specific | verified G1 | each `SupportRoute` owns its required/open dependency boundary, environment, justification/certificate/check refs, warrant refs, and provenance. `PromoteClaim` requires every route to bind the exact recorded warrant decision; grounding and downstream/missing-dependency tests use the route-local boundary. |
| RCI-030 | Minimal support antichain and nogoods | verified G1 | `LemmaSupport` is joined to one `LemmaVersion` comparison class and pins its policy version, separates current `support_routes` from immutable `historical_support_routes`, and validates the current antichain; the selector recomputes the current antichain from `all_support_routes`. Event-owned `Nogood` and append-only route/nogood standing histories deactivate every containing environment while preserving unaffected routes. `test_active_theory_selection_is_exactly_policy_scoped` and `test_owned_nogood_and_route_standing_histories_deactivate_and_reopen`. |
| RCI-031 | Promotion creates linked lemma/L3 view | verified G1 | `decide_promotion`, `LemmaVersion`/`LemmaSupport`/`PromotionLink`; source claims reject L3 mutation and remain unchanged in aggregate promotion/cognitive tests |
| RCI-032 | Positive warrant and ancestry cycles rejected atomically | verified G1 | `support_graph_is_acyclic`, `ancestry_is_acyclic`, `decide_promotion`, aggregate fold validation, and append pre-fold checks reject ungrounded support and invalid ancestry. `test_aggregate_rejects_support_and_ancestry_cycle_routes_without_events` proves command rejection without state change; `test_sqlite_cycle_rejection_rolls_back_stream_and_export` proves typed store rejection with unchanged sequence and byte-identical export. |
| RCI-033 | Guard/support/nogood/applicability invalidation preserves history and can reopen | verified G1 trigger set; retained-residue trigger deferred G3 | append-only `GuardChange`, `SupportRouteStandingChange`, and `NogoodStandingChange` feed the derived exact `TheorySelector`; scope/binding/universe/policy mismatch deactivates selection, while re-selection or standing restoration reopens without rewriting versions, routes, claims, or provenance. Guard, exact-selector, alternate-route nogood, withdrawal/restoration, and history tests cover the G1-owned triggers. Retained-residue change remains gated with executable retention in G3. |
| RCI-034 | Lemma versions owned by semantic memory; support owned by warrant | verified G1 | separate `lemma_versions`, `lemma_supports`, and `promotion_links` state owners with derived `warranted_lemmas`; aggregate alignment invariants and promotion regression |
| RCI-035 | Canonical result surface is typed | verified G1 | strict discriminated canonical result union; `test_every_g1_canonical_role_has_a_strict_schema` and unknown/malformed-role rejection |
| RCI-036 | Exact scoped warrant policy | verified G1 | `decide_evidence_warrant` and `decide_promotion`; exact witness, closed-finite exhaustive, forged universe, dependency/guard, and Z3-only soft-warrant tests |

## Questions, scheduling, interfaces, and cognitive spine

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-037 | Immutable versioned full catalog; only admitted profile schedules | verified G1 | `CATALOG_V0_3` retains stable core contracts and inert draft families with maturity/profile validation; deprecated contracts cannot be newly profiled. Inquiry start stores the exact catalog bytes in CAS and pins its artifact and digest in the manifest; each question request pins its exact contract artifact for replay. Catalog gating and the vertical slice cover the path. |
| RCI-038 | Exact `core-v1` contract set | verified G1 | `CORE_V1` contains exactly the eight named contracts; `test_only_core_v1_is_schedulable_and_rendering_is_literal`; later families are excluded from every schedulable profile |
| RCI-039 | Deterministic dedupe/order/budget/attempt policy | verified G1 | normalized obligation/attempt fingerprints, deterministic safety/priority/depth/creation/ID order, aggregate-owned content-derived `StepPlan`, and 100/3/60 defaults. The SDK passes replay-stable stream sequence as reducer usage and reserves the exact four-event READY batch cost; `test_ready_plan_reserves_its_exact_atomic_event_batch_cost` proves sequence-equivalent use 96 fits exactly and use 97 returns typed Unknown without overshoot. Attempt exhaustion and bounded `run(max_steps)` have focused SDK tests. |
| RCI-040 | SDK/CLI lifecycle parity | verified G1 | SDK exposes every lifecycle method; CLI exposes lifecycle and contract/eval/db/backlog groups; `test_cli_and_sdk_share_the_complete_offline_lifecycle` compares inspect/resume/replay and exported bytes with the SDK |
| RCI-041 | Manual/scripted offline generators; constrained optional OpenAI | verified G1 | manual/scripted generator tests; stateless tool-free bounded OpenAI envelope with explicit model/store=false; persisted fake-client pipeline records raw bytes, status, and usage; network/credentials are not needed by blocking tests |
| RCI-042 | Comparable probes and immutable traces | verified G1 bounded spine | `ProbeIdentity`, warranted `ComparabilityBridge`, ordered `ProbeTrace`; probe identity/bridge unit test and aggregate observation validation |
| RCI-043 | Question-conditioned semantic field is a derived view | verified G1 bounded spine | deterministic `build_semantic_field` returns a non-authoritative view not stored in `InquiryState`; `ProbeEvent` with fresh isolation requires an already captured return and `withheld_until_capture`; semantic-field and aggregate cognitive tests |
| RCI-044 | Probe pattern is provisional; reconstruction/history/knowledge differ | verified G1 bounded spine | provisional probe answer claim plus separate raw return, decode, `Reconstruction`, `SemanticDelta`, and hard-warrant gate; cognitive owner and lifecycle regressions |
| RCI-045 | Eight-state circuit conclusions | verified G1 | `rci.bindings.circuit`; `test_eight_state_circuit_has_the_predetermined_findings` exhausts all eight states and checks the three required findings |
| RCI-046 | Two-route graph bypass and may/must distinction | verified G1 | `rci.bindings.routes`; `test_two_route_graph_proves_may_reach_but_refutes_prerequisite_control` checks both bypass branches and refuses control promotion |

## Consequence quotient, retention, and compression

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-047 | Configuration/history/retained carriers and recovery modes do not collapse | verified G3A-H | explicit `CarrierRole`; unchanged G2 routes; parity/order fixtures; package existence yields no capability before the licensed join |
| RCI-048 | Explicit carrier contract; validation/license/application separate | verified G3A-H exact; deferred G3B approximate | strict `CompressionContract`/`CompressionValidation`/`ExactCompressionLicense`/`CompressionApplication` stages; property checks bind the exact contract fingerprint and property |
| RCI-049 | Route-specific licensed capabilities join package/application/license | verified G3A-H | unchanged G2 route schemas plus `RecoveryLicense` and `RetentionCapabilityLink`; derived capability remains empty until the complete join exists |
| RCI-050 | Path residue differs from open dependency; debt/ancestry/fallback/reopening preserved | implemented G3A-H exact residue; deferred G3B debt | typed `PathResidue`, recoverable parity reopening, missing-residue `Unknown`, and successor lineage tests |
| RCI-051 | Correct exact finite linear-family theorem | active G3A-L | exact rational quotient/kernel construction plus independent Fraction checker |
| RCI-052 | Distributional/vector corollaries with almost-sure scope | active G3A-L | finite positive rational scalar/vector support and uncentered Gram fixtures |
| RCI-053 | Finite-probe rank and only linear minimality | active G3A-L | exact rational rank, redundant/independent probe, and scope-label tests |
| RCI-054 | Generic factorization reopening; linear kernel is one instance | verified G3A-H generic; active G3A-L linear | existing generic owned resolution plus exact old-kernel/new-kernel witness, reversed-inclusion rejection, and mandatory pure-layer `Unknown` |
| RCI-055 | Approximate geometry never establishes exact proof | deferred G3B | numerical near-zero/zero-loss non-promotion tests |
| RCI-056 | Native methods remain isolated adapters | deferred G3C | ADR-0008; container-policy and provenance tests |

## Milestones, governance, and verification

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-057 | G1 is Foundation + Phases 1–2 + bounded cognitive spine | verified G1 | `docs/goals/G1.md`, Python packaging, native Windows/Linux CI, pinned supplementary Docker image, and the implementation evidence itemized above. The frozen 12-command native gate is recorded with all commands exiting 0 in `docs/verification.md`; later retrieval/compression/formal-control/release capabilities remain absent or inert as assigned. |
| RCI-058 | G2 retrieval/consolidation/retention/probes/reacquisition | verified G2A and G2B | ADR-0009/0010, sealed Goals, 170-test local gate, protected PR checks, and successful post-merge workflow 32576841848 |
| RCI-059 | G3A-H/L then G3B/C gate exact history, exact linear, approximate, native | verified G3A-H; active G3A-L; G3B/C deferred | unchanged G3A-H authority plus pure exact-linear binding and focused acceptance; no event/snapshot change |
| RCI-060 | G4–G7 remain separately gated | deferred G4–G7 | later Goals; no G1 stubs |
| RCI-061 | Backlog policy is human-owned and close proposal-only | verified G1 | tracked `.rci/config.toml`; pure reconciliation/apply allowlist; dedicated `BacklogEffectRecorded` ledger ownership rather than synthetic external-return evidence; shadow non-mutation, close proposal-only, checked-evidence, repeat-apply, out-of-order mutation, and linked-recurrence tests |
| RCI-062 | Evidence runners are bounded and lack mutation authority | verified G1 | explicit argv and captured-input models, digest-pinned isolated Docker plan, timeout/output/input bounds, read-only/network-none/capability-drop flags, and runner unit/integration/security tests rejecting mutation, Git, packaging, and release actions. The one Windows symlink-fixture privilege skip is explicitly qualified in `docs/verification.md` and remains live in native Linux CI. |
| RCI-063 | Enumerated G1 blocking evidence exists | verified G1 | Named unit/property/integration/replay/acceptance/security tests cover inert payloads, illegal folds, byte-identical replay/export, CAS tamper/orphan/dangling boundaries, OCC and crash rollback, attempt timeout/cardinality/late acceptance, payload distinctions, separate decode/check/warrant/promotion, independently checked realizability, support/nogood/ancestry topology and rollback, guard/route/policy reopening, probe comparability/fresh isolation, prediction/mismatch, memory separation, unknown relevance, both bindings, SDK/CLI parity, and backlog/runner authority. Recorded returns: 139 passed/1 skipped/4 deselected in the base lane, 143 passed/1 skipped with all extras, and 12 acceptance tests passed. |
| RCI-064 | Verification records exact returns; no stub conformance | verified G1 | `docs/verification.md` records all 12 frozen G1 commands and exact returns: lock/sync/import, Ruff, mypy over 88 files, base and all-extras pytest, 12 acceptance tests, CLI help, and both build artifacts all exited 0. The sole Windows symlink-creation privilege skip and unavailable non-gate `pdflatex` check remain visible rather than being reported as passing assertions. |

## Recovery and future benchmark addendum

| Requirement | Contract | Disposition | Evidence or planned evidence |
|---|---|---|---|
| RCI-065 | Use, reconstruction, direct evaluation, and reacquisition are typed relations | verified G3A-H licensed join | unchanged G2A route separation plus application/route-specific recovery license and capability-link tests |
| RCI-066 | Reacquisition advantage uses typed competence equivalence and pinned frontier | verified G2A provisional comparison; licensed budgets deferred G3B | existing exact-axis/Pareto tests; ADR-0011 forbids reusing history equivalence unless carrier typing permits it |
| RCI-067 | Recovery licence/scaffold; forgetting is reduced capacity; reopening can relearn | verified G3A-H recovery licence; checked forgetting later | G2A saga remains sealed; G3A-H adds separately warranted `RecoveryLicense` without allowing a scaffold/package to self-license |
| RCI-068 | Opaque benchmark includes same-configuration/different-history consequence | research G4–G6; deferred end-to-end G7 | staged capability rows plus required v0.4 path-sensitive case |
| RCI-069 | Aggregate fold and retained-state representation never collapse | verified G3A-H | frozen G1/G2B stream replay, explicit carriers, five-byte history to one-byte retained state, complete ledger replay, and derived-only view |
| RCI-070 | Executable retained state requires continuation compatibility | verified G3A-H | unbounded unary base/step congruence, present-answer/future-continuation counterexample, and lawful answer-only scope narrowing |
| RCI-071 | Representation replacement requires preserve + gain + warrant or frontier | verified G3A-H | positive warranted successor, atomic predecessor-capability-loss rejection, novelty-only rejection, and explicit incomparability |
| RCI-072 | Repository inquiry pins an exact clean project anchor without creating a second source history | verified G3R | strict `ProjectAnchor`, exact commit propagation, candidate-environment anchor checks, Git/ledger ownership rules in ADR-0012/0013, and PR/main exact-head evidence |
| RCI-073 | A project limitation requires a protected consequential boundary | verified G3R | `CapabilityLimitation` requires current/desired consequence and a separating observation; empty dissatisfaction and novelty cannot enter the frontier |
| RCI-074 | Question repertoire succession is typed, inert, attacked, and independently admitted | verified G3Q | Exact admission plus the derived `CompiledQuestionContract` registry, context/policy pins, ordinary scheduling, provisional return routing, adversarial acceptance, fresh exact-head review, protected promotion, and seven-check post-merge CI |
| RCI-075 | Method repertoire succession binds native assumptions and does not install itself | verified G3R | `MethodBindingCandidate`, preserved primary-source/applicability/license pins, exact independently reviewed evidence, separate `MethodAdmissionDecision`, and exact Goal linkage when an adapter is absent |
| RCI-076 | Project successors use a partial-order frontier and immutable discriminator-first Goal | verified G3G | exact `CapabilitySuccessorCandidate`, permutation-stable frontiers, deterministic `ImplementationGoalCandidate`, one total `GoalAdmissionDecision`, immutable admitted `ImplementationGoalContract`, confined gate/mutation registries, protected PR/main promotion, eight-check hosted CI, and `test_goal_synthesis.py` |
| RCI-077 | Candidate actualization, evidence, review, successor decision, and promotion remain separate | verified G3R | `CandidateEnvironmentManifest`, exact-head evidence, different-context review, exact reviewed-evidence successor and promotion stages, complete SDK/CLI recording surface, protected merge, and absence of runtime source/Git ports |
| RCI-078 | Recursive project inquiry has append-only continuity and typed stopping | verified G3R | `RecursiveCycleCheckpoint`, predecessor/phase monotonicity, `RecursiveStopDisposition`, `Unknown` paths, durable cycle handoff/report, and bounded blocker rule |
| RCI-079 | Bounded mechanical review is exact-profile-relative and never substitutes for fresh semantic review | unverified; stopped G3V candidate | ADR-0015 and candidate `a425f4b0dfa5b2c52a67df87d460f25e4e825518`; its closed profile and hosted CI passed, but fresh semantic review was unavailable, so no implementation, successor decision, or promotion entered protected main |

### RCI-068 staged capability evidence

| Stage | Capability delivered independently | What it does not yet claim |
|---|---|---|
| G1 | Verified raw-return authority, attempt alignment, sealed predictions, and basic probe records under the frozen G1 gate | No learned opaque state or benchmark pass |
| G2A | Verified deterministic structural retrieval, candidate reconstruction, provisional retention routes, reacquisition scaffold/saga, and soft Pareto comparison on local and hosted Windows/Linux/Docker gates | No consolidation, learned probe, recovery licence, certified quotient, or control |
| G2B | Verified deterministic consolidation/reconsolidation, conservative semantic-field evaluation, and checked learned probes | No recovery licence, certified quotient, automaton dependency, or control |
| G3A-H | Verified exact history-state carriers, quotient validation, recovery licence, residue, reopening, and representation ratchet | No SymPy linear binding, approximation, native adapter, or control |
| G3R | Verified recursive project inquiry, repertoire/frontier succession, sealed Goals, isolated candidate evidence, fresh review, and externally observed promotion | No runtime source/Git authority |
| G3Q | Verified confined regenerative question scheduling | No arbitrary code, general planner, source authority, or automatic warrant |
| G3G | Verified confined implementation-Goal synthesis; selection anchor `60ff25635f94fb004e6419a09293c5e0fc023074`, protected implementation `5f48d397030b6a063fdca19e51b70a824096e564` | No free-form commands/paths, general planner, actuator, or authority expansion |
| G3V | Stopped-indeterminate bounded review candidate preserved at `a425f4b0dfa5b2c52a67df87d460f25e4e825518` | No standing implementation, fresh semantic-review substitution, successor warrant, or promotion authority |
| G3FO | Stopped-indeterminate failure-observation candidate preserved at `b3cb06363ac5b8cd60c9bfbda5c3fbdd7dca72fb` | No standing evaluator/handoff, model adapter, source/Git authority, review substitution, or promotion authority |
| G3Q-F | Candidate finite dependent frames and bounded compositional grammar; not selected | Requires two distinct verified question/frame-blindness bindings; no grammar, new requirement, or semantic replacement is standing |
| G3A-L | Active exact finite rational linear binding | No approximation, native adapter, raw-environment system identification, or unrestricted minimality |
| G3B/G3C | Approximate licences, then native adapters | No raw-environment system identification |
| G4 | Formal identification seam and future PSR/native-binding evaluation | No control certificate |
| G5 | Checked control synthesis/actualization | No multi-backend or end-to-end claim |
| G6 | Multi-backend evidence for learned relations | No production benchmark hardening |
| G7 | Pinned opaque environment, transfer conditions, evaluation frontier, hardening | End-to-end acceptance only here |

The linear consequence theorem is evidence for RCI-051–RCI-055 only after a
warranted vector representation and linear protected query family are supplied.
It is never evidence about raw opaque memory by itself.
