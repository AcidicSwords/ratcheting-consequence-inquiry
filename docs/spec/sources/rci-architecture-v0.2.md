# Ratcheting Consequence Inquiry 0.2

## A Question-Conditioned Architecture for Composable Fallibility, Consequence-Directed Reasoning, and Warranted Semantic Refinement

**Version:** 0.2
**Status:** Project theory, architecture, and implementation specification
**Replaces:** RCI 0.1

RCI 0.2 incorporates the architectural revision that questions do more than type claims: they temporarily reorganize semantic accessibility, suppress presently irrelevant structure, expose reopening conditions, and make domain-native methods relationally adjacent to the current inquiry. 

---

# 1. Abstract

Ratcheting Consequence Inquiry (RCI) is a domain-agnostic architecture for inquiry in which **questions are executable relational operators over an evolving semantic state**.

RCI separates:

1. **what is currently unresolved;**
2. **what consequence makes alternatives different;**
3. **what question is lawful and useful next;**
4. **what semantic material becomes locally relevant under that question;**
5. **what candidate claim an answer is being offered as;**
6. **what formal or domain-native operations may consume that claim;**
7. **what independent return constrains it;**
8. **what may become warranted;**
9. **what distinctions may then be split, merged, hidden, or reopened;**
10. **what consequential residual becomes the center of the next inquiry.**

The central type discipline is:

[
\boxed{
Q_\tau:
(\Sigma,O)
\rightsquigarrow
\operatorname{Claim}[\tau]
}
]

rather than:

[
Q_\tau:
(\Sigma,O)
\rightsquigarrow
\tau.
]

A question establishes what **role** an answer is being offered to play. The answer need not initially be correct, complete, or deeply parsed.

Thus:

[
\boxed{
\text{well-typed claim}
\neq
\text{true claim}.
}
]

The system is explicitly designed so that an untrusted semantic generator may return bad answers without corrupting the formal architecture.

Incorrect claims become material for:

* counterexample;
* contradiction;
* scope restriction;
* hidden-guard discovery;
* alternate-route search;
* reification failure;
* abstraction refinement;
* or further inquiry.

This principle is summarized as:

[
\boxed{
\textbf{fallibility must be composable.}
}
]

RCI 0.2 further recognizes that a question does not merely type its answer. It creates a **question-conditioned semantic field**:

[
\boxed{
\mathcal F_q
}
]

which determines:

* what is currently foregrounded;
* what distinctions are temporarily quotientable;
* what distant semantic material becomes relationally relevant;
* which methods become applicable;
* what is suppressed;
* and what would cause suppressed structure to reopen.

Hence the full effect of a question is:

[
\boxed{
\textbf{
QUESTION
========

RELATIONAL ROLE
+
SEMANTIC DEFORMATION
+
CONTEXTUAL OCCLUSION
+
REOPENING FRONTIER.
}
}
]

RCI therefore operates simultaneously as:

* a theory of inquiry;
* a typed conversational protocol;
* an abstraction-refinement architecture;
* a semantic context-management system;
* an agent control loop;
* and a framework for integrating formal solvers, domain-native methods, experiments, retrieval, execution, and other independent returns.

---

# 2. Governing idea

RCI does not require a system to generate a correct chain of reasoning from the outset.

Instead it repeatedly asks:

[
\boxed{
\text{What difference matters?}
}
]

and:

[
\boxed{
\text{What would make that difference?}
}
]

while subjecting every proposed necessity, sufficiency, prerequisite, explanation, and transformation to adversarial pressure.

The system alternates between two geometric operations.

### Stretch within consequence

[
\boxed{
\text{Change as much as possible while consequence remains fixed.}
}
]

### Squeeze across consequence

[
\boxed{
\text{Change as little as possible while consequence changes.}
}
]

Stretch destroys accidental commonality.

Squeeze exposes consequential boundaries.

The surviving relation is not automatically treated as true, explanatory, or controllable. It is attacked, actualized, independently constrained, generalized only as far as warranted, then compressed into the retained state.

---

# 3. The epistemic ratchet

The system distinguishes:

[
\boxed{
\text{generation}
\neq
\text{retention}.
}
]

Semantic generation may be expansive, speculative, inconsistent, and noisy.

Retained inquiry state should change only through consequential progress.

The principal monotone structure is not the active possibility region.

It is the guarded warrant store:

[
\boxed{
\Theta_{t+1}
============

\Theta_t\cup{\lambda_{t+1}}.
}
]

where each:

[
\lambda=(g,\ell,\sigma,w,\Gamma,\pi)
]

contains:

* guard (g);
* learned relation (\ell);
* scope (\sigma);
* warrant class (w);
* antecedent dependencies (\Gamma);
* certificate or provenance (\pi).

The active theory may shrink or expand as guards change.

The permanent epistemic ratchet need not forget the original warrant.

Thus:

[
\boxed{
\textbf{reopening is guard deactivation, not epistemic amnesia.}
}
]

---

# 4. Formal binding

An inquiry is conducted relative to:

[
\boxed{
\mathfrak B
===========

(
\mathbf X,
\mathcal L,
\mathcal A,
\mathcal U,
\mathcal H,
\mathcal M,
\mathcal E
).
}
]

Where:

* (\mathbf X={X_\tau}): typed carriers;
* (\mathcal L): predicates, relations, constructions, abstractions, and expressions available to inquiry;
* (\mathcal A): admissible arrangement deformations;
* (\mathcal U): admissible successions or transformations;
* (\mathcal H): protected consequence horizon;
* (\mathcal M): available methods or intermediate reasoning procedures;
* (\mathcal E): independent discharge mechanisms.

RCI assumes none of the following unless supplied:

* probability;
* metric;
* total order;
* scalar utility;
* causality;
* temporal semantics;
* continuity;
* determinism;
* completeness.

---

# 5. Relations and succession

For carriers (X,Y):

[
R:X\rightsquigarrow Y
]

denotes:

[
R\subseteq X\times Y.
]

Relational composition is:

[
S\circ R
========

{(x,z):\exists y,\ xRy\land ySz}.
]

Every admissible transformation:

[
u\in\mathcal U
]

has relation:

[
R_u\subseteq X\times X.
]

A path:

[
\pi=(u_1,\dots,u_n)
]

has relation:

[
R_\pi
=====

R_{u_n}\circ\cdots\circ R_{u_1}.
]

For target region (T\subseteq X), define:

[
\Diamond_R(T)
=============

{x:R\cap T\neq\varnothing},
]

