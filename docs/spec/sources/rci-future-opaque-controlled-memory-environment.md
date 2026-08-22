# Future Test: Opaque Controlled Memory Environment

## Purpose

This test evaluates whether the system can learn a usable relational model of an initially opaque controlled environment through repeated action, observation, comparison, reconstruction, warrant, memory, and relearning.

The environment is a game or game-like executable system whose internal state is exposed to the agent primarily as a raw memory stream.

The agent is not given the semantic interpretation of that memory.

It must discover, through interaction, which parts of the memory stream correspond to its own interventions, which changes are consequences of those interventions, which distinctions predict future behavior, which relations are conditional, which representations expose those relations, and which discovered structure is sufficient for future prediction and control.

The target is not exhaustive reverse engineering.

The target is:

[
\boxed{
\textbf{
RECOVER THE SMALLEST REGENERATIVELY SUFFICIENT RELATIONAL STATE
FOR THE PROTECTED FUTURE INTERACTIONS.
}}
]

This environment is intended as a future end-to-end test of RCI rather than as a new primitive of the formalism.

---

# 1. Test principle

The system begins with:

[
\boxed{
\text{known interventions}
+
\text{opaque returns}
+
\text{ordered interaction history}.
}
]

It must construct the useful state representation itself.

Let the raw memory state at time (t) be:

[
\boxed{
m_t\in\mathcal M_{\mathrm{raw}}.
}
]

For a byte-addressable memory region, one possible binding is:

[
\mathcal M_{\mathrm{raw}}
=========================

{0,\ldots,255}^{N}.
]

Let the set of interventions available to the agent be:

[
\boxed{
\mathcal A
==========

{a_1,\ldots,a_k}.
}
]

Examples may include:

[
LEFT,\ RIGHT,\ UP,\ DOWN,\ JUMP,\ FIRE,\ NONE.
]

The environment evolves according to an initially unknown relation:

[
\boxed{
R:
\mathcal M_{\mathrm{raw}}
\times
\mathcal A
\rightsquigarrow
\mathcal M_{\mathrm{raw}}.
}
]

The agent observes an ordered interaction stream:

[
\boxed{
H_t
===

(
m_0,
a_0,
m_1,
a_1,
m_2,
\ldots,
a_{t-1},
m_t
).
}
]

It is not told the semantic variables underlying (R).

---

# 2. What the agent must not be given

The benchmark should withhold, unless explicitly introduced in a later test condition:

* source-code variable names;
* memory maps;
* object labels;
* player coordinates;
* velocity labels;
* health labels;
* game-state labels;
* collision flags;
* inventory schemas;
* controller-memory mappings;
* programmer-authored state machines;
* semantic annotations of addresses;
* privileged access to the game's internal object model.

The benchmark should not begin with statements such as:

```text
0x043A = player_x
0x043B = player_x_high
0x0812 = grounded
```

Instead it exposes observations such as:

```text
address 0x043A changed 31 -> 32
address 0x0812 remained 1
...
```

The distinction is fundamental:

[
\boxed{
\text{memory address}
\neq
\text{semantic variable}.
}
]

A semantic role must be earned from observed relations.

---

# 3. Minimal environment interface

The minimum useful interface is:

```text
observe_memory() -> RawMemoryReturn
act(action) -> AttemptOutcome
step(frames = 1) -> AttemptOutcome
```

A stronger experimental environment should also provide:

```text
save_state() -> StateHandle
load_state(handle)
reset()
```

Optional later capabilities may include:

```text
observe_screen()
observe_audio()
write_memory(...)
```

but these should not be required for the basic test.

The preferred initial test is read-only with respect to memory:

[
\boxed{
\text{the agent controls the game through legitimate actions,
not arbitrary memory writes}.
}
]

This keeps intervention semantics clear.

---

# 4. Raw observations must remain authoritative

Each actual memory observation is an external return.

Define:

[
\boxed{
r_t^{mem}
=========

ExternalReturn(m_t).
}
]

