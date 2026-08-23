# Operator-First Reconstruction of the Invariant of Good Reasoning and RCI

## Exact notation, relation semantics, question calculus, and implementation propagation

**Status:** Reconstruction / proposed semantic rebind  
**Basis examined:** `THE_INVARIANT_OF_GOOD_REASONING_CANONICAL(3).md` and the live `AcidicSwords/ratcheting-consequence-inquiry` repository at the inspected `main` revision.  
**Purpose:** Determine the smallest exact operator-first structure from which the existing consequence, inquiry, question, perception, memory, compression, ratchet, and self-improvement machinery can be regenerated without erasing the project's verified epistemic and authority boundaries.

---

# 0. Executive conclusion

The current formalization contains the right invariant but gives its primitives in the wrong order.

It says that the central relation is consequential distinguishability under admissible future use, and it repeatedly relies on composition to define meaning, equivalence, compression, path sensitivity, continuation, perception, and self-application. Yet it introduces transformations only after carriers, distinctions, claims, questions, and live regions.

The stronger reconstruction is:

\[
\boxed{
\textbf{typed transformation}
\;\to\;
\textbf{composition}
\;\to\;
\textbf{open composition/context}
\;\to\;
\textbf{consequence}
\;\to\;
\textbf{contextual distinction/equivalence}
}
\]

followed by actuality and warrant:

\[
\boxed{
\textbf{represented composition}
\;\neq\;
\textbf{actualized interaction}
\;\neq\;
\textbf{raw return}
\;\neq\;
\textbf{interpretation}
\;\neq\;
\textbf{warrant}.
}
\]

From these, the remaining structures are derived.

A state is a fold of realized composition. It earns the name **state** only when the future operators protected by the binding descend to the fold.

A probe is an actualizable distinguishing operator/context.

A question is not a primitive linguistic species. A question is a typed relation with one or more argument positions left open.

A fully bound relation is a proposition that may be carried by a claim.

A candidate answer is a substitution into the open positions.

A question program is composition of such open relations, candidate substitutions, actualizations, returns, and continuations.

A learned question, learned probe, learned method, compiled composite, representation refinement, and project self-improvement are therefore instances of one general operation:

\[
\boxed{
\textbf{change the admitted compositional repertoire or its warranted equations.}
}
\]

The project should not collapse their **governance roles**. It should unify their **semantic form**.

The smallest useful presentation of the reasoner's current generative competence is:

\[
\boxed{
\mathsf{Pres}_t
=
\left\langle
\mathsf G_t
\mid
\mathsf E_t
\right\rangle,
}
\]

where:

- \(\mathsf G_t\) is the admitted typed operator/relation generator repertoire;
- \(\mathsf E_t\) is the warranted family of equations, inequations, applicability constraints, and composition laws governing those generators.

The freely generated well-typed term language is:

\[
\boxed{
\mathsf{Tm}_t
=
\operatorname{Free}(\mathsf G_t),
}
\]

and protected contextual equivalence gives the operative quotient:

\[
\boxed{
\mathfrak A_t(A,B)
=
\mathsf{Tm}_t(A,B)/{\equiv_{\mathcal H_t}}
}
\]

for each interface pair \(A,B\), with quotient composition defined only when contextual
equivalence is a congruence.

Generative reasoning takes place in the free compositional space.

Epistemic compression and identification take place in the quotient.

Actuality enters through externally constrained return.

Warrant governs which generated relations may acquire standing.

Self-improvement changes \(\mathsf{Pres}_t\) using the same calculus.

---

# 1. What the current formalization already gets right

The uploaded canonical document explicitly intends to be domain-agnostic, goal-agnostic, binding-relative, regenerative rather than encyclopedic, and requires every proposed primitive to earn its place by preserving some otherwise non-regenerable reasoning capability. Those constraints should remain constitutional.

The following current structures survive the rebind essentially unchanged:

1. protected future consequence rather than metaphysical identity;
2. exact contextual/consequence equivalence versus working nondistinction;
3. constructible versus realizable versus actual;
4. prediction versus return;
5. raw return versus interpretation;
6. interpretation versus warrant;
7. self-application versus self-validation;
8. positive warrant acyclicity;
9. scope, applicability, assumptions, and resources;
10. factorization as the exact criterion of safe semantic compression;
11. continuation compatibility as the stronger criterion required for executable retained state;
12. path residue when endpoint information is insufficient;
13. recovery, reconstruction, evaluation, and reacquisition as distinct;
14. preserve + strict gain + independent warrant as the successor ratchet;
15. native-method transport rather than domain identification;
16. explicit reopening conditions;
17. lawful `Unknown`, `Blocked`, resource exhaustion, and external stopping.

These are not artifacts of the current state-centric representation. They constrain lawful transformations.

What changes is the ontology beneath them.

---

# 2. Semantic strata: keep these levels distinct

A major source of notation drift in the current document is that symbols from several different semantic strata appear side by side. The revised calculus must make the strata explicit.

## 2.1 Stratum \(\mathbf{L_0}\): interfaces and represented operators

This is the object-language of things that can compose.

\[
A,B,C,\ldots \in \mathsf{Int}_{\mathbb B}.
\]

\[
f:A\to_{\mathbb B}B.
\]

At this level, \(f\) is represented transformation, not actuality and not a claim about actuality.

## 2.2 Stratum \(\mathbf{L_1}\): relation schemas over typed entities

A relation schema is:

\[
R\hookrightarrow X_1\times\cdots\times X_n.
\]

Its arguments may themselves be:

- interfaces;
- operators;
- contexts;
- consequences;
- returns;
- claims;
- warrants;
- representations;
- other relation schemas in a meta-binding.

A fully bound relation instance is a proposition.

A partially bound relation instance is a question.

## 2.3 Stratum \(\mathbf{L_2}\): actuality and returns

An actual attempt is:

\[
!_{\mathbb B}f\Downarrow r.
\]

The return \(r\) belongs to an environment-defined return type. It is not generated merely by satisfying a semantic relation.

## 2.4 Stratum \(\mathbf{L_3}\): interpretation and warrant

Claims, interpretations, evidence checks, and warrants concern the standing of propositions or candidate transformations.

They do not alter the raw return.

## 2.5 Stratum \(\mathbf{L_4}\): meta-reasoning

The reasoner's own:

- relation schemas;
- operator generators;
- question compiler;
- method repertoire;
- quotient/equivalence laws;
- implementation;

may themselves be represented in a meta-binding and become arguments of the same relation language.

No self-membership or untyped reflective universe is required.

Self-application is obtained by **reification into a higher binding**, while positive warrant remains acyclic.

---

# 3. The primitive operator calculus

## 3.1 Binding

Use:

\[
\boxed{\mathbb B}
\]

for a binding.

The blackboard-bold notation prevents collision with ordinary interfaces \(A,B,C\).

A binding supplies at least:

- a class or family of interfaces \(\mathsf{Int}_{\mathbb B}\);
- admitted primitive operator generators;
- lawful partial composition;
- consequence semantics for declared contexts;
- actualization channels where relevant;
- return types;
- validation/warrant mechanisms.

A binding may additionally supply probability, order, metric, topology, Boolean structure, vector spaces, causality, time, control, rewriting, or other native mathematics.

None is universal.

### Plain-language question generated by the notation

> What binding supplies the interfaces, operators, composition law, consequence semantics, actualization channels, and validation rules being used here?

This is a binding-characterization question.

---

## 3.2 Interfaces

\[
\boxed{
A\in\mathsf{Int}_{\mathbb B}.
}
\]

An interface has no required object-metaphysical interpretation.

Its universal role is compositional:

- it is a source or target of operators;
- it determines which compositions are well typed.

Two names refer to different interfaces exactly when the binding says they have different composition conditions or other protected consequences.

### What it is not

An interface is not:

- automatically a physical object;
- a stored state;
- a proposition;
- a return;
- a semantic claim.

### Generated question

> Which interface must this operator consume or produce for the desired composition to be well typed?

---

## 3.3 Primitive operator generators

For interfaces \(A,B\):

\[
\boxed{
\mathsf G_{\mathbb B}(A,B)
}
\]

is the currently admitted family of primitive operator generators from \(A\) to \(B\).

For:

\[
f\in\mathsf G_{\mathbb B}(A,B),
\]

write:

\[
\boxed{
f:A\to_{\mathbb B}B.
}
\]

The arrow says only that \(f\) has source interface \(A\), target interface \(B\), and is admitted by the binding.

It does **not** universally say that \(f\) is:

- deterministic;
- reversible;
- causal;
- temporal;
- executable;
- physical;
- a total function.

### Generated questions

> What admitted operator transforms interface \(A\) into interface \(B\)?

> What is the source interface of \(f\)?

> What is the target interface of \(f\)?

> Is \(f\) admitted in binding \(\mathbb B\)?

---

## 3.4 Identity

When the compositional regime supports identities:

\[
\boxed{
1_A:A\to A.
}
\]

It is characterized by:

\[
f\circ 1_A=f,
\qquad
1_B\circ f=f
\]

for every \(f:A\to B\).

Identity is the operator-theoretic version of “no consequential replacement at this interface.”

Do not assume identity if a specialized binding deliberately lacks a category-like structure; but the reference kernel should normally admit it because it makes typing and composition exact.

---

## 3.5 Composition

If:

\[
f:A\to B,
\qquad
g:B\to C,
\]

then the serial composite is:

\[
\boxed{
g\circ f:A\to C.
}
\]

Read:

> first \(f\), then \(g\).

Use one convention throughout the formalization. Do not mix the current document's semicolon ordering with ordinary mathematical composition unless an implementation adapter explicitly translates between them.

Associativity:

\[
\boxed{
h\circ(g\circ f)=(h\circ g)\circ f
}
\]

whenever all terms are well typed.

### What composition means

Composition is the basic way one transformation participates in a larger transformation.

It is the relation through which consequences become inspectable.

### Generated questions

> What is the composite of \(f\) followed by \(g\)?

> What continuation \(g\) after \(f\) produces the target composite \(h\)?

> What predecessor \(f\) before \(g\) produces \(h\)?

These three questions are not separate primitive question families. They are the three fibers of one relation:

\[
\operatorname{Comp}(f,g,h).
\]

---

## 3.6 Free typed term language

Define:

\[
\boxed{
\mathsf{Tm}_{\mathbb B}(A,B)
}
\]

as the well-typed terms generated by primitive operators and identities under lawful composition.

Inductively:

\[
1_A\in\mathsf{Tm}_{\mathbb B}(A,A),
\]

\[
f\in\mathsf G_{\mathbb B}(A,B)
\Rightarrow
f\in\mathsf{Tm}_{\mathbb B}(A,B),
\]

and:

\[
f\in\mathsf{Tm}_{\mathbb B}(A,B),
\quad
g\in\mathsf{Tm}_{\mathbb B}(B,C)
\Rightarrow
g\circ f\in\mathsf{Tm}_{\mathbb B}(A,C).
\]

This is the **generative space**.

The fact that a term is constructible does not establish that it is realizable, actual, useful, or warranted.

\[
\boxed{
\text{well-typed term}
\neq
\text{realizable operation}
\neq
\text{actualized operation}
\neq
\text{warranted claim}.
}
\]

---

## 3.7 Path and factorization

Reserve \(p\) for probes and \(q\) for quotient maps only where needed.

Use:

\[
\boxed{
\pi=(f_1,\ldots,f_n)
}
\]

for a factorization/path.

Its composite is:

\[
\boxed{
\operatorname{Comp}(\pi)
=
f_n\circ\cdots\circ f_1.
}
\]

Two paths may have the same composite under one semantics yet differ under a richer protected horizon.

A path therefore records **factorization**, not merely endpoint.

### Generated questions

> Which factorization realizes this composite?

> Which path difference changes a protected future consequence?

> Can this factorization be occluded while preserving every protected continuation?

---

# 4. Open composition and context

## 4.1 One-hole context

Use:

\[
\boxed{
K[-]
}
\]

for a typed one-hole context.

Do not use \(C[-]\) because \(C\) is valuable as an ordinary interface symbol.

If the hole accepts an operator of type \(A\to B\) and the completed term has type \(U\to V\), write:

\[
\boxed{
K[-]:(A\to B)\Longrightarrow(U\to V).
}
\]

For:

\[
f:A\to B,
\]

the completed composition is:

\[
K[f]:U\to V.
\]

A context may represent precomposition, postcomposition, or a larger admitted composition pattern.

## 4.2 Why context is indispensable

Without context, two operators can be syntactically different without the difference mattering.

The context is what exposes whether their difference propagates to a protected consequence.

Therefore context connects:

- composition;
- consequence;
- distinction;
- equivalence;
- question generation;
- compression;
- reopening.

### Generated questions

> In which context would the difference between \(f\) and \(g\) become consequential?

> What operator can lawfully fill this context?

> Which completions of this context remain equivalent?

---

# 5. Consequence and protected horizon

## 5.1 Consequence

For a completed context \(K[f]\), define:

\[
\boxed{
\operatorname{Con}_{K}(f)\in Y_K
}
\]

as the binding-native semantic consequence exposed by the context.

The codomain \(Y_K\) belongs to the binding.

It may be:

- a truth value;
- a symbolic object;
- a set;
- a trace;
- a probability law;
- a resource vector;
- a reachability class;
- another relation.

A consequence is semantic.

It is not automatically an actual return.

\[
\boxed{
\operatorname{Con}_{K}(f)
\neq
r
}
\]

unless a binding establishes that relation for the particular actualization.

---

## 5.2 Protected future horizon

\[
\boxed{
\mathcal H
\subseteq
\mathsf{Ctx}_{\mathbb B}
}
\]

is the family of future contexts whose consequences are protected for the current inquiry.

The horizon determines which differences the reasoner is currently forbidden to erase.

The horizon is not:

- the set of everything imaginable;
- a goal;
- a probability distribution;
- the current tested discriminator set.

### Generated question

> Which future contexts are protected strongly enough that their ability to distinguish these operators must survive compression?

---

## 5.3 Parallelism

Before comparing operators extensionally, require:

\[
\boxed{
f\parallel g
}
\]

meaning:

\[
src(f)=src(g),
\qquad
tgt(f)=tgt(g).
\]

This condition was implicit in much of the previous formalization and should become explicit.

A difference between nonparallel operators first requires a bridge, retyping, or common comparison context.

### Generated question

> Under what common interface or bridge do these two operators become comparable?

This is the exact version of “a difference requires a shared frame.”

---

## 5.4 Exact protected contextual equivalence

For parallel operators:

\[
\boxed{
f\equiv_{\mathcal H}g
\iff
\forall K\in\mathcal H,
\quad
\operatorname{Con}_{K}(f)
=
\operatorname{Con}_{K}(g).
}
\]

This replaces the current state-centric \(x\equiv_{\mathcal H}y\) as the universal form.

State, history, configuration, claims, representations, and even relation schemas can still be compared by first representing them as terms in an appropriate binding.

### Plain language

> \(f\) and \(g\) are the same for the protected future exactly when every protected context gives the same consequence after either is inserted.

### What it is not

It is not:

- syntactic identity;
- metaphysical identity;
- current failure to distinguish;
- approximate similarity;
- equality outside the declared horizon.

---

## 5.5 Separator family

\[
\boxed{
\operatorname{Sep}_{\mathcal H}(f,g)
=
\left\{
K\in\mathcal H:
\operatorname{Con}_{K}(f)
\neq
\operatorname{Con}_{K}(g)
\right\}.
}
\]

Then:

\[
\boxed{
f\not\equiv_{\mathcal H}g
\iff
\operatorname{Sep}_{\mathcal H}(f,g)\neq\varnothing.
}
\]

### Generated question

> Which protected context separates \(f\) from \(g\)?

This is the canonical probe/breaker question.

---

## 5.6 Working nondistinction

Let:

\[
\mathcal D_t\subseteq\mathcal H
\]

be the contexts actually checked so far.

Write:

\[
\boxed{
f\approx_{\mathcal H,\mathcal D_t}g
}
\]

when none of the checked contexts has separated the pair.

Then:

\[
\boxed{
f\approx_{\mathcal H,\mathcal D_t}g
\centernot\Rightarrow
f\equiv_{\mathcal H}g.
}
\]

This remains one of the project's critical no-collapse laws.

---

# 6. Distinction, difference, boundary, replacement

## 6.1 Universal distinction

Do not keep the current pair:

\[
\delta=(D_+,D_-)
\]

as a universal primitive.

That is a useful set/predicate binding.

The universal distinction relation is:

\[
\boxed{
\operatorname{Dist}_{\mathcal H}(f,g)
\iff
f\parallel g
\land
\operatorname{Sep}_{\mathcal H}(f,g)\neq\varnothing.
}
\]

A distinction is therefore a **witnessable failure of contextual identification**.

## 6.2 Difference as transformation

If a binding supplies a transformation:

\[
d:f\rightsquigarrow g,
\]

then \(d\) may represent a replacement/deformation carrying one represented process into another.

Do not universally assume uniqueness or invertibility.

In torsor-like bindings, the difference may be unique.

In groupoids, several arrows may connect the same endpoints.

In irreversible process categories, no reverse transformation need exist.

## 6.3 Structural replacement binding

Where replacement has a preserved interface, use the native rewrite form:

\[
\boxed{
L
\xleftarrow{\ell}
K
\xrightarrow{r}
R.
}
\]

Interpretation:

- \(K\): structure identified/preserved through replacement;
- the left residual: what ceases;
- the right residual: what becomes.

This is a **native binding**, not a universal definition of all operators.

## 6.4 Boundary

Two exact meanings should be distinguished.

### Compositional boundary

An interface whose typing permits or forbids composition.

### Replacement boundary

The common preserved interface \(K\) through a structural rewrite.

The shared abstract meaning is:

\[
\boxed{
\textbf{boundary = structure conditioning lawful composition or identification through transformation.}
}
\]

Do not define boundary universally as spatial surface, Boolean complement, or metric threshold.

---

# 7. Actuality and observation

## 7.1 Actualization

For a represented operator \(f\), actual attempt is:

\[
\boxed{
!_{\mathbb B}f\Downarrow r.
}
\]

Read:

> actualizing \(f\) through binding \(\mathbb B\) returned \(r\).

This is a relation established only through the actualization channel.

It cannot be populated by a semantic answer generator merely because the generator predicts \(r\).

## 7.2 Action lifecycle

Retain:

\[
\boxed{
Query
\neq
Solve
\neq
ActionPlan
\neq
ActionAttempt
\neq
RawReturn
\neq
Interpretation
\neq
Warrant
\neq
SemanticCommit.
}
\]

This separation belongs to the epistemic layer and is untouched by the operator rebind.

## 7.3 Probe

A probe is a role played by an actualizable context/operator.

For example:

\[
p:A\to Z
\]

or, when probing changes the tested process:

\[
p:A\to A'\otimes Z
\]

in a binding with a suitable parallel product.

Its epistemic role is distinguishing:

\[
p\in \operatorname{Sep}_{\mathcal H}(f,g)
\]

when its completed consequences separate \(f\) and \(g\).

### Plain language

> A probe is an operator selected because actualizing or semantically composing it can expose a consequential difference.

## 7.4 Perception

Perception becomes:

\[
\boxed{
\textbf{actualized distinguishing composition.}
}
\]

A raw return can make a difference available before the system knows what that difference means.

Therefore:

\[
\boxed{
\text{perceptual return}
\neq
\text{interpretation}
\neq
\text{warranted claim}.
}
\]

---

# 8. Realized succession, state, and fold

## 8.1 Realized succession

A realized interaction history is represented as a realized factorization:

\[
\boxed{
\pi_t=(u_1,\ldots,u_t)
}
\]

with realized composite:

\[
\boxed{
F_t
=
\operatorname{Comp}(\pi_t)
=
u_t\circ\cdots\circ u_1.
}
\]

The event ledger remains a different history.

Repository event succession is evidence/authority history.

Binding-level \(\pi_t\) is realized domain/interactions history.

Never identify them without a binding proof.

## 8.2 Configuration

A configuration is an optional binding-specific view:

\[
\boxed{
p_{\mathbb B}:\Pi_{\mathbb B}\to X_{\mathbb B}.
}
\]

It is not universal state.

Two paths can share:

\[
p_{\mathbb B}(\pi)=p_{\mathbb B}(\pi')
\]

while remaining protected-context distinguishable.

## 8.3 Semantic quotient

Exact contextual equivalence is only defined directly between **parallel** terms. The quotient must therefore be taken hom-wise rather than by throwing all differently typed operators into one quotient carrier.

For every pair of interfaces \(A,B\), define:

\[
\boxed{
\mathsf Q_{\mathcal H}(A,B)
=
\mathsf{Tm}_{\mathbb B}(A,B)/{\equiv_{\mathcal H}}.
}
\]

The quotient map on that hom-family is:

\[
\boxed{
\eta_{\mathcal H}^{A,B}:
\mathsf{Tm}_{\mathbb B}(A,B)
\to
\mathsf Q_{\mathcal H}(A,B).
}
\]

When protected equivalence is a congruence for the admitted composition regime, composition descends:

\[
\boxed{
[g]_{\mathcal H}\circ[f]_{\mathcal H}
=
[g\circ f]_{\mathcal H}.
}
\]

Thus the semantic quotient is itself a compositional structure with the same interfaces and quotient hom-families.

This is more exact than writing one untyped \(X/{\equiv_{\mathcal H}}\).

For a particular retained-state binding with designated realized-process source interface \(A_0\), the current state at interface \(A\) is represented by a class in:

\[
\boxed{
\mathsf{State}_{\mathcal H}(A_0,A)
=
\mathsf Q_{\mathcal H}(A_0,A).
}
\]

No universal monoidal unit or privileged origin is assumed; a binding that has one may use it.

## 8.4 Executable encoding

A concrete implementation may encode the relevant quotient classes in a binding-specific carrier:

\[
S_{\mathcal H}^{A_0,A}.
\]

Let:

\[
\boxed{
enc_{\mathcal H}^{A_0,A}:
\mathsf Q_{\mathcal H}(A_0,A)
\to
S_{\mathcal H}^{A_0,A}.
}
\]

Then:

\[
\boxed{
\text{semantic quotient}
\neq
\text{executable encoding}.
}
\]

This makes a current no-collapse law explicit in notation instead of leaving both roles hidden under one map \(q\).

## 8.5 Operator descent

A fold becomes **state** for a continuation family only if each protected continuation acts on the folded representation.

Let:

\[
h:A_0\to A
\]

be a realized process and:

\[
a:A\to B
\]

an admitted continuation.

Postcomposition induces the fine-grain continuation map:

\[
\boxed{
L_a(h)=a\circ h.
}
\]

The continuation descends to the quotient exactly when there exists:

\[
\boxed{
\bar a:
\mathsf Q_{\mathcal H}(A_0,A)
\to
\mathsf Q_{\mathcal H}(A_0,B)
}
\]

such that:

\[
\boxed{
\eta_{\mathcal H}^{A_0,B}\circ L_a
=
\bar a\circ
\eta_{\mathcal H}^{A_0,A}.
}
\]

Equivalently:

\[
\boxed{
\bar a([h]_{\mathcal H})
=
[a\circ h]_{\mathcal H}.
}
\]

If concrete encodings are used, an executable update \(U_a\) must additionally satisfy:

\[
\boxed{
enc_{\mathcal H}^{A_0,B}([a\circ h]_{\mathcal H})
=
U_a\!\left(
enc_{\mathcal H}^{A_0,A}([h]_{\mathcal H})
\right).
}
\]

For deterministic history extension, this is the typed operator-first form of the current:

\[
q(h\cdot u)=U(q(h),u).
\]

### Plain language

> Folding process into state is lawful only if the future operation can be performed on the folded form without reopening the discarded detail.

This is the exact interpretation of:

> state is folded process that contains the condition of unfolding.

## 8.6 Congruence

The cleaner abstract condition is:

\[
\boxed{
f\equiv_{\mathcal H}g
\Rightarrow
K[f]\equiv_{\mathcal H}K[g]
}
\]

for every continuation context admitted by the executable-state contract.

This is contextual equivalence being a congruence over the protected composition regime.

---

# 9. Factorization, compression, promotion, reopening

## 9.1 Consequence factorization

For a representation:

\[
q:X\to S,
\]

retain the exact current criterion:

\[
\boxed{
Suff_{\mathcal H}(q)
\iff
\forall e\in\mathcal H,
\quad
\exists \bar e,
\quad
\operatorname{Con}_e
=
\bar e\circ q.
}
\]

In the operator-first kernel this is interpreted as:

> every protected observational/contextual consequence can be computed from the quotient representation.

## 9.2 Factorization defect

\[
\boxed{
FD_{\mathcal H}(q)
=
\{
(x,y):
q(x)=q(y)
\land
x\not\equiv_{\mathcal H}y
\}.
}
\]

This remains valid in any set-compatible realization.

At the abstract operator level:

\[
\boxed{
FD_{\mathcal H}(q)\neq\varnothing
}
\]

means the candidate representation identifies two processes that some protected context separates.

## 9.3 Promotion of a composite

Suppose:

\[
t=f_n\circ\cdots\circ f_1.
\]

A promoted operator \(m\) may be introduced with defining relation:

\[
\boxed{
m\doteq_{\mathcal H} t.
}
\]

Here \(\doteq_{\mathcal H}\) means:

- \(m\) and \(t\) are parallel;
- their protected consequences agree;
- use of \(m\) is licensed by the declared implementation/warrant contract.

Promotion may be a **semantic no-op** but an **operational gain** if \(m\) reduces future cost.

That is how expensive reasoning becomes compiled reusable reasoning.

## 9.4 Residue

If factorization detail may later matter, retain:

\[
\boxed{
\partial_{\eta}(\pi)
}
\]

as path/factorization residue.

It is distinct from unresolved epistemic requirements:

\[
\boxed{
\partial_{\eta}
\neq
\partial^- Q.
}
\]

## 9.5 Reopening

A new context \(K'\) reopens a quotient when:

\[
\boxed{
\exists f,g:
\eta_{\mathcal H}(f)=\eta_{\mathcal H}(g)
\land
\operatorname{Con}_{K'}(f)
\neq
\operatorname{Con}_{K'}(g).
}
\]

This is the operator-first form of the current reopening theorem.

---

# 10. Relation schemas: the missing bridge from notation to questions

The project already says a question asks for a typed relation. The exact completion of that idea is to make **relation schemas** explicit and define questions as their fibers.

## 10.1 Typed relation schema

Let:

\[
\boxed{
R
\hookrightarrow
X_1\times\cdots\times X_n
}
\]

be an \(n\)-ary typed relation schema.

Its ordered port signature is:

\[
\boxed{
\operatorname{sig}(R)
=
(x_1:X_1,\ldots,x_n:X_n).
}
\]

Each port name has semantic meaning.

Port names are not presentation decoration: they determine which value is being asked for and which substitutions are legal.

## 10.2 Relation discharge class

The same question syntax must not collapse semantic generation, deterministic derivation,
actuality, checking, and warrant. Therefore every relation schema declares an authority
or discharge class:

\[
\boxed{
mode(R)
\in
\{
Derived,\;
Candidate,\;
Actual,\;
Checked,\;
Warrant
\}.
}
\]

Interpretation:

- \(Derived\): the relation is determined by already standing typed data and a pure registered rule;
- \(Candidate\): a semantic generator may propose fillings, but the result is only a provisional claim;
- \(Actual\): the open port can be filled only by an actualization/return channel;
- \(Checked\): the relation is established only by an admitted independent checker;
- \(Warrant\): the relation is established only by the standing warrant policy.

This is not five different question calculi. It is one typed relation/query language with
five different lawful discharge routes.

For example:

\[
?_{r}Act_{\mathbb B}(f,r)
\]

is grammatically a question, but because \(mode(Act)=Actual\), it cannot be answered by
ordinary semantic generation. It must compile to an actual effect/return program.

Likewise:

\[
?_{w}(w\Vdash c)
\]

must compile to the warrant/checking route rather than a model asking itself to invent
its own warrant.

This field is what preserves the repository's existing authority boundaries inside the
unified question language.

## 10.3 Complete binding

A complete assignment:

\[
\gamma
=
(x_1\mapsto a_1,\ldots,x_n\mapsto a_n)
\]

produces the proposition:

\[
\boxed{
R[\gamma].
}
\]

A `Claim` may carry \(R[\gamma]\) as its proposition.

The claim remains provisional until warrant is established.

## 10.4 Partial binding

Let:

\[
I\subseteq\{1,\ldots,n\}
\]

be the set of open ports.

Let \(\beta\) bind every port outside \(I\).

Define the fiber:

\[
\boxed{
\operatorname{Fib}_{I}(R\mid\beta)
=
\left\{
a_I\in\prod_{i\in I}X_i:
R[\beta\oplus a_I]
\right\}.
}
\]

This is the answer space of the corresponding question.

## 10.5 Question

Define:

\[
\boxed{
?_{I}R[\beta]
}
\]

to mean:

> Which values of the open ports \(I\) complete the bound relation \(R[\beta]\)?

That is the canonical question object.

A question is therefore not another semantic object added beside relations.

It is a **relation seen through an open fiber**.

## 10.6 Candidate answer

For:

\[
a_I\in\operatorname{Fib}_{I}(R\mid\beta),
\]

the candidate answer yields:

\[
\boxed{
c
=
Claim\bigl(R[\beta\oplus a_I]\bigr).
}
\]

Generation can propose \(a_I\).

Only checking/actualization/warrant can establish standing.

## 10.7 The Jeopardy duality

The relation/prose/question correspondence is exact:

\[
\boxed{
\begin{array}{rcl}
R(x_1,\ldots,x_n)
&=&
\text{relation schema},\\
R[\gamma]
&=&
\text{fully bound proposition},\\
?_{I}R[\beta]
&=&
\text{partially bound question},\\
a_I
&=&
\text{candidate answer/filling}.
\end{array}
}
\]

Plain language is generated from the port labels and relation semantics.

For every relation \(R\), every nonempty set of open ports \(I\) generates a lawful question family.

There is therefore no need for a closed universal taxonomy of question types.

---

# 11. Relation expressions and compositional questions

## 11.1 Join

If relation schemas share compatible ports, their conjunction/join is:

\[
\boxed{
R\Join S.
}
\]

This creates a relation whose satisfying assignments satisfy both schemas.

Use `Join` only at the relation/query layer. It is distinct from operator composition \(\circ\).

## 11.2 Binding/substitution

For a partial binding \(\beta\):

\[
\boxed{
Bind(R,\beta)=R[\beta].
}
\]

A candidate answer may bind additional ports.

## 11.3 Projection/exposure

For a set of ports \(I\), expose only those ports:

\[
\boxed{
Expose_I(R).
}
\]

Set-theoretically, this is relational projection in bindings where ordinary relations are represented as sets of tuples.

Operationally, it defines which values the question asks the generator to supply.

## 11.4 Guard

For applicability relation \(G\):

\[
\boxed{
Guard_G(R)
=
R\Join G.
}
\]

A guard constrains when the question/relation is meaningful. It is not warrant.

## 11.5 Query expression grammar

A minimal data-only query language can be:

\[
\boxed{
E
::=
R
\mid
Bind(E,\beta)
\mid
Join(E,E)
\mid
Expose_I(E)
\mid
Guard_G(E).
}
\]

A concrete question is:

\[
\boxed{
Q=Ask(E).
}
\]

No arbitrary code is required.

This is compatible with the repository's existing inert-data and allowlisted-policy discipline.

---

# 12. Operational inquiry program

The current:

\[
K ::= Return(z)\mid Step(q,a,\kappa)
\]

mixes asking and acting in one constructor.

The operator-first version should preserve their semantic difference:

\[
\boxed{
\begin{aligned}
K
::={}&
Return(z)\\
&\mid Ask(Q,\kappa_c)\\
&\mid Act(f,\kappa_r),
\end{aligned}
}
\]

where:

\[
\boxed{
\kappa_c:
CandidateClaim(Q)\to K,
}
\]

and:

\[
\boxed{
\kappa_r:
RawReturn(f)\to K.
}
\]

`Ask` obtains a candidate semantic completion.

`Act` crosses the actuality boundary.

That distinction is already present in the repository's effect lifecycle and should appear in the abstract inquiry language.

---

# 13. Canonical relation basis

The universal question language is generated from relation schemas. A small standard basis makes the project operable without pretending that every future relation is known in advance.

The following basis is sufficient to regenerate most existing core question families.

## 13.1 Typing

\[
\boxed{
Type(f,A,B)
}
\]

Meaning:

> \(f\) is an admitted operator from interface \(A\) to interface \(B\).

Open-port questions:

- `?_{f} Type(f,A,B)` — What operator connects \(A\) to \(B\)?
- `?_{A} Type(f,A,B)` — What input interface does \(f\) require?
- `?_{B} Type(f,A,B)` — What output interface does \(f\) produce?

## 13.2 Composition

\[
\boxed{
Comp(f,g,h)
\iff
h=g\circ f.
}
\]

Questions:

- open \(h\): What results from composing \(g\) after \(f\)?
- open \(g\): What continuation after \(f\) yields \(h\)?
- open \(f\): What predecessor before \(g\) yields \(h\)?

This single relation generates forward construction, prerequisite, and inverse-completion questions.

## 13.3 Consequence

\[
\boxed{
Con(K,f,y)
\iff
\operatorname{Con}_{K}(f)=y.
}
\]

Questions:

- open \(y\): What consequence does \(f\) have in context \(K\)?
- open \(K\): Under what context does \(f\) have consequence \(y\)?
- open \(f\): What transform gives consequence \(y\) in \(K\)?

## 13.4 Separation

\[
\boxed{
Sep(K,f,g)
\iff
f\parallel g
\land
\operatorname{Con}_{K}(f)\neq\operatorname{Con}_{K}(g).
}
\]

Questions:

- open \(K\): What context/probe separates \(f\) and \(g\)?
- open \(g\): What alternative to \(f\) is separated by \(K\)?
- open \(f,g\): Which pair exposes the current representation gap?

## 13.5 Protected equivalence

\[
\boxed{
Eq_{\mathcal H}(f,g)
\iff
f\equiv_{\mathcal H}g.
}
\]

Questions:

- open \(g\): Which operators are protected-equivalent to \(f\)?
- open \(\mathcal H\): Under which horizon are \(f\) and \(g\) equivalent?

The second question is useful but potentially expensive; horizon synthesis remains a governed operation.

## 13.6 Factorization

\[
\boxed{
Factor(e,q,\bar e)
\iff
\operatorname{Con}_e
=
\bar e\circ q.
}
\]

Questions:

- open \(q\): What representation is sufficient for consequence \(e\)?
- open \(\bar e\): What readout computes \(e\) from representation \(q\)?
- open \(e\): Which consequences factor through \(q\)?

## 13.7 Operator descent

\[
\boxed{
Desc(\eta,a,\bar a)
\iff
\eta_B\circ L_a
=
\bar a\circ\eta_A
}
\]

where \(L_a(h)=a\circ h\), and the source/target quotient maps are the correctly typed
\(\eta_A:\mathsf{Tm}(A_0,A)\to\mathsf Q(A_0,A)\) and
\(\eta_B:\mathsf{Tm}(A_0,B)\to\mathsf Q(A_0,B)\).

Questions:

- open \(\bar a\): What compiled operator realizes \(a\) on the folded representation?
- open \(q\): What representation makes \(a\) descend?
- open \(a\): Which source operators are implementable by \(\bar a\)?

A failure of this relation is the exact recursive-state defect.

## 13.8 Actualization

\[
\boxed{
Act_{\mathbb B}(f,r)
}
\]

Meaning:

> actualizing \(f\) in binding \(\mathbb B\) produced raw return \(r\).

Only the environment/actualization boundary may establish this relation.

Question:

- open \(r\): What did actualization of \(f\) return?

This is not answered by semantic generation; it requires `Act`.

## 13.9 Support/warrant

Use:

\[
\boxed{
w\Vdash c
}
\]

for:

> warrant \(w\) licenses claim \(c\) in its exact pinned scope.

Questions:

- open \(w\): What warrant would license \(c\)?
- open \(c\): What exact claim does \(w\) support?

The warrant graph and non-self-licensing constraints remain separate structural conditions on admissible \(w\).

## 13.10 Preservation and gain

\[
\boxed{
Pres_{\mathcal H}(R',R)
}
\]

and:

\[
\boxed{
Gain_{\mathcal H}(R',R,g)
}
\]

record preserved capability and typed gain.

Then successor is derived:

\[
\boxed{
Succ_{\mathcal H}(R',R)
\iff
Pres_{\mathcal H}(R',R)
\land
\exists g\,Gain_{\mathcal H}(R',R,g)
\land
Warranted(R').
}
\]

Question:

- open \(R'\): What warranted successor preserves \(R\) and adds strict gain?

This is the canonical self-improvement question.

## 13.11 Recovery

Use a mode parameter:

\[
\boxed{
Recover_{\mu,\mathcal H}(m,c,k),
\qquad
\mu\in
\{
Use,
Reconstruct,
Evaluate,
Reacquire
\}.
}
\]

This preserves the project's required recovery distinctions while giving them one typed family.

---

# 14. Derived question families: exact replacements for the current taxonomy

The current four “primary pressures” are useful prose, but they should no longer be primitive question forms.

They are derived relations.

## 14.1 Variation

For candidate variation operator \(v\):

\[
\boxed{
PreserveCon_{\mathcal H}(v,f)
\iff
v\circ f
\equiv_{\mathcal H}
f
}
\]

or the corresponding contextual form.

Question:

> Which admissible transformation of \(f\) leaves the protected consequence unchanged?

This is `same-class-variation`.

## 14.2 Boundary crossing

\[
\boxed{
Cross_{\mathcal H}(v,f)
\iff
v\circ f
\not\equiv_{\mathcal H}
f.
}
\]

Question:

> Which admissible transformation crosses a protected consequence boundary?

Do **not** universally ask for the “smallest” such transform.

Minimality requires a declared preorder, metric, edit cost, or other comparison structure.

If the binding supplies \(\preceq\), ask for:

\[
\operatorname{Min}_{\preceq}
\{
v:Cross_{\mathcal H}(v,f)
\}.
\]

Otherwise retain the nondominated frontier.

## 14.3 Necessity breaker

In a binding with proposition/predicate structure, a proposed necessary factor \(D\) for consequence \(Y\) is attacked by:

\[
\boxed{
NBreak(x;D,Y)
\iff
Y(x)
\land
\neg D(x).
}
\]

Question:

> What case preserves the consequence while removing the proposed necessary condition?

## 14.4 Sufficiency breaker

\[
\boxed{
SBreak(x;D,Y)
\iff
D(x)
\land
\neg Y(x).
}
\]

Question:

> What case preserves the proposed sufficient condition while the consequence fails?

These two are binding-specific logical derivations, not universal operator primitives.

## 14.5 Actualization/prerequisite

Given target composite \(h\) and continuation \(g\):

\[
?_{f}Comp(f,g,h)
\]

asks:

> What predecessor/prerequisite makes the target composition possible?

Given \(f\) and target \(h\):

\[
?_{g}Comp(f,g,h)
\]

asks:

> What continuation realizes the target from here?

## 14.6 Factor proposal

Replace:

> Which factor best explains...

with:

\[
?_{q,\bar e}Factor(e,q,\bar e).
\]

Plain language:

> Through what candidate representation does this protected consequence factor?

If several candidates are found, use a declared partial order/frontier. Do not smuggle in “best.”

## 14.7 Conflict localization

Represent conflicts as relation instances with structured support/dependency references.

Open the implicated port:

> Which exact proposition, dependency, guard, binding, or representation relation is the smallest currently demonstrated locus of conflict?

Again, “smallest” is meaningful only relative to a declared containment/dependency order.

## 14.8 Residual characterization

A residual is the set of still-open fibers, failed factorizations, unresolved prerequisites, or unseparated live alternatives after reconciliation.

Question:

> Which typed relation port remains unresolved after the accepted update?

This is more exact than treating “residual” as one semantic species.

---

# 15. Mapping the current `core-v1` question catalog

The existing profile should remain operationally supported, but it becomes a compiled compatibility view over the relation calculus.

| Existing contract | Current role | Operator-first source relation | Exact interpretation |
|---|---|---|---|
| `obligation-characterization` | CHARACTERIZATION | arbitrary \(?_{I}R[\beta]\) | Identify the open relation/ports that must be established. |
| `same-class-variation` | VARIATION | \(?_{v}PreserveCon_{\mathcal H}(v,f)\) | Find a transform whose protected consequence is unchanged. |
| `minimal-boundary-crossing` | BOUNDARY | \(?_{v}Cross_{\mathcal H}(v,f)\) plus optional preorder | Find a separating transformation; “minimal” only when comparison structure is supplied. |
| `factor-proposal` | FACTOR | \(?_{q,\bar e}Factor(e,q,\bar e)\) | Find a consequence-sufficient factorization. |
| `necessity-counterexample` | NECESSITY | \(?_{x}NBreak(x;D,Y)\) | Search for consequence without the proposed condition. |
| `sufficiency-counterexample` | SUFFICIENCY | \(?_{x}SBreak(x;D,Y)\) | Search for condition without consequence. |
| `conflict-localization` | LOCALIZATION | open port of support/conflict relation | Identify the exact implicated structure. |
| `residual-characterization` | RESIDUAL | open unresolved relation fibers | Describe what remains unresolved after the current update. |

`core-v1` therefore remains a useful scheduler profile.

It is no longer the canonical set of all possible questions.

---

# 16. Mapping the current draft question families

The inactive catalog families should also be derived instead of promoted wholesale.

| Draft family | Derivation |
|---|---|
| binding | open ports of binding/interface/operator-admission relations |
| consequence | `Con` fibers |
| distinction | `Sep` / `Dist` fibers |
| equivalence | `Eq_H` fibers |
| second-distinction | separator over prior separator/context relations |
| arrangement | quotient/promotion/factorization relation |
| succession | `Comp` / path-factorization relation |
| stretch-negative | variation over an excluded/failed consequence class |
| squeeze-negative-to-positive | boundary-crossing transform with reversed target class |
| extreme-reversal | binding-specific variation operator family; no universal “extreme” without order |
| problem-reconstruction | open target/constraint relation |
| abstraction | `Factor` + quotient + promotion |
| description-control | open action/strategy relation plus explicit control certificate |
| actualization | `Act` |
| prerequisite | inverse fiber of `Comp`, support, or applicability relation |
| discharge-selection | open validator/evidence mechanism relation |
| warrant | `w ⊩ c` |
| success-localization | open cause/support/composition port on successful path |
| failure-localization | open violated relation/dependency port |
| generalization | candidate quotient/invariance relation |
| conditional-learning | successor relation under explicit context/horizon |
| reopening | new `Sep` witness against old quotient |
| compression | `Factor` / quotient relation |
| intermediate-lawfulness | congruence/descent at intermediate composites |
| question-selection | consequentiality / expected discrimination / resource frontier |
| progress | successor/gain relation |
| stopping | resolved/blocked/resource/external status relation |
| recurrent-perception | repeated actualization of same distinguishing operator with comparability relation |

This table is important: it demonstrates that the prior catalog was discovering fibers of a smaller relation algebra.

---

# 17. Claim roles after the rebind

Current `ClaimRole` values should become **compatibility and presentation tags**, not semantic primitives.

A claim's semantic identity should be a fully bound relation instance.

Recommended disposition:

| Current ClaimRole | New status |
|---|---|
| OBSERVATION | retain as tag for interpreted observation proposition; never raw return |
| CHARACTERIZATION | presentation tag for an open-port completion |
| VARIATION | derived relation tag |
| BOUNDARY | derived relation tag |
| FACTOR | derived relation tag |
| NECESSITY | binding-specific logical relation tag |
| SUFFICIENCY | binding-specific logical relation tag |
| PREREQUISITE | derived inverse-composition/support tag |
| CONFLICT | structured conflict relation tag |
| RESIDUAL | unresolved-fiber/residue tag |
| LOCALIZATION | open implicated-port tag |
| GENERALIZATION | quotient/invariance candidate tag |
| ACTUALIZATION | candidate/interpretation tag; actual return remains separate |
| INVARIANT | derived protected-equivalence tag |
| PATTERN | higher-order relation/composite candidate tag |
| INTERPRETATION | interpretation relation tag |
| UNKNOWN | **remove/demote as claim role**; `Unknown` is epistemic outcome/status, not a semantic relation |

This removes a category error already latent in the existing code: semantic relation role and epistemic failure/outcome should not share one enum.

---

# 18. Question compositionality

## 18.1 Question from notation

Every notation with a relation signature automatically provides its question forms.

Given:

\[
R(x_1:X_1,\ldots,x_n:X_n),
\]

choose nonempty \(I\subseteq\{1,\ldots,n\}\).

Bind the remaining ports.

The result:

\[
?_{I}R[\beta]
\]

is a question.

There is no additional semantic invention.

## 18.2 Answer substitution

If answer \(a\) fills port \(x_i\):

\[
R[\beta]
\;\xrightarrow{x_i:=a}\;
R[\beta\oplus(x_i\mapsto a)].
\]

If all ports are filled, the result is a proposition.

If some remain open, the answer generates another question.

This is the exact formal explanation of:

\[
\boxed{
\textbf{QUESTIONS GENERATE QUESTIONS THROUGH THEIR OWN OPEN REQUIREMENTS.}
}
\]

## 18.3 Joining questions

If:

\[
R(x,y)
\]

and:

\[
S(y,z)
\]

share \(y\), then:

\[
R\Join S
\]

creates the composite relational problem.

Opening \(z\) while binding \(x\) produces a multi-step question whose intermediate \(y\) may remain existential or be exposed.

This is a relational programming language.

## 18.4 Questions about questions

Reify a relation schema \(R\) as a value \(\ulcorner R\urcorner\) in a meta-binding.

Then define meta-relations such as:

\[
Redundant(R_1,R_2,\mathcal H),
\]

\[
Consequential(R,\mathcal H),
\]

\[
Admissible(R,\mathsf{Policy}),
\]

\[
Generates(R,Q'),
\]

\[
CompilesTo(R,\mathsf{Contract}).
\]

Opening their ports yields questions about the question repertoire itself.

No untyped reflection is required.

---

# 19. The generative reasoning presentation

## 19.1 Presentation

Define:

\[
\boxed{
\mathsf{Pres}_t
=
\langle
\mathsf G_t
\mid
\mathsf E_t
\rangle.
}
\]

\(\mathsf G_t\) contains admitted generators:

- primitive operators;
- relation schemas;
- probes;
- methods;
- compiled composites;
- question/operator schemas where admitted.

\(\mathsf E_t\) contains warranted constraints:

- typing laws;
- compositional equations;
- contextual equivalences;
- separations;
- guards/applicability;
- support dependencies;
- incompatibilities.

## 19.2 Free generation

\[
\boxed{
\mathsf{Tm}_t
=
\operatorname{Free}(\mathsf G_t).
}
\]

This is where candidate reasoning paths are constructed.

Generation has no warrant merely because it is grammatically lawful.

## 19.3 Quotient

\[
\boxed{
\mathfrak A_t(A,B)
=
\mathsf{Tm}_t(A,B)/{\equiv_{\mathcal H_t}}
}
\]

for each interface pair \(A,B\), with quotient composition defined only when contextual
equivalence is a congruence.

This identifies generated terms only where protected future contexts cannot distinguish them.

## 19.4 Why both are needed

If the system stores only the quotient, it may lose factorization/reopening information.

If it stores only the free term space, it repeatedly rediscovers equivalent computations.

Therefore generative reasoning requires both:

\[
\boxed{
\text{free construction}
\quad+\quad
\text{warranted quotient}.
}
\]

---

# 20. Learning as presentation change

The main learning moves now become exact.

## 20.1 Add a generator

\[
\boxed{
\mathsf G_{t+1}
=
\mathsf G_t\cup\{g\}.
}
\]

Justified when a consequential open relation has no adequate filling expressible from the existing repertoire.

Examples:

- new question operator;
- new probe;
- new native method;
- new action;
- new formal representation;
- new tool adapter.

## 20.2 Add a warranted equation: merge

\[
\boxed{
\mathsf E_{t+1}
=
\mathsf E_t\cup\{f\equiv_{\mathcal H}g\}.
}
\]

This compresses a distinction shown to be protected-future-null.

## 20.3 Refine/remove an equation: split

A new separator establishes:

\[
f\not\equiv_{\mathcal H'}g.
\]

The prior identification must be withdrawn or scoped to its original horizon.

## 20.4 Promote a composite

\[
m\doteq_{\mathcal H}f_n\circ\cdots\circ f_1.
\]

This adds a new generator with a defining equivalence.

If the promoted operator reduces cost while preserving protected behavior, it is a strict operational gain even when semantic consequence is unchanged.

## 20.5 Reopen

Expand the protected horizon:

\[
\mathcal H_t\subset\mathcal H_{t+1}
\]

and split any equivalence classes that the new contexts distinguish.

## 20.6 Rebind

If the current interfaces, relation schemas, or composition laws cannot even express the required consequential distinction:

\[
\boxed{
\mathbb B_t\rightsquigarrow\mathbb B_{t+1}.
}
\]

Rebinding changes the representational regime.

It must preserve explicit bridges, residue, prior warrant, and reopened obligations.

---

# 21. The epistemic ratchet on presentations

Let:

\[
\mathsf{Pres}_t
\]

be the incumbent presentation.

A candidate successor:

\[
\mathsf{Pres}'
\]

may replace it only when:

\[
\boxed{
\mathsf{Pres}'
\succ_{\mathcal H}
\mathsf{Pres}
}
\]

iff:

\[
\boxed{
Preserve_{\mathcal H}(\mathsf{Pres}',\mathsf{Pres})
\land
StrictGain_{\mathcal H}(\mathsf{Pres}',\mathsf{Pres})
\land
Warranted(\mathsf{Pres}').
}
\]

The four classic ratchet moves become presentation edits:

- **KEEP** — no warranted dominating edit;
- **SPLIT** — refine/remove a prior equation;
- **MERGE** — add a warranted equation;
- **REOPEN** — enlarge protected contexts and reconsider old equations.

Add one explicitly operational move:

- **PROMOTE** — add a named generator definitionally equivalent to a useful composite.

Promotion does not alter semantic equivalence but can alter future computational cost.

---

# 22. Memory in the operator-first system

Memory is best defined as:

\[
\boxed{
\textbf{retained compositional capacity whose presence changes protected future behavior or recovery cost.}
}
\]

This may include:

- primitive generators;
- promoted composites;
- operator factorizations;
- distinguishing contexts;
- relation schemas;
- support/warrant ancestry;
- failed routes;
- prerequisite structure;
- reopening conditions;
- reacquisition scaffolds.

A remembered result need not be directly reconstructible.

A prior episode may survive because:

\[
\mathfrak C_{\mathcal H}(m,c,k)
\prec
\mathfrak C^0_{\mathcal H}(c,k).
\]

The existing four recovery modes remain:

\[
Use,\quad
Reconstruct,\quad
Evaluate,\quad
Reacquire.
\]

---

# 23. Higher-grain arrangement and objecthood

The current document says a retained invariant of realized succession at one grain may become arrangement at a higher grain.

Operator-first, this becomes more exact.

Suppose a fine-grain composite:

\[
t=f_n\circ\cdots\circ f_1
\]

is protected-equivalent to promoted operator \(m\).

Then at the higher grain, use:

\[
m
\]

as one operator/interface-bearing unit.

The internal factorization remains residue only if protected future use can inspect it.

Thus:

\[
\boxed{
\text{fine composition}
\to
\text{contextual quotient}
\to
\text{promoted operator}
\to
\text{new composition}.
}
\]

An “object” at a grain is therefore a stable compositional interface/profile generated from lower-grain process, not a universal primitive.

---

# 24. Native precedent and bridges

The current bridge notation should become explicitly composition-preserving.

For bindings \(\mathbb B,\mathbb B'\), a bridge:

\[
\boxed{
\beta:
\mathsf{Tm}_{\mathbb B}
\rightsquigarrow
\mathsf{Tm}_{\mathbb B'}
}
\]

must state which fragment it preserves.

Where composition is preserved:

\[
\boxed{
\beta(g\circ f)
\equiv
\beta(g)\circ\beta(f).
}
\]

Where protected consequence is preserved:

\[
\boxed{
\operatorname{Con}^{\mathbb B}_{K}(f)
\equiv
\operatorname{Con}^{\mathbb B'}_{\beta(K)}(\beta(f)).
}
\]

Anything unpreserved is:

\[
Residue(\beta).
\]

This is the exact sense in which native mathematics may be transported without equating domains.

---

# 25. Goals and control

A goal is still not a primitive of reasoning.

It supplies or prioritizes protected consequence relations.

Control remains stronger than description.

An action/control binding must supply explicit strategy/action relations.

Do not derive control from:

- correlation;
- factorization;
- prediction;
- observed reachability.

The operator-first kernel simply makes the control distinction cleaner: a descriptive relation says what compositions have which consequences; a control certificate additionally establishes a lawfully selectable action/strategy operator satisfying target constraints.

---

# 26. Self-application

## 26.1 Meta-binding

Reify the current presentation:

\[
\ulcorner\mathsf{Pres}_t\urcorner
\]

into a meta-binding.

Candidate meta-operators include:

\[
AddGenerator,
\]

\[
AddEquation,
\]

\[
SplitEquation,
\]

\[
PromoteComposite,
\]

\[
RetireGenerator,
\]

\[
ChangeInterface,
\]

\[
Rebind,
\]

\[
ChangeImplementation.
\]

These act on presentations:

\[
\boxed{
m:
\mathsf{Pres}_t
\rightsquigarrow
\mathsf{Pres}_{t+1}.
}
\]

## 26.2 Self-improvement question

The canonical question is:

\[
\boxed{
?_{\mathsf{Pres}'}
Succ_{\mathcal H}
(
\mathsf{Pres}',
\mathsf{Pres}_t
).
}
\]

Plain language:

> What successor of the current reasoning presentation preserves every still-valid protected capability, adds a strict typed gain, and can receive independent warrant?

That is a precise self-improvement objective.

## 26.3 Through itself / through not itself

Through itself:

\[
\mathsf{Pres}_t
\to
?_{\mathsf{Pres}'}
Succ_{\mathcal H}(\mathsf{Pres}',\mathsf{Pres}_t).
\]

Through not itself:

\[
Candidate
\to
sealed\ discriminator
\to
!_{\mathbb B}a\Downarrow r.
\]

Changes itself:

\[
(\mathsf{Pres}_t,r,w)
\to
\mathsf{Pres}_{t+1}.
\]

The candidate may generate the challenge.

It may not determine the return or warrant by accepting itself.

---

# 27. Exact notation registry

The following registry gives each recommended canonical symbol one unique job.

| Notation | Type / role | Exact meaning | Must not be confused with | Direct connections |
|---|---|---|---|---|
| \(\mathbb B\) | binding | supplies interfaces, operators, composition, semantics, actuality, checking | interface \(B\) | indexes all binding-relative structures |
| \(A,B,C\) | interface | compositional source/target types | binding | type operators |
| \(\mathsf{Int}_{\mathbb B}\) | family | interfaces admitted by binding | state set | source/target of terms |
| \(\mathsf G_{\mathbb B}(A,B)\) | generator family | primitive admitted operators \(A\to B\) | all derived terms | generates \(\mathsf{Tm}\) |
| \(f,g,a\) | operator terms | represented transformations | claims, returns | compose under \(\circ\) |
| \(1_A\) | operator | identity at interface \(A\) | “nothing happened” evidence | unit for composition |
| \(g\circ f\) | operator | first \(f\), then \(g\) | relation join | serial transformation |
| \(\mathsf{Tm}_{\mathbb B}(A,B)\) | term family | all well-typed generated composites | actual executions | free generative space |
| \(\pi\) | factorization/path | ordered term sequence | probe \(p\) | maps to composite |
| \(\operatorname{Comp}(\pi)\) | operator | composite denoted by path | configuration | may be quotient-promoted |
| \(K[-]\) | context | typed open composition | consequence \(K_e\) codomain | exposes differences |
| \(\mathcal H\) | horizon | protected future context family | checked discriminator set | defines equivalence |
| \(Y_K\) | consequence type | codomain for consequence of context \(K\) | raw return type | types `Con` |
| \(\operatorname{Con}_K(f)\) | semantic consequence | result of completing \(K\) with \(f\) under binding semantics | raw return | defines `Sep`, `Eq` |
| \(f\parallel g\) | relation | common source/target | equivalence | prerequisite for direct comparison |
| \(f\equiv_{\mathcal H}g\) | exact equivalence | all protected contexts give equal consequence | working nondistinction | quotient relation |
| \(\mathcal D_t\) | tested contexts | discriminator subset actually checked | horizon \(\mathcal H\) | defines working relation |
| \(f\approx_{\mathcal H,\mathcal D_t}g\) | working relation | no checked context has separated pair | exact equivalence | bounded epistemic status |
| \(\operatorname{Sep}_{\mathcal H}(f,g)\) | set/family | protected contexts that separate \(f,g\) | replacement operator | witnesses inequivalence |
| \(R\) | relation schema | typed \(n\)-ary relation | operator \(f\) | source of questions |
| \(\operatorname{sig}(R)\) | signature | named typed ports of relation | operator signature | controls legal binding |
| \(\beta\) | partial binding | values assigned to some relation ports | cross-binding bridge \(\beta\); rename bridge to \(\mathcal B\) if needed | forms question fiber |
| \(I\) | port-index set | currently open ports | identity interface | defines question |
| \(\operatorname{Fib}_{I}(R\mid\beta)\) | answer fiber | values completing relation | live-world state set | candidate answers |
| \(?_{I}R[\beta]\) | question | relation with ports \(I\) open | claim | asks for fiber |
| \(\gamma\) | complete port binding | all relation arguments fixed | grain | creates proposition |
| \(R[\gamma]\) | proposition | fully bound relation instance | warranted fact | payload of claim |
| \(c\) | claim | inert proposal carrying proposition | consequence | may receive warrant |
| \(w\Vdash c\) | warrant relation | \(w\) licenses exact claim \(c\) | truth by generation | positive standing |
| \(r\) | raw return | immutable environment return | semantic consequence | enters through actuality |
| \(!_{\mathbb B}f\Downarrow r\) | actuality relation | actual attempt of \(f\) returned \(r\) | predicted consequence | independent constraint |
| \(\Pi_t\) | prediction seal | prospective commitment before return | return \(r\) | mismatch comparison |
| \(\Sigma_t\) | inquiry aggregate/standing | replayable authoritative inquiry state | retained semantic state | implementation/governance state |
| \(\pi_t\) | realized factorization | binding-level realized operator path | ledger sequence | source of semantic fold |
| \(p_{\mathbb B}\) | configuration projection | optional path→configuration view | probe \(p\); prefer `cfg_B` in code/doc | endpoint/view only |
| \(\mathsf Q_{\mathcal H}(A,B)\) | quotient hom-family | parallel process terms \(A\to B\) modulo exact protected equivalence | question \(Q\), concrete state carrier | semantic process classes |
| \(\eta_{\mathcal H}^{A,B}\) | quotient map | parallel term \(A\to B\) → contextual equivalence class | concrete encoding | exact semantic fold |
| \(S_{\mathcal H}^{A_0,A}\) | encoded retained state | concrete encoding of retained process classes from \(A_0\) to \(A\) | semantic quotient itself | storage/computation |
| \(enc_{\mathcal H}^{A_0,A}\) | encoding | quotient process class→concrete retained state | quotient map | separates semantics from encoding |
| \(\bar a\) | descended operator | action induced on retained representation | original \(a\) | executable continuation |
| \(Suff_{\mathcal H}(q)\) | predicate | all protected consequences factor through q | recursive executability | exact output sufficiency |
| \(FD_{\mathcal H}(q)\) | defect set | pairs falsely identified by q | path residue | compression failure |
| \(\partial_{\eta}\) | representation residue | omitted factorization/detail required for reopening/recovery | \(\partial^-Q\) | compression maintenance |
| \(\partial^+Q\) | question completion field | admissible answer values | representation residue | query forward field |
| \(\partial^-Q\) | unresolved prerequisites | relation/guard requirements not established | representation residue | query backward field |
| \(\mathfrak C_{\mathcal H}\) | cost frontier | nondominated recovery/resource costs | scalar score | reacquisition comparison |
| \(\mathsf{Pres}_t\) | presentation | admitted generators + warranted relations | inquiry aggregate | object of self-improvement |
| \(\mathsf E_t\) | presentation laws | warranted equations/constraints | evidence records | quotient/composition semantics |
| \(\mathfrak A_t(A,B)\) | quotient reasoning hom-family | parallel free terms modulo protected equivalence | aggregate state | reusable semantic competence |
| \(\succ_{\mathcal H}\) | successor relation | preserve + strict gain + warrant | chronological “later” | ratchet |
| \(\mathcal B_{\mathbb B\mathbb B'}\) | bridge | relation/operator transport across bindings | partial port binding \(\beta\) | native-method transport |
| \(Residue(\mathcal B)\) | bridge residue | structure not preserved by transport | compression residue | new inquiry |
| \(K ::= \cdots\) | inquiry program | adaptive control over candidates/returns | semantic relation | execution orchestration |

The canonical rewrite should aggressively remove any remaining symbol collision.

---

# 28. How every notation is connected

The formalization should be represented internally as a **notation dependency graph**.

Let:

\[
\boxed{
\mathcal N=(V_N,E_N)
}
\]

where every canonical symbol/definition is a node and edges are typed by:

\[
\{
types,
generates,
composes,
binds,
indexes,
defines,
separates,
factors,
descends,
actualizes,
returns,
interprets,
warrants,
compresses,
recovers,
reopens,
supersedes,
transports
\}.
\]

Examples:

\[
\mathbb B
\xrightarrow{types}
\mathsf{Int}_{\mathbb B},
\]

\[
\mathsf G_{\mathbb B}
\xrightarrow{generates}
\mathsf{Tm}_{\mathbb B},
\]

\[
\circ
\xrightarrow{composes}
\mathsf{Tm}_{\mathbb B},
\]

\[
\mathcal H
\xrightarrow{indexes}
\equiv_{\mathcal H},
\]

\[
\operatorname{Con}
\xrightarrow{defines}
\operatorname{Sep},
\]

\[
\operatorname{Sep}
\xrightarrow{defines}
\not\equiv_{\mathcal H},
\]

\[
\equiv_{\mathcal H}
\xrightarrow{quotients}
Q_{\mathcal H},
\]

\[
Q_{\mathcal H}
\xrightarrow{encodes}
S_{\mathcal H},
\]

\[
a
\xrightarrow{descends}
\bar a,
\]

\[
!_{\mathbb B}a
\xrightarrow{returns}
r,
\]

\[
r
\xrightarrow{supports\ interpretation}
c,
\]

\[
w
\xrightarrow{warrants}
c,
\]

\[
\mathsf{Pres}_t
\xrightarrow{successor}
\mathsf{Pres}_{t+1}.
\]

No two symbols need a direct relation merely because they share the document.

But every kernel symbol must have a connected path to the central chain:

\[
\boxed{
\text{composition}
\to
\text{consequence}
\to
\text{distinction}
\to
\text{actuality}
\to
\text{warrant}
\to
\text{successor}.
}
\]

A notation node with no such path is either:

1. binding-specific;
2. implementation-specific;
3. redundant;
4. insufficiently defined.

That gives a mechanical primitive audit.

---

# 29. Exact rule for prose ↔ notation ↔ question

For every relation schema \(R\), the specification should provide four synchronized forms.

## Formal definition

\[
R(x_1,\ldots,x_n).
\]

## Declarative prose

> \(R\) holds when [exact relation among named ports].

## Port glossary

Each port has:

- name;
- type;
- semantic role;
- applicability condition.

## Question renderings

For every meaningful nonempty open-port set \(I\):

\[
?_{I}R[\beta]
\]

gets a canonical plain-language rendering:

> What [open-port role] makes [bound relation] hold?

This establishes a 1:1 semantic compiler:

\[
\boxed{
\text{relation schema}
\leftrightarrow
\text{declarative prose}
\leftrightarrow
\text{typed question family}.
}
\]

Natural-language surface variants may be many-to-one.

Semantic relation identity remains one-to-one.

---

# 30. What changes in each canonical section

The uploaded canonical file should not be patched in place. It should be rederived in the following order.

| Current section | Disposition | Operator-first replacement |
|---|---|---|
| Purpose | KEEP/SHARPEN | regenerative sufficiency now applies to compositional repertoire |
| Typed carriers and relations | REWRITE | interfaces + operators + composition + term generation |
| Local reasoning context | KEEP/RENAME COLLISIONS | scope/grain/assumptions/applicability/horizon/resources |
| Context and experiment | MOVE EARLIER | context is open composition |
| Protected horizon | KEEP | family of protected compositional contexts |
| Consequential equivalence | KEEP/GENERALIZE | equivalence of parallel operator terms |
| Working nondistinction | KEEP | checked context subset |
| Horizon refinement | KEEP | same theorem |
| Distinction | DERIVE | separator/contextual inequivalence; set pair only in predicate bindings |
| Exterior | DERIVE | contexts/replacements that break standing equivalence/invariance |
| Live possibility | REWRITE | live candidate fillings/terms, not universal world-state subset |
| Resolution | REWRITE | all live candidate fillings contextually equivalent or relation fiber resolved |
| Claim | KEEP | fully bound relation proposition carried provisionally |
| Question | REWRITE | relation fiber \(?_{I}R[\beta]\) |
| Forward/backward fields | DERIVE | open answer ports + unresolved prerequisite/guard ports |
| Consequential question | KEEP/RETYPE | candidate fillings induce protected-different continuations |
| Four pressures | DERIVE | variation/crossing/breaker/actualization relation fibers |
| Derived directions | RECOMPILE | all from standard relation basis |
| Question-basis insufficiency | KEEP/GENERALIZE | required relation/fiber has no expressible discriminator/operator |
| Transformation | MOVE TO KERNEL | primitive |
| Boundary crossing | DERIVE | `Cross` relation; minimality conditional on order |
| Controlled variation | DERIVE | operator family preserving comparability |
| Working invariant | REWRITE | protected equivalence under variation operator family |
| Constructed possibility | KEEP | free terms are constructible |
| Action lifecycle | KEEP | unchanged |
| Prediction seal | KEEP | unchanged |
| Non-self-licensing | KEEP | unchanged |
| Warrant | KEEP | unchanged |
| Reconciliation | KEEP/RETYPE | presentation/claim updates limited by return+warrant |
| Realized history | REWRITE | realized factorization \(\pi_t\) |
| Configuration | DEMOTE | optional binding projection |
| Present frontier | KEEP | realized composite / actuality frontier / possible continuation |
| Probe | DERIVE | actualizable distinguishing operator/context |
| Perception | REWRITE | actualized distinguishing composition |
| Recurrent perception | KEEP/DERIVE | repeated comparable actualization of same operator |
| Attention | DERIVE/OPTIONAL | active relation/context restriction |
| Succession→arrangement | REWRITE | quotient-stable composite promoted as higher-grain operator |
| Objecthood | DEMOTE | stable compositional profile/interface |
| Arrangement→succession | REWRITE | promoted operator participates in further composition |
| Path sensitivity | KEEP | factorization may remain consequential |
| Retained state | REWRITE | contextual quotient + explicit encoding |
| Factorization theorem | KEEP | central compression law |
| Factorization defect | KEEP | central breaker |
| Recursive state | REWRITE | operator descent/congruence |
| Carrier languages | DEMOTE | binding-specific predicate/effect languages |
| Lift/descent of determinations | KEEP AS BINDING THEOREMS | inverse image/saturation where sets/predicates exist |
| Memory | REWRITE | retained compositional capacity |
| Recovery modes | KEEP | one indexed family or distinct relations |
| Recovery equivalence | KEEP | protected consequence equivalence |
| Reacquisition advantage | KEEP | Pareto frontier |
| State update | REWRITE | realization/transition under fixed presentation |
| Representation learning | GENERALIZE | presentation/quotient/operator change |
| General learning | KEEP/SHARPEN | warranted deformation of future compositional capacity |
| Retrospective→prospective | KEEP | compilation/promotion witness |
| Forgetting | KEEP | lost future compositional/recovery capacity |
| Exact quotient | KEEP/GENERALIZE | process term quotient |
| Occlusion | KEEP | hide factorization under regeneration contract |
| Residue | KEEP | factorization/recovery residue |
| Promotion | REWRITE | named operator for stable composite |
| Reopening | KEEP | new context breaks quotient |
| Ratchet | KEEP/RETARGET | presentation/operator quotient |
| Structured friction | KEEP | separator-generation pressure |
| Native precedent | KEEP | find native realization of relation/operator |
| Bridge | KEEP/SHARPEN | composition/consequence-preserving translation |
| Goals | KEEP | prioritize horizons/target relations |
| Control | KEEP | explicit action/strategy operator certificates |
| Availability | KEEP | actual availability != warrantable selection |
| Relational holes | MERGE INTO QUESTION CALCULUS | open typed ports/contexts |
| Representation gap | GENERALIZE | composition/query/operator/binding gap |
| Rebind | KEEP | change interface/operator/relation regime |
| Self-application | REWRITE | presentation is operand in meta-binding |
| Through itself/not itself | KEEP | exact self-improvement recurrence |
| Regenerative extensibility | KEEP | now defined over presentation changes |
| Inquiry program | REWRITE | separate Ask from Act |
| Canonical rhythm | REGENERATE | derive next operation from open relation |
| Stop conditions | KEEP | unchanged |
| No-collapse laws | KEEP + ADD | add operator/context/state distinctions |
| GoodAccept | KEEP/GENERALIZE | apply to relation/operator/presentation successors |
| Kernel counterexamples | REWRITE | test operator-first regenerative sufficiency |
| Full invariant | REWRITE | operator-first |
| Smallest operational form | REWRITE | compositional |
| Final compression | REWRITE | composition is semantic center |

---

# 31. New no-collapse laws required by the rebind

Add:

\[
\boxed{
\text{interface}
\neq
\text{operator};
}
\]

\[
\boxed{
\text{operator term}
\neq
\text{actualized operation};
}
\]

\[
\boxed{
\text{operator composition}
\neq
\text{relation join};
}
\]

\[
\boxed{
\text{relation schema}
\neq
\text{question};
}
\]

\[
\boxed{
\text{question}
\neq
\text{candidate answer};
}
\]

\[
\boxed{
\text{candidate answer}
\neq
\text{fully bound warranted relation};
}
\]

\[
\boxed{
\text{semantic quotient}
\neq
\text{concrete encoding};
}
\]

\[
\boxed{
\text{composite endpoint}
\neq
\text{factorization};
}
\]

\[
\boxed{
\text{promoted composite}
\neq
\text{irreversible loss of factorization};
}
\]

\[
\boxed{
\text{question-family tag}
\neq
\text{relation semantics};
}
\]

\[
\boxed{
\text{epistemic Unknown}
\neq
\text{semantic relation role};
}
\]

\[
\boxed{
\text{semantic unification}
\neq
\text{governance-role collapse}.
}
\]

---

# 32. Repository correspondence

The live repository should be interpreted as follows.

## 32.1 `src/rci/core`

Remain the authority/event substrate.

The operator-first rebind does not replace:

```text
decide(state, command) -> events
evolve(state, event) -> state
EventStore.append(...)
plan_next(state) -> StepPlan
```

`InquiryState` remains the replay-complete aggregate.

It is **not** renamed into semantic process state.

## 32.2 `src/rci/questions`

Current `QuestionContract` becomes a compiled/presentation contract over a relation fiber.

Its existing fields remain useful:

- typed input roles;
- output claim role;
- precondition policy;
- inert renderer;
- update/follow-up rules;
- recurrent probe metadata.

The semantic core should eventually be:

```text
RelationSchema
+ partial port bindings
+ open ports
```

and `QuestionContract` should identify/render an admitted projection of that relation.

Existing sealed contracts remain unchanged as versioned compatibility data.

## 32.3 `src/rci/claims`

Current `Claim` remains an immutable provisional carrier.

Future relation-aware claims should link to a fully bound `RelationInstance`.

Do not mutate old claim schemas.

Add a new link/event/projection if needed.

Current `ClaimRole` remains compatibility metadata; semantic meaning moves to relation schema identity.

`UNKNOWN` should eventually be removed from newly generated semantic-role vocabularies.

## 32.4 `src/rci/orchestration`

The deterministic scheduler remains.

Its job is authority/budget/order over open obligations.

It should not become the semantic question generator.

A new relation-query compiler should be capable of generating ordinary `Obligation`s from unresolved relation fibers, after which the existing scheduler can schedule them.

## 32.5 `src/rci/probes`

`ProbeIdentity` becomes the identity of an admitted distinguishing operator/context under exact binding/scope/horizon/comparison pins.

`ProbeTrace` remains repeated comparable actualization of one operator.

`PredictionSeal`, `Mismatch`, return linkage, and semantic delta remain unchanged in authority meaning.

`SemanticField` becomes a derived context/relation view rather than an independent semantic ontology.

## 32.6 `src/rci/learning`

`RepresentationGap` generalizes naturally to:

```text
CompositionGap / ExpressibilityGap
```

with subcases:

- no term fills required context;
- no separator is available;
- operator does not descend;
- relation language inadequate;
- binding inadequate.

`LearnedProbeCandidate` is a specialization of a future generic `OperatorCandidate`.

Its existing holdout, redundancy, protected-error, challenge, and admission checks are exactly the sort of evidence a new operator must pass.

## 32.7 `src/rci/compression`

This package becomes the clearest existing implementation of operator-first quotient discipline.

Map:

- `CONSEQUENCE_FACTORIZATION` → context consequence factors through representation;
- `EXACT_EQUIVALENCE` → quotient law;
- `CONTINUATION_COMPATIBILITY` → congruence/descent;
- `RECURSIVE_UPDATE` → compiled operator action;
- `DETERMINATION_DESCENT` → binding-specific predicate descent;
- `RESIDUE_COMPLETENESS` → factorization/reopening residue.

`PathResidue` becomes omitted operator-factorization residue.

`RepresentationReopening` is exactly a new context that splits an old quotient.

Do not delete existing carrier contracts. Treat them as a state-centric realization of the more general operator quotient.

## 32.8 `src/rci/formal`

The Boolean/finite-enum AST remains one native relation language.

It is not the universal question language.

The relation/query calculus must sit above it and may compile a query into this AST only when the binding relation is Boolean/finite-enum.

## 32.9 `src/rci/memory`

Logical ownership remains.

Memory records are implementation evidence of retained compositional capacity.

No second writable “operator memory” authority should be introduced.

Promoted operators, methods, probes, and contracts belong logically with the existing procedural memory/repertoire owner `M_P` or through derived projections linked to its admitted records.

## 32.10 `src/rci/project`

Keep the present distinction among:

- theory;
- question;
- probe;
- representation;
- method;
- evidence;
- implementation;
- authority.

These are **diagnostic/governance roles**.

Semantically, many may become operator or relation-presentation changes.

Governance must continue to distinguish them because they authorize different mutations and evidence requirements.

`CapabilitySuccessorCandidate`, `CapabilityFrontier`, `ImplementationGoalContract`, and independent promotion remain the self-improvement authority boundary.

---

# 33. Existing verified milestones under the rebind

## G1

No semantic invalidation.

The effect/return/check/warrant architecture is required unchanged.

## G2A

Recovery/reconstruction remain valid.

Interpret as recovery of compositional capacity rather than only stored semantic objects.

## G2B

Learned probes become the first verified operator-repertoire learning mechanism.

The holdout/redundancy/protected-behavior admission pipeline should become evidence for generic operator admission.

## G3A-H

Becomes a verified state-centric instance of the general quotient/congruence theory.

It is not discarded.

## G3R

Becomes the project-level ratchet over the operator/relation presentation.

## G3Q

Already demonstrates safe generation and admission of a new question operator.

The new relation language should subsume it, not replace its authority checks.

## G3G

Already demonstrates compilation from an admitted project return and frontier selection into an inert Goal candidate under separate admission.

It is a concrete meta-operator pipeline.

---

# 34. Proposed new implementation records

Do not create all of these unless the acceptance Goal requires them.

The minimal useful seam is:

```text
RelationPort {
    name
    type_ref
}

RelationSchema {
    id
    version
    ports
    semantics_id
    discharge_class
    applicability_policy_id
}

RelationBinding {
    port_name
    value_ref
}

FiberQuery {
    relation_schema_key
    bound_ports
    open_ports
    scope
    binding_revision
    protected_horizon_id
}
```

A fully bound `FiberQuery` is invalid as a question and should instead compile to a relation proposition/claim instance.

A relation-aware question contract can be a derived view:

```text
RelationSchema + FiberQuery
    -> admitted QuestionContract rendering
```

For actual operator compilation later:

```text
OperatorSignature {
    source_interface_ref
    target_interface_ref
    binding_revision
}

CompositeExpr =
    Identity(interface)
  | Primitive(operator_ref)
  | Compose(left, right)

CompositePromotion {
    composite_expr
    promoted_operator_ref
    protected_equivalence_check_ref
    cost_gain_ref
    warrant_ref
    provenance_refs
    reopening_condition_refs
}
```

No source code, arbitrary callable, shell, network, or authority is implied by these records.

---

# 35. Proposed relation-query compiler

The compiler should perform only deterministic structural work:

1. resolve relation schema;
2. validate port names and types;
3. validate exact bound/open partition;
4. apply scope/binding/horizon pins;
5. derive the fiber query;
6. select an admitted rendering contract;
7. create an ordinary obligation;
8. bind a returned candidate into a provisional relation instance/claim;
9. leave checking/warrant/promotion to existing pipelines.

Pseudo-interface:

```text
compile_query(
    schema,
    bound_ports,
    open_ports,
    context
) -> CompiledRelationQuestion
```

It must not:

- call tools;
- generate source;
- select policy;
- warrant answers;
- alter the horizon;
- self-admit a relation schema.

This generalizes G3Q's current safe compilation boundary.

---

# 36. Proper question selection

The scheduler should choose among already lawful open fibers.

A question \(Q=?_I R[\beta]\) is consequential when there exist candidate completions:

\[
a,b\in\operatorname{Fib}_{I}(R\mid\beta)
\]

whose warranted successor continuations would differ under the protected project horizon.

Write:

\[
\boxed{
Consequential_{\mathcal H}(Q)
}
\]

only after the continuation mapping is pinned.

Question selection may use a partial order over:

- safety;
- prerequisite depth;
- discrimination;
- reversibility;
- cost;
- resource bounds.

Do not assume one scalar information-gain score.

The current deterministic scheduler's safety/priority/dependency/order policy can remain the operational default.

---

# 37. Question-basis learning

A question repertoire is inadequate when a protected difference exists but the current relation language cannot expose a lawful separator or required open fiber.

Three distinct failures:

## Missing relation

No current schema describes the required relation.

\[
R\notin Expressible(\mathsf{Rel}_t).
\]

Candidate response: add relation schema.

## Missing operator

The relation is expressible, but no admitted term fills the required operator port.

\[
\operatorname{Fib}_{I}(R\mid\beta)
\cap
\mathsf{Tm}_t
=
\varnothing.
\]

Candidate response: acquire/generate a new operator or native method.

## Missing discriminator

Candidate alternatives exist, but no admitted context separates them.

\[
f\not\equiv_{\mathcal H}g
\quad\text{is required by protected consequence, but}\quad
\operatorname{Sep}_{\mathcal D_t}(f,g)=\varnothing.
\]

Candidate response: learn a probe/context.

These failures must remain distinct.

---

# 38. Native methods as operator acquisition

A `MethodBindingCandidate` already names:

- relation;
- native field;
- method;
- sources;
- assumptions;
- applicability checks;
- license;
- adapter requirement.

Under the new semantics:

\[
\boxed{
\text{native method admission}
=
\text{admission of a new operator/relation implementation under a bridge.}
}
\]

The project should first ask:

\[
?_{\mathcal B}
BridgePreserves(R_{\text{required}},R_{\text{native}},\mathcal B).
\]

Only then can the native method become an admitted generator.

---

# 39. Self-improvement loop in exact form

Let current project/reasoning presentation be:

\[
\mathsf{Pres}_t.
\]

## Step 1: expose an open consequential relation

\[
Q_t
=
?_{I}R[\beta].
\]

## Step 2: search existing generated terms

\[
Candidates_t
=
\operatorname{Fib}_{I}(R\mid\beta)
\cap
\mathsf{Tm}_t.
\]

## Step 3: if alternatives exist, construct separator

For \(f,g\in Candidates_t\):

\[
?_{K}Sep(K,f,g).
\]

## Step 4: if no adequate term exists, localize the gap

\[
Gap
\in
\{
Relation,
Operator,
Probe,
Method,
Representation,
Binding,
Evidence,
Authority
\}.
\]

## Step 5: generate a candidate successor

\[
?_{\mathsf{Pres}'}
Succ_{\mathcal H}
(
\mathsf{Pres}',
\mathsf{Pres}_t
).
\]

## Step 6: seal discriminator before return

\[
\Pi_t\prec r_{t+1}.
\]

## Step 7: actualize through not-self

\[
!_{\mathbb B}a_t\Downarrow r_{t+1}.
\]

## Step 8: check/warrant independently

\[
w_{t+1}\Vdash c_{t+1}.
\]

## Step 9: reconcile

\[
\mathsf{Pres}_{t+1}
=
Rec(
\mathsf{Pres}_t,
r_{t+1},
w_{t+1}
).
\]

## Step 10: compile/promote

If a repeatedly useful composite \(t\) can be safely promoted:

\[
m\doteq_{\mathcal H}t.
\]

## Step 11: recurse

Generate the next consequential open relation from \(\mathsf{Pres}_{t+1}\).

---

# 40. Acceptance fixtures for the operator-first rebind

Before the repository changes its normative semantic kernel, the new model should regenerate every protected existing capability.

At minimum:

## 40.1 Same endpoint, different path

Two paths:

\[
\pi_1,\pi_2
\]

have the same projected configuration but a protected context separates their composites.

Expected: quotient keeps the distinction.

## 40.2 Same counts, different order

Factorizations with the same multiset of steps but different order yield different protected continuation.

Expected: factorization/order residue preserved.

## 40.3 Quotient with successful descent

Two source processes are equivalent and every admitted continuation descends.

Expected: concrete retained state is executable.

## 40.4 Consequence sufficient but not executable

Current answers factor through q, but one continuation fails to descend.

Expected: do not call q executable state.

## 40.5 Learned separator

Existing probe set cannot distinguish candidates; an independently evaluated learned probe can.

Expected: add operator/probe generator only after admission.

## 40.6 Question as relation fiber

One relation schema produces forward, prerequisite, and inverse-completion questions merely by opening different ports.

Expected: no new question family implementation needed.

## 40.7 Generated question

A safely admitted relation schema compiles to current G3Q-style question execution.

Expected: candidate answer remains provisional.

## 40.8 Actualization

Semantic prediction differs from actual return.

Expected: raw return survives unchanged; mismatch cannot select its own repair.

## 40.9 Composite promotion

Long reasoning composite:

\[
t=f_n\circ\cdots\circ f_1
\]

is promoted to \(m\).

Expected:

\[
m\equiv_{\mathcal H}t
\]

and future execution cost decreases under a pinned metric.

## 40.10 Reopening

New protected context separates \(m\) from a detail hidden by its previous contract.

Expected: reopen factorization/residue; do not silently keep old equivalence.

## 40.11 Structural replacement

A rewrite binding uses:

\[
L\leftarrow K\rightarrow R.
\]

Expected: delete/preserve/create are distinguishable; departure does not imply arrival.

## 40.12 Self-improvement

Current presentation cannot express a consequential relation; candidate successor adds a generator or schema.

Expected: replacement only after preserve + gain + independent warrant.

## 40.13 Authority preservation

Event replay aggregate remains distinct from semantic process quotient.

Expected: no second source history or writable active semantics.

---

# 41. Proposed normative requirements

## OP-001 — Operators precede derived state

The semantic kernel MUST treat typed composable transformations as primitive relative to a binding. Configuration, history-state, probe, question, and retained-state roles MUST be derivable or binding-specific.

## OP-002 — Contextual comparison requires a shared frame

Direct protected equivalence MUST compare parallel terms or explicitly bridged terms.

## OP-003 — Question is an open relation

Every canonical question MUST identify one relation schema, a complete partition of its ports into bound and open positions, and the exact binding/scope/horizon under which the fiber is requested.

## OP-004 — Fully bound relation is not warrant

Completing every relation port creates a proposition/candidate claim only.

## OP-005 — Ask and Act remain separate

Semantic completion and actual environmental return MUST use separate transitions.

## OP-006 — No universal minimality without order

Terms such as “minimal,” “nearest,” “best,” or “least” MUST name the preorder/metric/cost structure that licenses them; otherwise preserve a nondominated frontier.

## OP-007 — Exact state requires operator descent

A consequence-sufficient quotient MUST NOT be called executable retained state unless its protected continuation operators descend.

## OP-008 — Promotion is compiled composition

Promoting a composite MUST record the defining composite, protected equivalence contract, operational gain, provenance, and reopening route.

## OP-009 — Relation semantics are not role labels

Question/claim family labels MAY remain for compatibility but MUST NOT determine formal semantics independently of the underlying relation schema.

## OP-010 — Operator acquisition is governed

A generated operator, relation schema, question, probe, or method MUST remain inert until independently admitted under its governing policy.

## OP-011 — Semantic unification does not merge authority roles

Theory, question, probe, representation, method, evidence, implementation, and authority failures MUST remain distinguishable in project governance even when represented using one operator/relation calculus.

## OP-012 — Self-improvement is ordinary successor inquiry

Changes to the operator/relation presentation MUST pass the same preserve + strict gain + independent warrant ratchet as other project successors.

## OP-013 — Relation syntax does not grant discharge authority

Every executable relation schema MUST declare whether its open ports are discharged by
pure derivation, provisional semantic generation, actual external return, independent
checking, or warrant policy. A lower-authority route MUST NOT fill a higher-authority port.


---

# 42. Revised canonical invariant

A bounded reasoner has access to represented transformations only through the consequences of their lawful compositions and to actuality only through independently constrained returns.

A binding supplies the interfaces, primitive operators, composition laws, consequence semantics, actualization channels, and validation mechanisms that make those relations meaningful.

A represented transformation acquires reasoning-significance only through differences that some admissible protected composition can expose.

Parallel transformations may therefore be identified exactly when every protected context gives the same consequence. Failure to find a separator with the currently tested contexts is only working nondistinction.

A question is a typed relation with one or more ports left open. A candidate answer fills those ports and thereby produces a fully bound proposition; it does not make that proposition true. Questions compose by shared typed ports and by continuation from one completion into another. If the present relation/operator language cannot express or fill a consequential open port, that failure becomes an inquiry into a new relation, operator, probe, method, representation, or binding.

Represented operators may be composed freely where typing permits, but generated composition is not actuality. Actual interaction crosses a separate boundary and produces an immutable raw return. Prediction precedes return when the return is used to test it. Interpretation, checking, warrant, and semantic promotion remain separate. The system may construct its own challenge but may not make acceptance of its candidate the authority that validates the challenge.

Realized succession is a factorization of actually realized transformations. A configuration is only a binding-specific view of that succession. A retained semantic state is a contextual quotient of realized/generated process; a concrete state encoding is executable only when every protected future operator descends to it. Thus state is a lawful fold of process precisely when the future process algebra still acts on the fold.

Repeated useful composites may be promoted into new operators when their protected consequences agree with the original composition and the promotion provides an independently demonstrated gain such as lower future cost. Their internal factorization may be occluded only under an explicit recovery/reopening contract. A new protected context that separates previously identified composites reopens the quotient.

Learning is warranted deformation of future compositional capacity. It may add a generator, add or remove an equation, learn a separator, import a native method through a valid bridge, promote a composite, refine an encoding, or rebind the interface/relation language. Memory is whatever retained compositional structure changes future protected competence or the cost of recovering it.

The current reasoning presentation, question language, method repertoire, representations, and implementation are themselves reifiable into a meta-binding. A successor replaces the incumbent only if every still-valid protected capability is preserved or explicitly disposed, at least one strict consequential gain is independently demonstrated, and positive warrant does not circle.

Therefore:

\[
\boxed{
\textbf{GENERATE BY COMPOSITION;
DISTINGUISH BY CONSEQUENCE;
ACTUALIZE THROUGH NOT-SELF;
CHANGE ONLY BY WARRANT;
COMPILE WHAT SURVIVES;
REOPEN WHAT NEW COMPOSITION DISTINGUISHES;
APPLY THE SAME RELATION TO THE REASONING SYSTEM ITSELF.}
}
\]

---

# 43. Smallest question language

If everything else is lost, retain:

\[
\boxed{
R\hookrightarrow X_1\times\cdots\times X_n
}
\]

\[
\boxed{
?_{I}R[\beta]
}
\]

\[
\boxed{
\operatorname{Fib}_{I}(R\mid\beta)
=
\{a_I:R[\beta\oplus a_I]\}
}
\]

and:

\[
\boxed{
CandidateAnswer
\to
FullyBoundProposition
\neq
Warrant.
}
\]

Then retain the standard relation basis:

\[
\boxed{
Type,\;
Comp,\;
Con,\;
Sep,\;
Eq_{\mathcal H},\;
Factor,\;
Desc,\;
Act,\;
\Vdash,\;
Pres,\;
Gain,\;
Succ,\;
Recover.
}
\]

Every ordinary question is generated by opening one or more ports of these or of a binding-native relation constructed from them.

---

# 44. Smallest generative reasoning language

Retain:

\[
\boxed{
\mathsf{Pres}_t
=
\langle
\mathsf G_t
\mid
\mathsf E_t
\rangle
}
\]

\[
\boxed{
\mathsf{Tm}_t
=
\operatorname{Free}(\mathsf G_t)
}
\]

\[
\boxed{
f\equiv_{\mathcal H}g
\iff
\forall K\in\mathcal H,\;
\operatorname{Con}_K(f)=\operatorname{Con}_K(g)
}
\]

\[
\boxed{
\mathfrak A_t(A,B)
=
\mathsf{Tm}_t(A,B)/{\equiv_{\mathcal H}}
}
\]

for each parallel interface pair \(A,B\).

and the actuality/warrant boundary:

\[
\boxed{
!_{\mathbb B}f\Downarrow r,
\qquad
r\to interpretation\to check\to warrant.
}
\]

Then self-improvement is:

\[
\boxed{
?_{\mathsf{Pres}'}
Succ_{\mathcal H}
(
\mathsf{Pres}',
\mathsf{Pres}_t
).
}
\]

This is sufficient to state the project's core generative objective without hard-coding a fixed question taxonomy.

---

# 45. Final implementation recommendation

Do not begin by changing the sealed baseline.

Use the project's recursive project-inquiry machinery to open one exact limitation:

> **The current semantic specification and implementation represent questions, probes, methods, retained state, and project successors through separate semantic forms even though their protected behavior may be regenerable from one typed operator/relation composition system.**

Construct a candidate operator-first rebind and test it against the acceptance fixtures in §40.

The candidate succeeds only if it can regenerate:

- current `core-v1`;
- G2B learned-probe admission;
- G3A-H exact quotient/continuation/reopening;
- G3Q generated-question admission/scheduling;
- G3G Goal derivation;
- G3R preserve/gain/warrant project succession;
- raw-return and warrant no-collapse;
- replay authority boundaries;

with **fewer universal semantic primitives and no stronger universal assumptions**.

If it fails, the breaker identifies the missing primitive.

If it succeeds, the next specification should be a genuine operator-first canonical rewrite rather than an appended amendment.

---

# Appendix A. Current repository correspondence ledger

## A.1 Question code

`src/rci/questions/catalog.py`

- The eight stable `core-v1` contracts remain compatibility renderings.
- Draft families become derived fibers of relation schemas.
- `LEARNED_RECURRENT_PROBE` becomes a particular admitted distinguishing operator question.

`src/rci/questions/models.py`

- `QuestionContract.input_roles` correspond to bound/open relation port roles.
- `output_claim_role` becomes a compatibility tag.
- templates remain inert prose rendering.
- `bind_answer` remains correct: answer creates only provisional claim.

`src/rci/questions/generated.py`

- `CompiledQuestionContract` is an existing safe compilation precedent.
- exact anchor/binding/scope/horizon/policy pins remain.
- generated question remains data-only and independently admitted.

## A.2 Claim code

`src/rci/claims/models.py`

- `Claim` remains.
- `Obligation` remains.
- `ClaimRole.UNKNOWN` should not be used in future relation semantics.
- `ObligationKind` becomes compatibility/scheduler classification rather than the complete ontology of inquiry.
- `CorrectionKind` already resembles a typed transformation vocabulary and remains append-only evidence.

## A.3 Probe code

`src/rci/probes/models.py`

- `ProbeIdentity` is already much closer to an operator identity than to a wording identity.
- `ProbeEvent` is an actualization/comparison episode.
- `ProbeTrace` preserves factorization/order where relevant.
- `PredictionSeal` and `Mismatch` remain untouched.
- `SemanticDelta` is warranted presentation change evidence.

## A.4 Learning code

`src/rci/learning/models.py`

- `RepresentationGap` becomes evidence for missing separator/operator/schema/binding.
- `LearnedProbeCandidate` is a candidate generator addition.
- `ProbeEvaluation` already checks nonredundancy and protected behavior.
- `ProbeAdmissionDecision` already realizes the operator admission ratchet.

## A.5 Compression code

`src/rci/compression/models.py`

- `CompressionContract` becomes a concrete quotient/encoding contract.
- `CompressionValidation` tests quotient/congruence properties.
- `ExactCompressionLicense` remains.
- `PathResidue` becomes omitted factorization.
- `RepresentationSuccessorDecision` remains the concrete representation ratchet.
- `RepresentationReopening` is exactly horizon/context-induced splitting.

## A.6 Formal code

`src/rci/formal/ast.py`

- keep as native Boolean/finite-enum binding.
- do not expand it into the universal question language.
- relation queries may compile into it when applicable.

## A.7 Project code

`src/rci/project/models.py`

- `CapabilityLimitation` is the project-level open consequential relation.
- `QuestionContractCandidate` is a relation-schema/query candidate.
- `MethodBindingCandidate` is operator acquisition through native precedent.
- `CapabilitySuccessorCandidate` and `CapabilityFrontier` remain partial-order successor machinery.
- `ImplementationGoalContract` is a sealed discriminator/actualization contract.
- G3G `ImplementationGoalCandidate` is a meta-level compiled operator output.
- project kind distinctions remain governance distinctions.

## A.8 Scheduler

`src/rci/orchestration/scheduler.py`

- keep deterministic bounded scheduler.
- feed it obligations generated from relation fibers.
- do not turn it into semantic authority or model-ranked planner.

---

# Appendix B. Current canonical notation migration ledger

| Current notation | Recommended disposition |
|---|---|
| \(B\) binding | rename \(\mathbb B\) |
| \(\mathsf{Ty}_B\) | replace with interfaces plus binding-native value sorts |
| \(R:X\rightsquigarrow Y\) | distinguish operator \(f:A\to B\) from relation schema \(R\hookrightarrow\prod X_i\) |
| `;` composition | use \(\circ\) canonically; adapters may translate |
| \(\chi=(P,g,\Gamma,\tau,\mathcal H,\mathcal R)\) | keep but rename scope/grain symbols if collisions arise |
| \(C[\square]\) | rename context \(K[-]\) |
| \(e[-]\) | treat as protected context/probe specialization |
| \(\operatorname{Con}_e(x)\) | generalize to \(\operatorname{Con}_K(f)\) |
| \(\equiv_{\mathcal H}\) | keep, on parallel terms |
| \(\operatorname{Sig}_{\mathcal H}\) | derived product representation; not primitive |
| \(\delta=(D_+,D_-)\) | demote to predicate/set binding |
| \(Q_t\subseteq P\) live region | replace with live relation fiber/candidate term set where possible |
| \(Q_\tau:\Sigma\rightsquigarrow Claim[\tau]\) | replace universal semantics with \(?_{I}R[\beta]\); retain as operational wrapper if useful |
| \(\partial^+Q\) | derive from fiber |
| \(\partial^-Q\) | derive from unresolved prerequisite/guard ports |
| \(a:X\rightsquigarrow X'\) | move to primitive operator |
| \(p=a_1;\cdots;a_n\) | use \(\pi\) and \(\operatorname{Comp}(\pi)\) |
| \(\partial^{in/out}\) | binding-derived crossing relations |
| \(\operatorname{Var}\) | derived operator family |
| \(\alpha_{L_X}(V)\) | predicate-binding construction only |
| \(!_B a\Downarrow r\) | keep, binding \(\mathbb B\) |
| \(\Pi_t\) | keep |
| \(NonSelfLicensing\) | keep |
| \(W_t=(V_t,E_t)\) | keep |
| \(Rec\) | keep as warrant-limited reconciliation |
| \(\mathsf{Hist}_B\) | compatibility carrier; semantically realized factorization |
| \(p_B\) configuration projection | keep binding-specific; rename to avoid probe/path collision |
| \(o\) probe | use \(p\) or named probe operator; probe is role |
| \(F_{o,r}\) | binding-specific return fiber |
| \(q_g\) higher-grain registration | reinterpret as quotient/promotion map |
| \(Ext(s)\) | derive from admitted outgoing operators from encoded state |
| \(q_{\mathcal H}\) retained map | split into \(\eta_{\mathcal H}\) semantic quotient + \(enc_{\mathcal H}\) encoding |
| \(S_{\mathcal H}^{min}\) | quotient carrier \(Q_{\mathcal H}\) |
| \(Suff_{\mathcal H}\) | keep |
| \(FD_{\mathcal H}\) | keep |
| \(\rho_a\) | binding-specific relation realization of operator |
| \(\bar\rho_a\) | descended operator |
| \(U\) | concrete deterministic descended update |
| \(L_X,L_H,L_S\) | predicate-language binding only |
| \(Use/Reconstruct/Evaluate/Reacquire\) | keep/index under `Recover` |
| \(\mathfrak C\) | keep |
| \(s_t\to s_{t+1}\) | state-value transition under fixed presentation |
| \(q_t\to q_{t+1}\) | generalize to presentation/representation update |
| \(\partial_q\) | use \(\partial_\eta\) for semantic quotient residue |
| \(R_t\) incumbent representation | generalize to \(\mathsf{Pres}_t\) when reasoning repertoire is object |
| \(\beta\) bridge | rename bridge \(\mathcal B\), reserve \(\beta\) for port binding |
| \(Res_G\) | keep goal-binding relation |
| \(Avail,Sel_W\) | keep |
| \(\square_a\) hole | merge into open port/context notation |
| \(Expressible(B)\) | generalize to expressible term/relation language of \(\mathbb B\) |
| \(G_t\) grammar/theory | replace/clarify as \(\mathsf{Pres}_t\) |
| \(K ::= Return\mid Step\) | rewrite Ask/Act split |
| `GoodAccept` | keep, apply to successor relation/operator/presentation |

---

# Appendix C. A compact question compiler table

| Formal relation | Fully bound statement | Open-port question |
|---|---|---|
| \(Type(f,A,B)\) | “f maps A to B.” | “What maps A to B?” |
| \(Comp(f,g,h)\) | “g after f equals h.” | “What follows f to yield h?” / “What does g after f yield?” |
| \(Con(K,f,y)\) | “f has consequence y in K.” | “What consequence?” / “What context?” / “What transform?” |
| \(Sep(K,f,g)\) | “K separates f and g.” | “What separates f and g?” |
| \(Eq_H(f,g)\) | “f and g are H-equivalent.” | “What is equivalent to f under H?” |
| \(Factor(e,q,\bar e)\) | “e factors through q by readout \bar e.” | “What q preserves e?” / “What readout?” |
| \(Desc(q,a,\bar a)\) | “a descends through q as \bar a.” | “What compiled operator realizes a?” |
| \(Act_B(f,r)\) | “actualizing f returned r.” | “What did f actually return?” |
| \(w\Vdash c\) | “w warrants c.” | “What warrants c?” / “What does w warrant?” |
| \(Pres(R',R)\) | “R' preserves R.” | “What successor preserves R?” |
| \(Gain(R',R,g)\) | “R' gains g over R.” | “What gain does R' add?” |
| \(Succ(R',R)\) | “R' is a warranted strict successor of R.” | “What successor should replace R?” |
| \(Recover_{\mu}(m,c,k)\) | “m supports recovery mode μ for k in c.” | “What can recover k?” / “Which recovery mode works?” |

---

# Appendix D. Canonical prose discipline

Every formal definition in the next canonical document should satisfy:

1. **Type sentence** — what mathematical kind of thing the notation denotes.
2. **Definition sentence** — exact condition under which the relation holds.
3. **Contrast sentence** — nearest symbols/relations it must not be confused with.
4. **Composition sentence** — what it may legally compose with.
5. **Consequence sentence** — what downstream reasoning operation depends on it.
6. **Question sentence** — the canonical open-port question generated from it.
7. **Implementation sentence** — whether the relation is kernel, binding-specific, derived, or repository-only.
8. **Breaker sentence** — what observation would prove the definition insufficient.

A symbol that cannot satisfy these eight sentences has not earned canonical status.

---

# Appendix E. Source audit basis

The reconstruction above was checked against these live repository surfaces:

- `RCI_Project_Spec.tex` v0.5;
- `PLAN.md`;
- `AGENTS.md`;
- `docs/architecture.md`;
- `docs/requirements-matrix.md`;
- `docs/goals/G3R.md`;
- `docs/goals/G3Q.md`;
- `docs/goals/G3G.md`;
- `src/rci/claims/models.py`;
- `src/rci/questions/models.py`;
- `src/rci/questions/catalog.py`;
- `src/rci/questions/generated.py`;
- `src/rci/orchestration/scheduler.py`;
- `src/rci/probes/models.py`;
- `src/rci/learning/models.py`;
- `src/rci/compression/models.py`;
- `src/rci/formal/ast.py`;
- `src/rci/project/models.py`;
- `src/rci/project/selection.py`.

The uploaded canonical document was also audited section-by-section and its displayed mathematical notation was extracted across the full file. The reconstruction deliberately preserves the repository's sealed authority/evidence semantics while changing the proposed semantic center from state/carrier-first to operator/composition-first.