[
\Box_R(T)
=========

{x:R\subseteq T},
]

and:

[
\operatorname{Must}_R(T)
========================

\operatorname{Dom}(R)\cap\Box_R(T).
]

These distinguish:

* may reach;
* must reach;
* cannot reach;
* unknown reachability.

---

# 6. Protected consequence

Let:

[
\Phi:X\rightsquigarrow Z
]

denote the protected consequence profile.

For binary consequence:

[
C:X\to{0,1},
]

define:

[
C^+=C^{-1}(1),
\qquad
C^-=C^{-1}(0).
]

If inquiry begins with a problem predicate (P), then:

[
\boxed{
\neg P
}
]

is the first provisional opposite pole.

This does not imply that every member of (\neg P) is an acceptable solution.

Additional protected consequences may further constrain acceptable resolution.

---

# 7. Consequence equivalence

Two states are consequence-equivalent relative to protected horizon (\mathcal H) iff:

[
\boxed{
x\equiv_{\mathcal H}y
\iff
\forall h\in\mathcal H,\quad
J_h[x]=J_h[y].
}
]

Thus:

[
x\neq y
]

does not entail:

[
x\not\equiv_{\mathcal H}y.
]

The protected quotient is:

[
\boxed{
X/{\equiv_{\mathcal H}}.
}
]

When a new protected continuation separates two previously folded states, the quotient must refine.

---

# 8. Questions as semantic deformation

RCI 0.1 treated questions principally as typed claim constructors.

RCI 0.2 adds an equally important function:

[
\boxed{
q
:
\text{persistent semantic state}
\to
\text{temporary consequential semantic field}.
}
]

A question determines not only what role an answer plays, but what should become locally relevant while answering.

---

# 9. Active consequential field

Given state (\Sigma_t), question (q), and horizon (\mathcal H_t), define:

[
\boxed{
A_t(q)
======

{
x\in\Sigma_t:
x
\text{ can alter}
;
\begin{array}{l}
\text{a candidate completion of }q,\
\text{the applicability of }q,\
\text{interpretation of its answer},\
\text{warrant of its answer},\
\text{or a protected downstream consequence}
\end{array}
}.
}
]

Define temporarily occluded structure:

[
\boxed{
O_t(q)
======

\Sigma_t\setminus A_t(q).
}
]

Occlusion is not deletion.

For any consequentially suppressible object (x), retain a reopening predicate:

[
\boxed{
\rho_x(\Sigma,q,\mathcal H).
}
]

If:

[
\rho_x=1,
]

then (x) must re-enter the active field.

---

# 10. Question-conditioned context

The semantic generator should receive approximately:

[
\boxed{
Context(q,\Sigma)
=================

A_t(q)
\cup
Retrieve_{\mathrm{rel}}(q,\Sigma)
\cup
Methods(q)
\cup
ReopenEdges(q,\Sigma).
}
]

Where:

### (A_t(q))

contains already known locally consequential structure.

### (Retrieve_{\mathrm{rel}})

retrieves semantically distant material that is structurally adjacent under the current relation.

### (Methods(q))

makes applicable formal or domain-native methods locally available.

### `ReopenEdges`

preserves information about what is currently hidden and what would make it relevant again.

The context window therefore becomes part of the reasoning architecture.

---

# 11. Question-conditioned quotient

Define:

[
x\sim_q y
]

iff distinguishing (x) from (y) cannot change:

1. applicability of (q);
2. a candidate answer to (q);
3. interpretation of the answer;
4. warrant of the answer;
5. any currently protected downstream consequence.

Then:

[
\boxed{
\Sigma/{\sim_q}
}
]

is the question-relative working representation.

Different questions induce different quotients:

[
\Sigma/{\sim_q}
\neq
\Sigma/{\sim_{q'}}.
]

There is therefore no single globally optimal context compression.

Contextual compression is relational and question-conditioned.

---

# 12. Distinction geometry

A distinction is triadic.

For:

[
d:X\to D
]

and:

[
d(x)\neq d(y),
]

the elementary form is:

[
\boxed{
(x,d,y).
}
]

Two relata are distinguished under one common relation.

Introduce another binary distinction (D).

Then:

[
\langle C,D\rangle:X\to{0,1}^2.
]

Its actual image is:

[
\boxed{
T_{C,D}
=======

\operatorname{im}\langle C,D\rangle.
}
]

The logical cells are:

[
C\land D,
\quad
C\land\neg D,
\quad
\neg C\land D,
\quad
\neg C\land\neg D.
]

Not all need be realizable.

The off-diagonal cells are especially important:

[
C\land\neg D
]

attacks necessity.

[
D\land\neg C
]

attacks sufficiency.

Thus:

[
\boxed{
\text{triad}
\to
\text{second distinction}
\to
\text{tetradic probe}
\to
\text{residual}
\to
\text{new triad}.
}
]

---

# 13. Arrangement and succession

Inquiry separates two coordinates.

## Arrangement

What differs among realizations?

For reference (r), let:

[
\preceq_A^r
]

be an arrangement-preservation preorder.

## Succession

What differs among paths or transformations?

Let:

[
\preceq_S
]

be a succession preorder when supplied.

Arrangement and succession may interact, but neither should be silently reduced to the other.

---

# 14. Stretch

Hold consequence fixed and maximize relevant variation.

For active distinction set (B):

[
\Delta_B(x,y)
=============

{p\in B:p(x)\neq p(y)}.
]

Then:

[
\boxed{
\operatorname{Stretch}_B(x)
===========================

\operatorname{Max}_{\subseteq}
{
\Delta_B(x,y):
C(y)=C(x)
}.
}
]

Operationally:

> What can change while this consequence remains the same?

Then:

> Can more change?

Then:

> What survives only because the variation has not yet challenged it?

Generation should prefer:

* structural diversity;
* mechanistic diversity;
* extreme anchors;
* direct attacks on current explanations.

Thus:

[
\boxed{
\textbf{generate for separation, not plausibility.}
}
]

---

# 15. Squeeze

Hold as much fixed as possible while changing consequence.

[
\boxed{
\operatorname{Squeeze}_B(x)
===========================

\operatorname{Min}_{\subseteq}
{
\Delta_B(x,y):
C(y)\neq C(x)
}.
}
]

More generally:

[
\operatorname{Cross}_{C,\rho}(x,b)
==================================

\operatorname{Front}*{\preceq*\rho^x}
{
y:
C(y)=b
\land
\operatorname{Adm}_\rho(x,y)
}.
]

Operationally:

> What is the least change that makes the consequence different?

From both poles:

[
C^+\to C^-,
]

[
C^-\to C^+.
]

---

# 16. Boundary learning

Stretch and squeeze jointly induce an adaptive consequence geometry:

[
\boxed{
\text{maximize distance inside consequence-equivalence;}
}
]

[
\boxed{
\text{minimize distance across consequence boundaries.}
}
]

No universal scalar distance is required.

Only local partial orders or nondominated frontiers are needed.

Repeated inquiry reorganizes representation around consequence-bearing structure rather than lexical similarity.

---

# 17. Factor discovery

Let:

[
h:X\to H
]

be a candidate representation.

Define:

[
\boxed{
FD_\Phi(h)
==========

{
(x,y):
h(x)=h(y)
\land
\Phi(x)\neq\Phi(y)
}.
}
]

If:

[
FD_\Phi(h)=\varnothing,
]

then:

[
\Phi=d\circ h
]

for some (d) on the declared scope.

Representations are ordered by factorization:

[
\boxed{
h_1\preceq h_2
\iff
\exists m,\ h_1=m\circ h_2.
}
]

RCI seeks the coarsest or nondominated noncircular representation sufficient for currently protected consequence.

---

# 18. Mandatory falsification

Every proposed necessity produces:

[
\boxed{
C\land\neg N;?
}
]

Every proposed sufficiency produces:

[
\boxed{
N\land\neg C;?
}
]

Every proposed prerequisite (P) for target (T) produces:

[
\boxed{
Reach_{\neg P}(x)\cap T;?
}
]

Thus:

[
\boxed{
\textbf{every “must” generates a without-it attack;}
}
]

[
\boxed{
\textbf{every “enough” generates an it-without-result attack;}
}
]

[
\boxed{
\textbf{every prerequisite generates an alternate-route attack.}
}
]

---

# 19. Questions create relational addressability

Suppose the system asks for a mechanism.

The model answers semantic payload (a).

RCI does not immediately assert:

[
Mechanism(a).
]

Instead:

[
\boxed{
c
=

Claim_{\text{Mechanism}}(a).
}
]

The question makes (a) relationally addressable.

The controller now knows what may lawfully happen next.

For example:

* test whether consequence occurs without (a);
* test whether (a) occurs without consequence;
* seek prerequisites for (a);
* retrieve evidence relevant to (a);
* choose a native method capable of constraining (a);
* detect conflict with another mechanism claim;
* attempt actualization;
* restrict its scope;
* or discard it as irrelevant.

Hence:

[
\boxed{
\textbf{a question does not make content true;
it makes content lawfully addressable.}
}
]

---

# 20. Claim type

Define:

[
\boxed{
Claim[\tau].
}
]

A claim contains:

[
\boxed{
c=
(
id,
role,
args,
payload,
scope,
provenance,
status,
parents,
level
).
}
]

Recommended statuses:

[
{
proposed,
contested,
reified,
supported,
warranted,
refuted,
inactive,
unknown
}.
]

Question role does not imply truth.

---

# 21. Lazy semantic formalization

Claims may remain progressively structured.

### L0 — Opaque claim

Only:

* question role;
* bound referents;
* payload;
* provenance.

### L1 — Relational slots

Extract:

* relevant entities;
* polarity;
* candidate relation;
* scope;
* condition;
* path;
* transformation.

### L2 — Formal candidate

Convert to:

* predicate;
* formula;
* constraint;
* relation;
* transition;
* path;
* guard.

### L3 — Warranted object

Independent warrant licenses hard retention.

Thus:

[
\boxed{
L_0\to L_1\to L_2\to L_3
}
]

only when consequentially useful.

RCI specifically rejects the requirement that every natural-language answer be perfectly parsed into logic before it can participate in inquiry.

---

# 22. Candidate store

Let:

[
\boxed{
\mathcal C_t
}
]

be the candidate claim graph.

It may contain contradiction.

If:

[
P\in\mathcal C_t
]

and:

[
\neg P\in\mathcal C_t,
]

the system derives:

[
\boxed{
Conflict(P,\neg P)
}
]

not arbitrary (Q).

Candidate reasoning therefore requires a non-explosive treatment of inconsistency.

Conflict becomes an obligation.

---

# 23. Contradiction as inquiry

A conflict:

[
Conflict(c_i,c_j)
]

generates:

[
ResolveConflict(c_i,c_j).
]

Natural-language probes include:

> Can both claims hold here?

> If not, which one fails?

> Are they operating over different scopes?

> Did a term change meaning?

> Is one missing a guard?

> What smallest distinction makes them compatible?

> Can the contradiction still occur without that distinction?

Thus semantic error becomes material for further reasoning.

---

# 24. Description versus control

A descriptive factor:

[
\Phi=d\circ h
]

does not imply an actionable transformation.

Therefore:

[
\boxed{
\text{description}
\neq
\text{control}.
}
]

A control certificate from source (S) to target (T) requires:

[
\boxed{
S\subseteq\operatorname{MustPre}_\pi(T)
}
]

or another explicitly declared success semantics.

Where control occurs over an abstraction, an abstraction-to-concrete refinement relation must preserve the relevant guarantee.

---

# 25. Actualization

Given present state (x) and target region (T):

[
\boxed{
\operatorname{Emb}(x,T)
=======================

\operatorname{Front}_{\preceq_A^x}(T).
}
]

Three broad outcomes exist.

## Arrangement obstruction

The desired relation cannot coexist with retained structure.

Generate conflict-localization and repair obligations.

## Succession obstruction

A compatible target exists, but no currently known path reaches it.

Regress through predecessor conditions.

## Reachable target

Retain the nondominated path frontier and independently test it.

---

# 26. Recursive prerequisite descent

If target (T) requires apparent predecessor condition (N):

> Can (T) still be reached while (N) remains absent?

If yes:

[
N
]

was route-specific.

If no, ask:

> What would establish (N)?

That answer becomes another target.

Thus every obstruction is itself turned into a consequence boundary.

---

# 27. Question frontier

RCI 0.1 assumed a controller selected the next question.

RCI 0.2 instead defines:

[
\boxed{
\mathcal Q_t
============

LawfulQuestions(\Sigma_t,O_t,\mathcal H_t).
}
]

This is the **lawful question frontier**.

A question belongs to (\mathcal Q_t) iff:

1. its referents are well-typed;
2. its possible returns can differ consequentially;
3. at least one return can alter a protected conclusion, obligation, factorization, boundary, warrant, compression, or reopening state;
4. downstream consumers exist or can be lawfully generated.

The controller may select from this frontier.

The semantic model may also propose a new question not currently enumerated.

---

# 28. Dynamic question generation

Let semantic model propose:

[
q^\star.
]

The controller accepts it only if a valid contract can be inferred:

[
\boxed{
\mathcal Q^\star
================

(
\tau_{in},
\tau_{claim},
Pre,
Bind,
Consumers,
Counterconditions
).
}
]

A generated question need not belong to a closed universal library.

The library is extensible so long as new questions can be grounded in lawful relational composition.

Therefore:

[
\boxed{
\text{formal controller constrains;}
\qquad
\text{semantic model navigates.}
}
]

---

# 29. Primitive question kernel

The universal question basis should remain small.

## Variation

> What can change while this consequence remains the same?

## Boundary

> What is the least change that makes the consequence different?

## Necessity attack

> Can the consequence still occur without this?

## Sufficiency attack

> Can this still occur while the consequence fails?

## Actualization

> What would have to be true for this relation to hold here?

## Alternate route

> Can the target be reached without that?

## Warrant

> What independently constrains this claim?

## Generalization

> What broader relation follows for the same reason?

## Compression

> What distinction can now be ignored?

## Reopening

> What would make that distinction matter again?

## Recursion

> What consequential difference remains?

These questions form the regenerative kernel.

---

# 30. Derived question contracts

Domain-specific and method-specific questions are derived compositions.

For example:

[
Q_{\mathrm{effect}}
:
(Function,FailureMode)
\rightsquigarrow
Claim[Effect]
]

may be generated under a failure-analysis binding.

A statistical method might provide:

[
Q_{\mathrm{factor-response}}
:
(Factors,Response,Domain)
\rightsquigarrow
Claim[EffectStructure].
]

A software debugger might provide:

[
Q_{\mathrm{minimal-reproducer}}
:
(Failure,Environment)
\rightsquigarrow
Claim[BoundaryWitness].
]

These are not universal RCI primitives.

They are compiled domain realizations.

---

# 31. Method repertoire

RCI 0.2 distinguishes:

[
\boxed{
\mathcal M
}
]

from:

[
\boxed{
\mathcal E.
}
]

### (\mathcal M): Method repertoire

Methods may themselves generate structured subquestions, analyses, comparisons, and intermediate objects.

Examples include:

* failure analysis;
* optimization;
* causal modeling;
* statistical design;
* theorem-proving strategy;
* debugging method;
* hazard analysis;
* control analysis;
* architecture analysis;
* literature synthesis.

### (\mathcal E): Discharge mechanisms

These return independently constraining evidence:

* solver result;
* proof;
* execution;
* observation;
* measurement;
* experiment;
* retrieval;
* human answer;
* external system return.

A method need not independently warrant its own conclusions.

It may only organize inquiry.

---

# 32. Method adapter

A method adapter is:

[
\boxed{
M=
(
id,
Applicability,
Inputs,
QuestionGenerators,
IntermediateRoles,
DischargeOptions
).
}
]

Implementation form:

```text
MethodAdapter {
    id
    applicability_relation
    input_claim_roles[]
    generated_question_contracts[]
    possible_intermediate_roles[]
    compatible_discharge_adapters[]
}
```

Questions can therefore make a method locally adjacent even when the method comes from a semantically distant domain.

---

# 33. Relational retrieval

The model should not retrieve context solely by lexical similarity.

Given question (q), retrieval should prefer:

[
\boxed{
\text{structural correspondence under the relation exposed by }q.
}
]

A semantically distant case may be locally relevant if it instantiates:

* the same failure geometry;
* the same boundary pattern;
* the same prerequisite structure;
* the same control relation;
* the same conflict;
* the same transformation topology.

Thus:

[
d_{\mathrm{lexical}}(x,q)
]

may be large while:

[
d_{\mathrm{relational}\mid q}(x,q)
]

is small.

---

# 34. Question contract

Every persistent question family is represented as:

[
\boxed{
\mathcal Q
==========

(
id,
\tau_{in},
\tau_{claim},
Pre,
Render,
Bind,
Field,
Reify,
Check,
Update,
Next
).
}
]

RCI 0.2 adds:

[
\boxed{
Field
}
]

to the contract.

`Field` determines how the question constructs or requests its active semantic field.

---

# 35. Binding law

Given answer payload (a):

[
\boxed{
Bind_Q(a)
=========

Claim_Q(a).
}
]

This asserts:

> (a) was offered as an answer playing role (\tau_Q).

It does not assert:

[
a:\tau_Q
]

as fact.

This is intentionally shallow.

---

# 36. Reification law

[
\boxed{
Reify_\tau:
Claim[\tau]
\rightharpoonup
Candidate[\tau].
}
]

Reification is partial.

Failure creates a new inquiry obligation rather than invalidating the protocol.

---

# 37. Promotion law

[
\boxed{
Promote(c,\pi)=\lambda
}
]

only when:

[
Check(\pi)=\top.
]

The model cannot promote its own answer merely by repeating or elaborating it.

---

# 38. Warrant interface

Every backend (e\in\mathcal E) should support:

[
Encode_e:O\to Query_e,
]

[
Run_e:Query_e\to Return_e,
]

[
Decode_e:Return_e\to Result,
]

[
Check_e:Result\to WarrantStatus.
]

A hard relation enters (\Theta) only under a policy-authorized warrant class.

---

# 39. Warrant classes

Suggested classes:

* formal proof;
* checked certificate;
* exhaustive computation;
* reproducible execution;
* authenticated measurement;
* controlled experiment;
* trusted external source;
* corroborated evidence;
* heuristic support;
* model-generated hypothesis.

Different deployments may assign different promotion policies.

---

# 40. Generalization

Given warranted return (r):

[
\boxed{
Gen(r)
}
]

returns a nondominated set of reusable conditional relations.

Generalization itself remains attackable.

One failed instance should become a generalized cut only as far as warrant permits.

Potential implementations include:

* conflict analysis;
* interpolation;
* inductive generalization;
* minimal conflict;
* minimal support;
* theory-specific explanation.

---

# 41. Adaptive abstraction

Let:

[
B_t={p_1,\dots,p_n}
]

be current distinctions.

Define:

[
\boxed{
\alpha_t(x)
===========

(p_1(x),\dots,p_n(x)).
}
]

The realized abstract carrier is:

[
\boxed{
V_t
===

\operatorname{im}\alpha_t.
}
]

No unrealized Cartesian combination is automatically treated as actual.

---

# 42. Abstraction law

Extend:

[
\alpha_t^\sharp(S)
==================

{\alpha_t(x):x\in S}.
]

Define:

[
\gamma_t(A)
===========

{x:\alpha_t(x)\in A}.
]

Where exact realized abstraction is intended:

[
\boxed{
\alpha_t^\sharp(S)\subseteq A
\iff
S\subseteq\gamma_t(A).
}
]

---

# 43. Refinement

If:

[
\alpha(x)=\alpha(y)
]

but:

[
\Phi(x)\neq\Phi(y),
]

the abstraction contains a false equivalence.

Find:

[
p(x)\neq p(y)
]

and refine:

[
B_{t+1}=B_t\cup{p}.
]

Require forgetting map:

[
\boxed{
\rho_{t+1,t}:V_{t+1}\to V_t
}
]

such that:

[
\boxed{
\alpha_t
========

\rho_{t+1,t}\circ\alpha_{t+1}.
}
]

---

# 44. Compression

A quotient:

[
q:V_t\to V'
]

is admissible only if every protected consequence factors through it:

[
\boxed{
\widehat\Phi_t
==============

\Phi'\circ q.
}
]

If protected transition or control behavior matters, those relations must factor as well.

Therefore:

[
\boxed{
\text{split when protected consequence distinguishes;}
}
]

[
\boxed{
\text{merge when protected consequence permits.}
}
]

---

# 45. Question-conditioned compression

Persistent abstraction and temporary question-relative compression are distinct.

Persistent abstraction asks:

> Which distinctions need to remain represented in the system at all?

Question-conditioned compression asks:

> Which represented distinctions matter for this question right now?

Thus:

[
\boxed{
\alpha_t
}
]

and:

[
\boxed{
\sim_q
}
]

must remain separate.

A distinction may remain persistent but be temporarily occluded.

---

# 46. Reopening edge

Define:

```text
ReopeningEdge {
    object_id
    suppression_context
    trigger
    protected_consequences[]
    rationale
}
```

A reopening edge records why a distinction was safely hidden and what would invalidate that hiding.

This allows aggressive local context compression without epistemic deletion.

---

# 47. Full runtime state

RCI 0.2 maintains:

[
\boxed{
\Sigma_t=
(
\mathfrak B,
\gamma_t,
\Phi_t,
B_t,
\alpha_t,
\widehat R_t,
\mathcal C_t,
\Theta_t,
\mathcal O_t,
W_t,
\mathcal Q_t,
\mathcal F_t,
M_t
).
}
]

Where:

* (\mathfrak B): binding;
* (\gamma_t): context;
* (\Phi_t): protected consequence;
* (B_t): persistent distinction basis;
* (\alpha_t): persistent abstraction;
* (\widehat R_t): abstract succession;
* (\mathcal C_t): candidate claim graph;
* (\Theta_t): guarded warranted theory;
* (\mathcal O_t): obligations;
* (W_t): warrant DAG;
* (\mathcal Q_t): lawful question frontier;
* (\mathcal F_t): current question-conditioned semantic field;
* (M_t): active inquiry mode.

---

# 48. Semantic field object

```text
SemanticField {
    question_id
    active_claim_ids[]
    active_lemma_ids[]
    active_object_ids[]
    active_obligation_ids[]
    retrieved_relational_analogues[]
    applicable_method_ids[]
    suppressed_object_ids[]
    reopening_edges[]
}
```

This object defines what the semantic model sees.

---

# 49. Question frontier object

```text
QuestionFrontier {
    obligation_id
    contract_candidates[]
    dynamically_proposed_questions[]
    dominance_relations[]
    rejected_questions[]
}
```

A dynamic question may enter the frontier only after its relational contract is accepted.

---

# 50. Inquiry obligation

Canonical obligation kinds include:

[
Establish(C),
]

[
Eliminate(C),
]

[
Distinguish(x,y),
]

[
TestNec(N,C),
]

[
TestSuff(S,C),
]

[
CrossBoundary(x,C),
]

[
ResolveConflict(K),
]

[
EstablishPrereq(N),
]

[
TestPrereq(N,T),
]

[
LocalizeFailure(F),
]

[
RefineAbstraction(x,y),
]

[
Reify(c),
]

[
ValidateWarrant(c),
]

[
Reopen(x,\rho_x),
]

[
GenerateQuestion(O).
]

---

# 51. Inquiry modes

The principal modes are:

[
\mathsf V
=========

Variation,
]

[
\mathsf B
=========

Boundary,
]

[
\mathsf F
=========

Falsification,
]

[
\mathsf A
=========

Actualization,
]

[
\mathsf W
=========

Warrant,
]

[
\mathsf C
=========

Compression.
]

A useful recurring rhythm is:

[
\boxed{
\mathsf V
\to
\mathsf B
\to
\mathsf F
\to
\mathsf A
\to
\mathsf W
\to
\mathsf C
\to
\mathsf V.
}
]

But runtime control is event-driven rather than mechanically periodic.

---

# 52. Complete RCI 0.2 process

```text
RATCHETING CONSEQUENCE INQUIRY 0.2

INPUT
    binding
    current context
    protected consequences
    initial obligation
    semantic generator
    method repertoire
    discharge mechanisms

STATE
    candidate claim graph
    warranted conditional theory
    persistent distinction basis
    abstraction
    transition structure
    obligations
    warrant DAG
    lawful question frontier
    semantic field
    inquiry mode

LOOP

1. SELECT CONSEQUENTIAL OBLIGATION

   What unresolved difference can still change a protected consequence,
   warranted conclusion, action, representation, or next obligation?

2. GENERATE LAWFUL QUESTION FRONTIER

   Determine question contracts whose inputs are available and whose
   possible answers would produce consequentially distinct downstream states.

   Permit the semantic model to propose additional questions.

   Admit a proposed question only if its relational role, referents,
   possible claims, and downstream attack surfaces can be made lawful.

3. SELECT QUESTION

   Choose a nondominated question according to available criteria.

   Prefer questions that:
       separate consequential alternatives;
       expose reusable boundaries;
       have strong independent discharge;
       avoid unnecessary assumptions;
       are reversible or cheap where otherwise equivalent.

4. CONSTRUCT QUESTION-CONDITIONED SEMANTIC FIELD

   Activate:
       locally consequential claims;
       relevant warranted lemmas;
       relationally analogous material;
       applicable methods;
       relevant reopening conditions.

   Occlude distinctions whose variation cannot affect the question or
   protected downstream consequence.

5. RENDER QUESTION

   Express the selected relation in ordinary domain-appropriate language.

6. GENERATE SEMANTIC PAYLOAD

   Let the semantic model answer.

7. BIND

   Store:
       Claim(question_role, bound_referents, answer_payload).

   Do not assert truth.

8. COMPOSE

   Relate the new claim to existing claims according to question roles.

   Detect:
       support,
       contradiction,
       counterexample,
       candidate boundary,
       candidate prerequisite,
       candidate equivalence,
       target,
       abstraction defect,
       reification need,
       warrant need.

9. STRETCH WHERE NECESSARY

   For any explanation or candidate invariant:
       generate same-consequence cases maximally disagreeing with it.

10. SQUEEZE WHERE NECESSARY

    Seek minimally different opposite-consequence cases from both poles.

11. ATTACK

    For every proposed necessity:
        seek consequence without it.

    For every proposed sufficiency:
        seek it without consequence.

    For every prerequisite:
        seek target without it.

12. REIFY LAZILY

    Formalize only claims whose deeper structure is needed by a consequential operation.

    If reification fails:
        generate decomposition, clarification, alternate-expression, or unknown obligation.

13. SELECT METHOD

    Use the active question relation to make relevant domain-native methods adjacent.

    A method may generate additional lawful subquestions before independent discharge.

14. DISCHARGE

    Obtain external or formal return where necessary.

15. LOCALIZE

    On contradiction:
        locate smallest scope, guard, meaning, or false-claim distinction.

    On failure:
        localize arrangement, succession, or interaction residual.

    On success:
        subtract unnecessary support.

16. GENERALIZE

    Find the broadest nondominated reusable relation warranted by the return.

17. PROMOTE

    Add only adequately warranted relations to the guarded theory.

18. REFINE

    Split any persistent abstraction that merges protected-consequence-distinct states.

19. COMPRESS

    Persistently merge distinctions no protected future can inspect.

    Temporarily occlude distinctions irrelevant to the next question.

    Preserve reopening conditions.

20. PROGRESS TEST

    Retain the step only if it:
        adds warrant;
        eliminates possibility;
        removes false equivalence;
        establishes useful equivalence;
        localizes boundary;
        falsifies necessity/sufficiency;
        resolves prerequisite;
        identifies obstruction;
        changes control;
        changes representation;
        changes next obligation;
        or establishes reopening conditions.

21. RE-CENTER

    What consequential residual now deserves to become the center of the semantic field?

22. RECUR

STOP WHEN
    the obligation is warranted satisfied;
    warranted impossible under the binding;
    all live alternatives are consequence-equivalent;
    or no available question, method, observation, or formal backend can
    discriminate the remaining alternatives.

RETURN UNKNOWN rather than inventing a distinction that cannot be made.
```

---

# 53. Full recursive question rhythm

A domain-neutral runtime may repeatedly use:

> What is unresolved?

> What consequence makes the live alternatives different?

> What can vary radically while that consequence stays the same?

> What very different mechanism preserves the same consequence?

> What is the smallest change that flips the consequence?

> What is the smallest change that flips it back?

> What relation survives those comparisons?

> Can the consequence still hold without that relation?

> Can that relation hold while the consequence fails?

> What smaller relation survives both attacks?

> What would have to be true for that relation to hold here?

> Can that requirement be avoided?

> What method is naturally suited to constraining this relation?

> What independent return can tell us which way it goes?

> What did that return actually establish?

> What broader relation is supported for the same reason?

> What would falsify that generalization?

> What distinction can now be hidden?

> What would make it matter again?

> What consequential residual should become the center of the next inquiry?

Then repeat.

---

# 54. Question composition

Questions compose when the output claim role of one supplies a lawful input role to another.

For example:

[
Q_{Factor}
:
C
\rightsquigarrow
Claim[Factor].
]

Then:

[
Q_{NecAttack}
:
(C,Claim[Factor])
\rightsquigarrow
Claim[Counterexample].
]

Then:

[
Q_{Residual}
:
(Counterexample,Factor)
\rightsquigarrow
Claim[Separator].
]

Then:

[
Q_{Actualize}
:
(Separator,x)
\rightsquigarrow
Claim[Prerequisite].
]

Question sequencing is therefore a typed program over provisional semantic objects.

---

# 55. Deictic binding

Surface language may remain simple:

> What differs?

> Can it still work without that?

> What would make that hold here?

> Can that be avoided?

The controller binds:

* `this`;
* `that`;
* `what changed`;
* `the result`;
* `the requirement`;

to explicit claim or object IDs.

Natural conversational deixis is therefore a surface syntax over typed references.

---

# 56. Question scheduling

Define:

[
q_i\prec q_j
]

when the answer to (q_i) can change:

* the referent of (q_j);
* applicability of (q_j);
* meaning of possible answers;
* or downstream consequence.

Then:

[
\boxed{
\textbf{sequence dependencies;}
}
]

[
\boxed{
\textbf{batch antichains.}
}
]

Questions believed independent may be permuted.

If order changes the protected conclusion, generate an inquiry:

> Is this genuine relational interaction or irrelevant context-order dependence?

---

# 57. Lawfulness conditions

A conforming RCI implementation must preserve the following.

## L1 — Claim/fact separation

[
Claim[\tau]
\not\Rightarrow
Warranted[\tau].
]

## L2 — Candidate non-explosion

Candidate contradiction creates conflict, not arbitrary inference.

## L3 — Consequence-sound compression

No persistent merge may identify states distinguishable by a protected consequence.

## L4 — Question-relative occlusion

Temporary hiding may not remove structure capable of changing the current question, its warrant, or protected successor consequence.

## L5 — Reopening preservation

Any consequentially hidden persistent structure must retain a mechanism for re-entry.

## L6 — Conservative refinement

Persistent refinement must admit a lawful forgetting projection to the prior abstraction.

## L7 — Transition soundness

Relevant concrete transitions must remain represented abstractly.

## L8 — Description/control separation

No descriptive relation becomes a control guarantee without an implementation/refinement certificate.

## L9 — Hard-warrant soundness

Hard retained lemmas require policy-authorized independent warrant.

## L10 — Warrant acyclicity

Positive warrant may not depend on itself.

## L11 — Dynamic-question lawfulness

A generated question may enter the question frontier only when its relational role and downstream consumers can be specified.

## L12 — Unknown legality

Inability to distinguish does not itself imply equivalence.

---

# 58. Architectural layers

RCI 0.2 should be implemented as separable layers.

## Layer A — Persistent formal state

Maintains:

* claims;
* warrants;
* abstractions;
* obligations;
* transitions;
* reopening structure.

## Layer B — Obligation controller

Determines the consequential unresolved frontier.

## Layer C — Question frontier generator

Produces lawful candidate relational cuts.

May combine formal and semantic generation.

## Layer D — Semantic-field compiler

Determines what should be visible for this question.

## Layer E — Semantic generator

Produces candidate content.

## Layer F — Claim binder

Wraps content under the question role.

## Layer G — Lazy reifier

Formalizes only as needed.

## Layer H — Method selector

Maps relations to useful domain-native methods.

## Layer I — Discharge layer

Executes formal or environmental tests.

## Layer J — Warrant manager

Promotes only licensed returns.

## Layer K — Refinement/compression manager

Splits, merges, occludes, and reopens representation.

---

# 59. Main implementation objects

### InquiryState

```text
InquiryState {
    binding
    context
    protected_consequences
    persistent_predicate_basis
    abstraction
    transition_structure
    candidate_claim_graph
    warranted_lemma_store
    obligations
    warrant_graph
    question_frontier
    current_semantic_field
    current_mode
}
```

### Claim

```text
Claim {
    id
    role
    bound_referents[]
    payload
    scope
    provenance
    status
    formalization_level
    parents[]
    conflicts[]
}
```

### QuestionContract

```text
QuestionContract {
    id
    input_roles[]
    output_claim_role
    precondition
    render
    bind
    semantic_field_policy
    reifier
    verifier
    update_rule
    next_obligation_rules[]
}
```

### SemanticField

```text
SemanticField {
    question_id
    active_claim_ids[]
    active_lemma_ids[]
    active_object_ids[]
    active_obligation_ids[]
    relational_retrievals[]
    available_methods[]
    suppressed_object_ids[]
    reopening_edges[]
}
```

### ReopeningEdge

```text
ReopeningEdge {
    object_id
    trigger
    suppression_scope
    reason
    protected_consequences[]
}
```

### MethodAdapter

```text
MethodAdapter {
    id
    applicability_relation
    input_roles[]
    generated_question_contracts[]
    possible_intermediate_roles[]
    compatible_discharge_adapters[]
}
```

### WarrantedLemma

```text
WarrantedLemma {
    id
    guard
    relation
    scope
    warrant_class
    dependencies[]
    certificate
    provenance
    source_claims[]
}
```

---

# 60. Established theoretical correspondences

RCI is a synthesis, not a renaming of one established algorithm.

Its major components correspond to established mathematical traditions.

### Relational semantics / Kleene algebra with tests

Provides compositional action and predicate structure.

### Predicate transformers / weakest-precondition reasoning

Provides backward actualization and predecessor propagation.

### Abstract interpretation

Provides sound abstraction/concretization and consequence-relative approximation.

### CEGAR

Provides separator-driven refinement when abstractions create spurious equivalences.

### Myhill–Nerode / (L^*)

Provides continuation-relative behavioral equivalence and counterexample-driven state refinement.

### Paige–Tarjan / bisimulation refinement

Provides coarsest relational partitioning for explicit systems.

### SAT / SMT / DPLL(T)

Provides modular satisfiability and theory-specific counterexample attacks.

### CDCL

Provides generalized conflict learning.

### PDR / IC3

Provides recursive predecessor obligations and inductive generalized cuts.

### Constrained Horn clauses

Provide a natural formal representation for recursively dependent obligations.

### Craig interpolation

Provides shared-vocabulary explanations of inconsistency.

### MUS / MCS / QuickXPlain

Provide conflict localization and minimal correction.

### ATMS / truth maintenance

Provides context-sensitive assumptions and conflict-localized candidate management.

### Feedback refinement / alternating simulation

Provides abstract-to-concrete control guarantees.

RCI adds the question-conditioned semantic-field layer and the typed untrusted-claim protocol across these mechanisms.

---

# 61. What is novel in RCI 0.2

The project-specific synthesis consists principally of:

### 1. Question-conditioned semantic deformation

Questions reorganize semantic accessibility rather than merely request answers.

### 2. Typed untrusted claims

The answer inherits relational role from the question but not truth.

### 3. Composable fallibility

Incorrect claims remain safely usable because their attack surfaces are known.

### 4. Universal stretch/squeeze geometry

Maximal diversity inside consequence classes and minimal deformation across consequence classes are used as the universal boundary-learning pressures.

### 5. Open question frontier

The question library is regenerative rather than closed.

### 6. Method adjacency

A question can make a domain-native method locally relevant even when the method is semantically distant under ordinary retrieval.

### 7. Question-relative quotienting

The active context is dynamically compressed differently for each question.

### 8. Reopening edges

Occluded structure retains conditions under which it becomes relevant again.

### 9. Externalized epistemic ratchet

Only warranted generalized relations persist as hard semantic deformation.

---

# 62. Development strategy

## Phase 1 — Claim protocol

Implement:

* QuestionContract;
* Claim;
* Obligation;
* claim graph;
* contradiction edges;
* recursive question sequencing.

No full semantic parser required.

## Phase 2 — Semantic field

Implement:

* active field;
* suppression;
* relational retrieval;
* reopening edges;
* question-relative context construction.

## Phase 3 — Dynamic question frontier

Implement:

* contract matching;
* semantic question proposals;
* dynamic question validation;
* dependency scheduling.

## Phase 4 — Warrant store

Implement:

* guards;
* scopes;
* provenance;
* warrant classes;
* promotion;
* deactivation.

## Phase 5 — Lazy formalization

Add:

* reifiers;
* predicates;
* SAT/SMT;
* necessity/sufficiency attack.

## Phase 6 — Abstraction/refinement

Add:

* persistent predicate abstraction;
* CEGAR-style separators;
* compression;
* conservative forgetting.

## Phase 7 — Recursive formal obligations

Add:

* CHCs;
* PDR/Spacer;
* predecessor reasoning.

## Phase 8 — Method repertoire

Add adapters for domain-native methods.

## Phase 9 — Control

Add:

* action semantics;
* control certificates;
* refinement relations.

---

# 63. Minimum viable behavioral demonstration

Before implementing every formal backend, a valid RCI 0.2 prototype should demonstrate:

1. an obligation creates a question frontier;
2. a question constructs a reduced semantic field;
3. an LLM answer becomes a typed provisional claim;
4. no semantic correctness is assumed;
5. another lawful question consumes that claim;
6. conflicting answers remain representable;
7. contradiction creates a repair obligation;
8. the question context changes according to the residual;
9. irrelevant information can be suppressed;
10. a reopening trigger can restore it;
11. an independently checked return can promote a guarded lemma;
12. the lemma changes subsequent inquiry;
13. the remaining residual becomes the next center.

That would establish the central architecture independently of full formal automation.

---

# 64. Core experimental hypotheses

RCI 0.2 predicts that reasoning quality should differ materially between:

### Static full-context prompting

All information and instructions always visible.

### Static typed questioning

Questions type claims but context does not deform.

### Question-conditioned context

Each question receives only its active consequential field.

### Question-conditioned context plus reopening

Occlusion becomes reversible rather than lossy.

### Question-conditioned context plus dynamic methods

Methods are retrieved structurally from the relation exposed by the current question.

The hypothesis is that the latter regimes should reduce:

* semantic drift;
* irrelevant continuation;
* instruction averaging;
* premature ontology;
* unsupported necessity;
* repeated rediscovery;

while improving:

* counterexample discovery;
* structural analogy;
* conflict localization;
* context efficiency;
* question relevance;
* long-horizon coherence.

---

# 65. Governing laws of RCI 0.2

## Consequence law

[
\boxed{
\textbf{Reason relative to protected consequence, not mere descriptive difference.}
}
]

## Question law

[
\boxed{
\textbf{A question makes semantic content relationally addressable; it does not make it true.}
}
]

## Semantic-field law

[
\boxed{
\textbf{Every consequential question may induce a different locally relevant semantic quotient.}
}
]

## Generation law

[
\boxed{
\textbf{Generate for discrimination, not plausibility.}
}
]

## Stretch law

[
\boxed{
\textbf{Within a consequence class, maximize useful variation.}
}
]

## Squeeze law

[
\boxed{
\textbf{Across consequence classes, minimize useful variation.}
}
]

## Falsification law

[
\boxed{
\textbf{Every necessity, sufficiency, and prerequisite generates its missing counterexample obligation.}
}
]

## Claim law

[
\boxed{
\textbf{Generated answers are claims, not facts.}
}
]

## Fallibility law

[
\boxed{
\textbf{The inquiry process must remain well-defined even when semantic payloads are wrong.}
}
]

## Contradiction law

[
\boxed{
\textbf{Contradiction creates a new distinction to resolve, not logical explosion.}
}
]

## Actualization law

[
\boxed{
\textbf{A descriptive boundary becomes a solution only through a warranted boundary-crossing succession.}
}
]

## Method law

[
\boxed{
\textbf{Use questions to retrieve methods by relational applicability, not merely domain vocabulary.}
}
]

## Warrant law

[
\boxed{
\textbf{Only independently licensed returns may create hard retained knowledge.}
}
]

## Compression law

[
\boxed{
\textbf{Keep no distinction more finely than protected consequence requires and no more coarsely than it permits.}
}
]

## Occlusion law

[
\boxed{
\textbf{Temporarily hide what cannot affect the current inquiry, but retain the conditions under which it becomes relevant again.}
}
]

## Reopening law

[
\boxed{
\textbf{A changed semantic horizon may reactivate distinctions without erasing their earlier warrant history.}
}
]

## Recursion law

[
\boxed{
\textbf{Every consequential residual becomes the center of the next semantic field.}
}
]

---

# 66. Minimal generative form

The full system compresses to:

[
\boxed{
\textbf{
POLARIZE
\to
DEFORM CONTEXT
\to
STRETCH
\leftrightarrow
SQUEEZE
\to
FALSIFY
\to
ACTUALIZE
\to
CONSTRAIN
\to
WARRANT
\to
FOLD
\to
RE-CENTER
\to
RECUR.
}
}
]

Or in questions:

[
\boxed{
\begin{aligned}
&\textbf{What consequence is live?}\
&\textbf{What needs to be visible to answer the next consequential question?}\
&\textbf{What can vary while the consequence stays fixed?}\
&\textbf{What smallest variation flips it?}\
&\textbf{Can the consequence survive without what appears necessary?}\
&\textbf{Can what appears sufficient survive without the consequence?}\
&\textbf{What would make the surviving relation hold here?}\
&\textbf{Can that prerequisite be avoided?}\
&\textbf{What method or independent return can constrain this?}\
&\textbf{What does the return actually warrant?}\
&\textbf{What can now be hidden or merged?}\
&\textbf{What would make it relevant again?}\
&\textbf{What residual now deserves to become the center?}
\end{aligned}
}
]

---

# 67. Final project definition

[
\boxed{
\begin{aligned}
\textbf{Ratcheting Consequence Inquiry 0.2 is a question-conditioned}\
\textbf{semantic and formal refinement architecture in which protected}\
\textbf{consequences determine what differences matter; questions establish}\
\textbf{the relational role and temporary semantic field of inquiry; semantic}\
\textbf{generators supply untrusted candidate content; lawful composition}\
\textbf{turns that content into addressable claims, conflicts, boundaries,}\
\textbf{prerequisites, and possible transformations; domain-native methods}\
\textbf{and independent returns constrain those claims; warrant determines}\
\textbf{which relations persist; abstraction and context are continuously}\
\textbf{split, merged, occluded, and reopened according to protected}\
\textbf{consequence; and every consequential residual reconstructs the}\
\textbf{semantic field for the next recursion.}
\end{aligned}
}
]

The central implementation criterion is:

[
\boxed{
\textbf{
THE FORMAL PROCESS MUST REMAIN LAWFUL EVEN WHEN THE SEMANTIC GENERATOR IS WRONG.
}
}
]

The central semantic criterion is:

[
\boxed{
\textbf{
THE QUESTION SHOULD MAKE THE NEXT USEFUL RELATIONS LOCALLY NATURAL
WITHOUT PRETENDING THEIR CONTENT IS ALREADY TRUE.
}
}
]

The central epistemic criterion is:

[
\boxed{
\textbf{
ONLY WARRANTED CONSEQUENTIAL DEFORMATION PERSISTS.
}
}
]

And the central recursive criterion is:

[
\boxed{
\textbf{
THE REMAINING CONSEQUENCE BOUNDARY BECOMES THE CENTER OF THE NEXT QUESTION-CONDITIONED WORLD.
}
}
]