The system must preserve:

[
\boxed{
RawMemoryReturn
\neq
Interpretation(RawMemoryReturn).
}
]

A generated interpretation such as:

> address (i) may encode horizontal position

must remain a candidate relation until independently constrained.

The test therefore exercises:

[
\boxed{
\text{actual return}
\neq
\text{generated explanation}
\neq
\text{warranted relation}.
}
]

---

# 5. First required discovery: intervention ingress

The first major target is to discover where and how the system's own actions become visible in the memory stream.

Suppose the agent issues:

[
a_t=RIGHT.
]

It compares memory before and after the intervention:

[
\Delta_t
========

Diff(m_t,m_{t+1}).
]

One crude initial form is:

[
\boxed{
D_t
===

{i:m_t\neq m_{t+1}[i]}.
}
]

This set does not identify causes.

It only identifies changed observations.

The agent must repeatedly vary the known intervention:

[
LEFT,\ RIGHT,\ NONE,\ JUMP,\ldots
]

while controlling other differences as far as possible.

It should search for memory structure satisfying relations such as:

[
\boxed{
a_t
\leftrightarrow
u_t
}
]

where (u_t) is a discovered memory-side representation of the intervention.

A possible learned relation might eventually be:

[
LEFT\mapsto01,\qquad
RIGHT\mapsto02,\qquad
NONE\mapsto00.
]

But this remains provisional until attacked.

Required questions include:

* Does the candidate memory region change whenever the action changes?
* Can it change without the action changing?
* Does the relation survive different game contexts?
* Is it an immediate representation of input, a delayed consequence, or merely correlated downstream state?
* What happens on release?
* What happens under combinations of actions?
* Does the mapping change across modes?

The test should require the agent to distinguish:

[
\boxed{
\text{action representation}
\neq
\text{action consequence}.
}
]

---

# 6. Required discovery of temporal succession

The agent must not rely only on same-frame correlation.

It must be capable of discovering lagged relations:

[
\boxed{
a_t
\to
m_{t+k}[i].
}
]

For multiple lags:

[
k=0,1,\ldots,K.
]

A discovered chain may resemble:

[
Action_t
\to
InputState_t
\to
Velocity_{t+1}
\to
Position_{t+2}
\to
Camera_{t+3}.
]

The semantic labels are not supplied.

The agent must infer the relational structure first.

Therefore the benchmark must test whether it distinguishes:

[
\boxed{
\text{co-occurrence}
\neq
\text{succession}.
}
]

and:

[
\boxed{
\text{immediate response}
\neq
\text{delayed consequence}.
}
]

---

# 7. Controlled branching should be available in the stronger benchmark

Save-state branching gives the system genuine controlled comparisons.

Given one common state (s):

[
s
\xrightarrow{LEFT}
s_L,
]

[
s
\xrightarrow{RIGHT}
s_R,
]

[
s
\xrightarrow{NONE}
s_N.
]

The agent can then compare:

[
\Delta_L=Diff(s,s_L),
]

[
\Delta_R=Diff(s,s_R),
]

[
\Delta_N=Diff(s,s_N).
]

This is substantially stronger than observing unrelated trajectories.

It allows:

[
\boxed{
\text{hold starting state fixed;
vary intervention}.
}
]

The benchmark should encourage this whenever the environment permits it.

---

# 8. Candidate variables must be constructible

The useful state may not correspond to individual bytes.

The system must be permitted and expected to construct derived probes.

Examples:

[
p_1(m)=m[i],
]

[
p_2(m)=m[i]+256m[i+1],
]

[
p_3(m)=m[i]\oplus m[j],
]

[
p_4(m_t,m_{t-1})=m_t[i]-m_{t-1}[i],
]

[
p_5(H_t)=
\text{periodicity of address }i.
]

The agent might begin with two apparently noisy bytes and discover:

[
\boxed{
x_t
===

m_t[i]
+
256m_t[i+1].
}
]

If (x_t) exposes a stable action-dependent relation that neither byte does individually, the new probe has produced representational progress.

Therefore:

[
\boxed{
\text{learning the environment}
\neq
\text{only learning facts within a fixed observation basis}.
}
]

The system must also be capable of:

[
\boxed{
\text{learning better ways to observe the environment}.
}
]

---

# 9. Probe learning requirement

A generated probe (p') must not be promoted merely because it produces an interpretable pattern.

It must demonstrate nonredundant consequential discrimination.

A suitable criterion is:

[
\boxed{
p'\text{ is promotable}
\Rightarrow
\exists x,y:
\text{old probes fail to distinguish }x,y
\land
p'(x)\neq p'(y)
\land
\Phi(x)\neq\Phi(y)
}
]

or another binding-appropriate demonstration that the new probe materially improves:

* prediction;
* control;
* discrimination;
* reconstruction;
* reacquisition.

A new probe that merely restates an existing distinction should be considered redundant unless it improves another protected resource such as cost or robustness.

---

# 10. The agent must construct conditional relations

A relation such as:

[
RIGHT
\Rightarrow
x_{t+1}>x_t
]

will often fail in some contexts.

The system must not respond by immediately discarding the relation or silently adding arbitrary exceptions.

Instead the failure creates an open dependency:

[
\boxed{
d\in\partial^-\lambda.
}
]

The next inquiry becomes:

> What consequential state distinction separates cases in which the relation holds from cases in which it fails?

For example:

[
RIGHT\land g
\Rightarrow
x_{t+1}>x_t.
]

The agent must then investigate (g).

It may eventually discover a relation corresponding to:

* collision;
* menu state;
* immobilization;
* airborne state;
* animation phase;
* input lock;
* game mode.

Again, the label is secondary.

What matters first is the relational separation.

---

# 11. Support environments must be exercised

Suppose a learned relation can stand under either of two independent contexts:

[
E_1\vdash\lambda,
\qquad
E_2\vdash\lambda.
]

The environment should eventually include cases capable of showing that:

[
\boxed{
\mathsf{Supp}(\lambda)
======================

{E_1,E_2}
}
]

rather than flattening the relation into one brittle guard.

If one support route disappears, another must be allowed to keep the relation active.

Thus the benchmark can test the repaired warrant architecture:

[
\boxed{
\text{loss of one support environment}
\neq
\text{automatic loss of the relation}.
}
]

---

# 12. Stretch test

For a candidate consequence (C), the agent must seek multiple states satisfying:

[
C(x_i)=C.
]

Then vary as much else as possible.

The test question is:

[
\boxed{
\text{What can change while the protected consequence remains the same?}
}
]

For example, if a candidate memory structure appears to determine movement, search for movement episodes with:

* different unrelated memory values;
* different animation states;
* different scores;
* different backgrounds;
* different histories;
* different nearby entities.

Any supposed prerequisite that varies freely is weakened.

This is:

[
\boxed{
\textbf{STRETCH WITHIN CONSEQUENCE CLASS}.
}
]

---

# 13. Squeeze test

The agent must also seek pairs:

[
x,y
]

such that:

[
\Phi(x)\neq\Phi(y)
]

while minimizing relevant difference between them.

The target question is:

[
\boxed{
\text{What is the least change that makes the consequence different?}
}
]

Save-state branching is ideal for this.

The result is a candidate separator:

[
p(x)\neq p(y).
]

But the system must preserve:

[
\boxed{
\text{separator}
\neq
\text{unique cause}.
}
]

The separator becomes an object for further attack.

---

# 14. Prediction must precede consequential tests

Once a candidate relation exists, the system should make explicit predictions before acting.

For example:

```text
PredictionSeal {
    if RIGHT is issued from state S:
        probe P1 should increase
        probe P2 should remain stable
        probe P3 should change after 2 frames
}
```

Then:

[
\boxed{
PredictionSeal
\prec
Attempt
\prec
ExternalReturn.
}
]

The benchmark should penalize systems that reinterpret their prediction after observing the result.

Mismatch must become a new inquiry object.

---

# 15. The system must learn a predictive state, not just correlations

The central benchmark objective is to construct a state representation:

[
\boxed{
z_t=\phi(H_t)
}
]

such that (z_t) is sufficient for the protected future interactions.

For an admitted family of future tests (\mathcal T):

[
\boxed{
H_t\equiv_{\mathcal T}H'_t
}
]

iff every protected future action-observation test has equivalent consequential outcome from both histories.

The learned state should therefore satisfy:

[
\boxed{
\phi(H_t)=\phi(H'*t)
\Rightarrow
H_t\equiv*{\mathcal T}H'_t.
}
]

The ideal representation approaches the coarsest such quotient.

The target is not:

[
\text{reproduce all raw RAM}.
]

It is:

[
\boxed{
\text{preserve what protected future interaction can distinguish}.
}
]

---

# 16. Predictive State Representation is a relevant native binding

A mature formal precedent for this target is the Predictive State Representation idea:

[
\boxed{
\text{state may be represented by predictions of future
action-observation tests rather than supplied hidden variables}.
}
]

RCI should treat PSR-like machinery as a native formal binding for the opaque controlled-environment problem.

The benchmark should not require the RCI implementation to invent a new hidden-state formalism if PSR/system-identification machinery supplies a stronger established method.

---

# 17. Behavioral equivalence is the primary quotient

For histories or states (h,h'), define:

[
\boxed{
h\equiv_{\mathcal T}h'
}
]

when every admitted protected future test produces equivalent consequences:

[
\boxed{
\forall \tau\in\mathcal T,
\qquad
Cons_\tau(h)=Cons_\tau(h').
}
]

Then:

[
\boxed{
\mathcal H/{\equiv_{\mathcal T}}
}
]

is the behavioral consequence quotient of the environment relative to the protected future test family.

This is the general object the agent is trying to discover.

---

# 18. The Consequence Subspace Theorem is a later optional binding

The raw memory environment must not be assumed linear.

However, if the system later constructs:

[
z_t=\phi(H_t)\in\mathbb R^d
]

and the protected query family becomes linear:

[
Cons_q(z)=q^\top z,
]

then the Consequence Subspace Theorem becomes applicable.

Define:

[
M_Q=\mathbb E[qq^\top].
]

Then:

[
\boxed{
z\sim_Qz'
\iff
z-z'\in\ker M_Q
}
]

and the coarsest exact linear quotient is:

[
\boxed{
\mathbb R^d/\ker M_Q
\cong
\operatorname{im}M_Q.
}
]

Thus the benchmark can eventually test whether the system knows when a native theorem becomes applicable to a representation it has learned.

It must not force that theorem onto the raw environment.

---

# 19. Memory requirements

The benchmark must not be solvable by keeping every raw observation in active context forever.

The system must progressively distinguish:

[
M_E,
\quad
M_S,
\quad
M_P,
\quad
M_L.
]

### Episodic retention

Keep consequential action-return episodes and authoritative raw provenance.

### Semantic retention

Promote warranted relational structure such as:

[
Action
\xrightarrow[\text{condition}]{}
DerivedStateChange.
]

### Procedural retention

Retain useful ways of interrogating the environment:

* action branching procedures;
* lag scans;
* byte-combination probes;
* boundary searches;
* stable comparison procedures.

### Latent retention

Preserve compressed distinctions, reopening conditions, reacquisition scaffolds, and unresolved relevance.

---

# 20. The benchmark must test compression

After sufficient learning, the system should be required to reduce its active representation.

Given a learned representation (z), ask:

[
\boxed{
\text{Which distinctions can be removed without changing
protected future prediction or control?}
}
]

The system should attempt to merge equivalent states or retire redundant probes.

Compression must preserve:

* protected future behavior;
* open dependencies;
* warrant/provenance;
* reopening conditions;
* required reconstruction paths;
* required reacquisition paths.

Thus:

[
\boxed{
\text{inactive detail}
\neq
\text{forgotten detail}.
}
]

---

# 21. The benchmark must test reopening

After the agent has compressed a distinction as consequence-null, alter the protected future.

For example, introduce:

* a new action;
* a new objective;
* a new future query;
* a new game regime;
* a new environment mode;
* a longer prediction horizon.

A previously invisible distinction should now matter.

The system must:

1. detect that its existing quotient is insufficient;
2. reopen the compressed distinction or its provenance;
3. generate a representation/probe obligation;
4. refine its state model;
5. preserve ancestry of the old compression licence.

This tests:

[
\boxed{
\text{current equivalence}
\neq
\text{permanent equivalence}.
}
]

---

# 22. The benchmark must test relearning savings

After the system has successfully learned a relational model:

1. remove the active working representation;
2. retain only the memory package permitted by the retention policy;
3. wait or introduce unrelated intervening tasks;
4. return to the original environment or an equivalent regime;
5. measure reacquisition cost.

Compare:

[
\mathfrak C_{\mathcal H}(m_{\mathrm{retained}},c,k)
]

against a baseline:

[
\mathfrak C_{\mathcal H}(m_\bot,c,k).
]

The system demonstrates retained learning when:

[
\boxed{
\mathfrak C_{\mathcal H}(m_{\mathrm{retained}},c,k)
\prec
\mathfrak C_{\mathcal H}(m_\bot,c,k).
}
]

This remains true even if:

[
Recall(m_{\mathrm{retained}},c,k)=0.
]

Therefore the benchmark tests:

[
\boxed{
\text{memory as reacquisition advantage}.
}
]

---

# 23. Transfer test

A stronger version should alter the environment while preserving some relational structure.

Examples:

* different level;
* different map;
* shifted memory addresses;
* altered object layout;
* related game version;
* same dynamics under changed encoding.

The system must distinguish:

[
\boxed{
\text{representation identity}
\neq
\text{relational identity}.
}
]

A good learned model should permit some relations, probes, or learning procedures to transfer even if raw addresses do not.

This tests whether the agent retained:

[
\text{the old bytes}
]

or:

[
\boxed{
\text{the relational organization that made those bytes useful}.
}
]

---

# 24. Required progression

A successful system should be capable of progressing through something like:

[
\boxed{
\begin{array}{c}
\text{RAW MEMORY STREAM}\
\downarrow\
\text{CHANGE DETECTION}\
\downarrow\
\text{INTERVENTION FOOTPRINT}\
\downarrow\
\text{TEMPORAL DEPENDENCIES}\
\downarrow\
\text{DERIVED PROBES}\
\downarrow\
\text{CANDIDATE VARIABLES}\
\downarrow\
\text{CONDITIONAL RELATIONS}\
\downarrow\
\text{PREDICTIVE STATE}\
\downarrow\
\text{CONTROL MODEL}\
\downarrow\
\text{CONSEQUENCE QUOTIENT}\
\downarrow\
\text{COMPRESSION}\
\downarrow\
\text{REOPENING / RELEARNING}.
\end{array}}
]

This is not a mandatory fixed algorithmic sequence.

Stages may recurse, interleave, or reopen.

It is the expected developmental structure of the test.

---

# 25. Required agent capabilities

The test requires the project eventually to support the following.

### Observation

* immutable raw memory returns;
* memory differencing;
* temporal alignment;
* ordered observation traces.

### Intervention

* explicit action attempts;
* save/load branching when available;
* exact association between attempt and returned state.

### Prediction

* prediction sealing before tests;
* mismatch generation.

### Probe generation

* primitive address probes;
* multi-address derived probes;
* temporal probes;
* conditional probes;
* probe promotion and retirement.

### Relational discovery

* covariance/correlation as candidate generation only;
* lagged dependency discovery;
* stretch;
* squeeze;
* counterexample generation;
* prerequisite discovery;
* boundary localization.

### Warrant

* support environments;
* open dependency boundaries;
* explicit unresolved dependencies;
* no self-licensing.

### Representation

* candidate state abstractions;
* comparison of alternative abstractions;
* representation-gap detection;
* rebind when current representation cannot express a discovered distinction.

### Memory

* episodic trace retention;
* semantic consolidation;
* procedural probe/method retention;
* latent/reopening structure;
* reacquisition scaffolds.

### Compression

* consequence-equivalence testing;
* redundant probe retirement;
* state merging;
* compression licences;
* residual and reopening preservation.

### Relearning

* reopening;
* scaffold activation;
* measurement of reacquisition advantage.

---

# 26. Required permanent distinctions

The benchmark must test that the implementation preserves:

[
\boxed{
\text{raw RAM difference}
\neq
\text{semantic difference}
}
]

[
\boxed{
\text{changed byte}
\neq
\text{causal variable}
}
]

[
\boxed{
\text{correlation}
\neq
\text{dependency}
}
]

[
\boxed{
\text{separator}
\neq
\text{unique cause}
}
]

[
\boxed{
\text{action representation}
\neq
\text{action consequence}
}
]

[
\boxed{
\text{same-frame association}
\neq
\text{temporal dependence}
}
]

[
\boxed{
\text{candidate variable}
\neq
\text{warranted state variable}
}
]

[
\boxed{
\text{predictive variable}
\neq
\text{control handle}
}
]

[
\boxed{
\text{same raw state}
\neq
\text{same consequential state}
}
]

and conversely:

[
\boxed{
\text{different raw states}
\neq
\text{different consequential states}.
}
]

Also:

[
\boxed{
\text{current probe failure}
\neq
\text{absence of a distinction}
}
]

[
\boxed{
\text{compressed}
\neq
\text{forgotten}
}
]

[
\boxed{
\text{failure to recall}
\neq
\text{absence of retained learning}.
}
]

---

# 27. Core acceptance tests

At minimum, the future benchmark should contain fixtures equivalent to:

```text
AGENT_CAN_IDENTIFY_AN_ACTION_CORRELATED_MEMORY_FOOTPRINT

ACTION_FOOTPRINT_IS_NOT_AUTOMATICALLY_CLASSIFIED_AS_CAUSE

AGENT_CAN_DISCOVER_A_LAGGED_ACTION_RETURN_RELATION

AGENT_CAN_BRANCH_FROM_A_COMMON_STATE_AND_COMPARE_INTERVENTIONS

AGENT_CAN_CONSTRUCT_A_MULTI_BYTE_OR_DERIVED_PROBE

NEW_PROBE_REQUIRES_NONREDUNDANT_CONSEQUENTIAL_DISCRIMINATION

SAME_ACTION_DIFFERENT_OUTCOME_CREATES_OPEN_DEPENDENCY

OPEN_DEPENDENCY_GENERATES_A_NEW_INQUIRY

ALTERNATE_SUPPORT_ROUTE_SURVIVES_LOSS_OF_ONE_ROUTE

AGENT_CAN_LOCALIZE_A_BOUNDARY_WITH_STRETCH_AND_SQUEEZE

SEPARATOR_IS_NOT_PROMOTED_TO_UNIQUE_CAUSE

PREDICTION_IS_SEALED_BEFORE_ACTION_RETURN

RAW_MEMORY_RETURN_IS_PRESERVED_BEFORE_INTERPRETATION

MISMATCH_REOPENS_THE_CURRENT_MODEL

AGENT_CAN_BUILD_A_STATE_REPRESENTATION_THAT_PREDICTS_FUTURE_TESTS

AGENT_CAN_MERGE_RAWLY_DIFFERENT_BUT_BEHAVIORALLY_EQUIVALENT_STATES

AGENT_CAN_SEPARATE_RAWLY_SIMILAR_BUT_BEHAVIORALLY_DISTINCT_STATES

AGENT_CAN_RETIRE_A_REDUNDANT_PROBE

COMPRESSION_PRESERVES_OPEN_DEPENDENCIES_AND_REOPENING

NEW_PROTECTED_INTERACTION_REOPENS_A_PREVIOUSLY_COMPRESSED_DISTINCTION

REACQUISITION_FROM_RETAINED_STATE_IS_CHEAPER_THAN_BASELINE_LEARNING

FAILED_DIRECT_RECALL_DOES_NOT_ERASE_REACQUISITION_ADVANTAGE

TRANSFER_CAN_PRESERVE_RELATIONS_WHILE_RAW_MEMORY_ADDRESSES_CHANGE
```

---

# 28. Evaluation criteria

Do not score the system only by whether it eventually wins the game.

Evaluate several independent dimensions.

### Predictive competence

How accurately can the learned state predict selected future returns?

### Intervention competence

Can the system produce selected consequential transitions deliberately?

### Representation efficiency

How small is the retained state relative to its protected predictive/control competence?

### Probe efficiency

How many observations/interventions are required to discover useful distinctions?

### Warrant discipline

How often are provisional correlations incorrectly promoted?

### Reopening competence

Can the system detect when a prior abstraction ceases to be sufficient?

### Reacquisition efficiency

How much cheaper is relearning from retained state than from baseline?

### Transfer

Which learned relational structures survive representational changes?

The intended result is a frontier rather than one universal score:

[
\boxed{
Frontier(
Prediction,
Control,
RepresentationCost,
InteractionCost,
WarrantQuality,
Reopening,
Reacquisition,
Transfer
).
}
]

---

# 29. Strong success condition

The benchmark is not passed merely when the agent has identified many memory addresses.

The strong condition is that it has constructed a state (z_t) such that:

[
\boxed{
z_t=\phi(H_t)
}
]

supports the protected future interactions with acceptable fidelity while omitting raw distinctions that those future interactions cannot inspect.

And when the protected horizon changes, the system can:

[
\boxed{
\text{reopen}
\to
\text{refine}
\to
\text{relearn}
}
]

without discarding the ancestry of how the earlier model was warranted.

Thus:

[
\boxed{
\textbf{
SUCCESS IS NOT A MEMORY MAP.
SUCCESS IS A COMPACT, WARRANTED, REOPENABLE RELATIONAL MODEL
THAT SUPPORTS PREDICTION, CONTROL, AND FUTURE LEARNING.
}}
]

---

# 30. Why this test belongs in RCI

This benchmark forces the architecture to establish rather than assume nearly every important object:

[
\boxed{
\begin{aligned}
\text{variables} &\quad\text{must be discovered},\
\text{probes} &\quad\text{must be learned},\
\text{state} &\quad\text{must be reconstructed},\
\text{dependencies} &\quad\text{must be tested},\
\text{boundaries} &\quad\text{must be localized},\
\text{conditions} &\quad\text{must be exposed},\
\text{equivalences} &\quad\text{must be warranted},\
\text{control} &\quad\text{must be actualized},\
\text{memory} &\quad\text{must be compressed},\
\text{forgotten competence} &\quad\text{must be reacquirable},\
\text{new relevance} &\quad\text{must reopen the model}.
\end{aligned}}
]

The environment contributes actuality and the ability to intervene.

The agent must construct the rest.

That makes the test an unusually complete operational witness of the project's central recurrence:

[
\boxed{
\textbf{
LOOK
\to
ACT
\to
RETURN
\to
COMPARE
\to
DISTINGUISH
\to
MODEL
\to
TEST
\to
LEARN
\to
COMPRESS
\to
REMEMBER
\to
REOPEN
\to
LOOK AGAIN.
}}
]

Its governing objective is:

[
\boxed{
\textbf{
RECOVER, RETAIN, AND CONTINUALLY REVISE THE SMALLEST
RELATIONAL STATE FROM WHICH THE PROTECTED FUTURE INTERACTIONS
CAN BE PREDICTED, CONTROLLED, RECONSTRUCTED, OR REACQUIRED
WITHIN THEIR LICENSED COST.
}}
]
