# RCI 0.3 Repair Delta

This is what must change in the current integrated 0.3. It is a repair of 0.3, not a replacement of its question/perception/reconstruction architecture.

The repairs reduce to four coupled migrations:

[
\boxed{
\begin{array}{ll}
\textbf{A. SUPPORT/WARRANT} &
g,\Gamma,\text{DAG}
;\longrightarrow;
Applicability,\ MinSupp,\partial^{-},\mathcal W,\text{ancestry}
[2mm]
\textbf{B. RETURN} &
Query\to Return\to Result
;\longrightarrow;
Attempt\to Outcome\to ExternalReturn\to Decode\to Result
[2mm]
\textbf{C. RETENTION} &
\text{remove/merge}
;\longrightarrow;
\text{compress + residue + regeneration + reopening}
[2mm]
\textbf{D. STATE OWNERSHIP} &
\text{duplicated state}
;\longrightarrow;
\text{one authoritative owner + derived working views}.
\end{array}}
]

The (\Diamond/\Box) composition equations in §6 must **not** be changed: they are already correct under 0.3's definition of relational composition. 

---

## 1. Replace the learned-lemma representation

### Current 0.3

A learned lemma is effectively:

[
\lambda=(g,\ell,\sigma,w,\Gamma,\pi)
]

with one activation guard (g), one dependency set (\Gamma), and a certificate/provenance object (\pi). 

This must change.

A single guard is allowed to remain as an **applicability condition**, but it must no longer stand in for the epistemic support structure of the lemma.

### Replace with

[
\boxed{
\lambda
=======

(
\ell,
\sigma,
a,
\mathsf{Supp},
\partial^-,
w,
\Pi,
prov,
pred
)
}
]

where:

* (\ell): retained relation;
* (\sigma): scope;
* (a): applicability condition independent of evidential support;
* (\mathsf{Supp}): minimal support environments;
* (\partial^-): open dependency boundary;
* (w): warrant class;
* (\Pi): proof/certificate references;
* (prov): provenance;
* (pred): optional predecessor version.

In implementation form:

```text
WarrantedLemma {
    id
    relation

    scope
    applicability

    support_environments[]
    open_dependency_boundary[]

    warrant_class
    certificate_refs[]
    provenance_refs[]
    source_claim_ids[]

    predecessor_version?
}
```

This replaces the present `guard` + `dependencies[]` structure in `WarrantedLemma`. 

---

# 2. Introduce explicit support environments

A retained relation may have multiple independent routes by which it stands.

For example:

[
a\Rightarrow\ell
]

and independently:

[
b\Rightarrow\ell.
]

The support representation must retain:

[
\boxed{
\mathsf{Supp}(\lambda)
======================

\operatorname{Min}_{\subseteq}
{
E_1,E_2,\ldots
}.
}
]

For the example:

[
\mathsf{Supp}(\ell)
===================

{
{a},
{b}
}.
]

This is an antichain of minimal support environments.

Do not flatten it into:

[
a\lor b
]

even when the guard language could represent that extensionally, because the separate environments are needed for:

* dependency exposure;
* selective deactivation;
* nogood propagation;
* repair;
* provenance;
* reopening;
* alternate-route inquiry.

The repair set correctly identifies this as the mechanism missing behind current §31's simple guard-deactivation rule. 

---

# 3. Add the open dependency boundary (\partial^-)

This is the central warrant repair.

For a candidate or retained relation (\lambda) under support environment (E), define:

[
\boxed{
\partial^-_E\lambda
===================

{
d:
d
\text{ is required for }\lambda
\text{ but is neither supplied by }E
\text{ nor independently discharged}
}.
}
]

Then define:

[
\boxed{
Closed_E(\lambda)
\iff
Consistent(E)
\land
\partial^-_E\lambda=\varnothing
\land
Check(\Pi,E)=\top.
}
]

A conditional relation may be warranted when:

[
\boxed{
Warranted(\lambda)
\iff
\exists E\in\mathsf{Supp}(\lambda):
Closed_E(\lambda).
}
]

The important distinction is:

[
\boxed{
\text{assumption in declared support environment}
\neq
\text{undischarged hidden dependency}.
}
]

Conditional knowledge is not required to depend on nothing.

It is required to expose what it depends on.

---

# 4. Replace warrant acyclicity as the definition of sound warrant

### Remove

Current §32 says:

[
Parents(w_{t+1})\subseteq V(W_t)
]

and concludes:

> Positive warrant may not depend on itself. Control may recurse. Warrant may not circle. 

Current Invariant VII likewise says:

> Positive warrant remains acyclic. 

Those formulations must be replaced.

Acyclicity is not sufficient:

[
A\text{ unresolved},
\qquad
A\Rightarrow B
]

is acyclic but does not warrant (B) unconditionally.

And a valid proof certificate can contain cycles if an independently trusted proof discipline establishes its cyclic soundness.

### New warrant law

[
\boxed{
\textbf{
EVERY RETAINED HARD RELATION MUST EXPOSE ITS SUPPORT
AND HAVE NO UNACCOUNTED OPEN DEPENDENCY.
}}
]

And:

[
\boxed{
\textbf{
A DEPENDENCY RECURRENCE MAY NOT DISCHARGE ITSELF
MERELY BY RECURRING.
}}
]

This is the actual anti-self-licensing invariant.

---

# 5. Do not eliminate all acyclicity

Three structures must now be explicitly distinguished:

[
\boxed{
\text{proof/certificate structure}
\neq
\text{epistemic support structure}
\neq
\text{historical ancestry}.
}
]

A proof certificate may be cyclic.

Support relations may contain recursive relations without those cycles supplying their own warrant.

But successor/version ancestry should remain acyclic:

[
\lambda_0
\prec
\lambda_1
\prec
\lambda_2.
]

Therefore preserve:

[
\boxed{
\text{acyclic authoritative succession}
}
]

while removing:

[
\boxed{
\text{all warrant/proof structure must be a DAG}.
}
]

The stronger law becomes:

[
\boxed{
\textbf{
SUPPORT MAY RECUR;
RECURRENCE MAY NOT SELF-DISCHARGE;
AUTHORITATIVE SUCCESSION PRESERVES ACYCLIC ANCESTRY.
}}
]

---

# 6. Introduce a proper warrant/support structure

Replace `W_t: warrant DAG` everywhere with something like:

[
\boxed{
\mathcal W_t
============

(
J_t,
S_t,
N_t,
C_t
)
}
]

where:

* (J_t): justification relations;
* (S_t): minimal support environments;
* (N_t): nogoods/incompatible environments;
* (C_t): certificate/checking relations.

Historical version/provenance ancestry remains separately retained.

So controller responsibilities change from:

> maintain guard and warrant graph 

to:

```text
maintain support environments
maintain open dependency boundaries
maintain nogoods
maintain justification relations
maintain certificate references
maintain authoritative ancestry
```

---

# 7. Rewrite activation semantics

### Current

[
\Theta_t^\gamma
===============

{\ell_i:\gamma\models g_i}.
]



### Replace with

[
\boxed{
Active_\gamma(\lambda)
\iff
Applicable_\gamma(\lambda)
\land
\exists E\in MinSupp(\lambda):
Standing_\gamma(E).
}
]

This separates:

1. whether the relation applies in the present domain/context;
2. whether one warranted support route currently stands.

Do **not** put all of:

* scope;
* context;
* grain;
* time;
* binding applicability;
* assumption support

into the same ATMS environment.

They are different relations.

---

# 8. Rewrite reopening semantics

Current wording:

> reopening is guard deactivation, not epistemic amnesia. 

is now too narrow.

Replace it with:

[
\boxed{
\textbf{
REOPENING IS LOSS OR CHANGE OF CURRENT APPLICABILITY,
SUPPORT, OR COMPRESSION LICENCE;
IT IS NOT DELETION OF PRIOR WARRANT.
}}
]

A lemma can become inactive because:

* applicability ceases;
* all currently standing support environments fail;
* a support environment becomes a nogood;
* its scope no longer includes the present context;
* a compressed distinction's reopening condition fires;
* a successor representation splits its former equivalence class.

The historical object remains.

---

# 9. Rewrite the promotion law

### Current

[
Promote(c,\pi)=\lambda
]

when:

[
Check(\pi)=\top.
]



That is insufficient.

### Replace with

[
\boxed{
Promote(c,\Pi,E)=\lambda
}
]

only when:

[
\boxed{
Consistent(E)
\land
\partial^-_E(c)=\varnothing
\land
Check(\Pi,E)=\top.
}
]

Promotion must record:

* relation;
* scope;
* applicability;
* minimal support environment;
* open-boundary closure;
* warrant class;
* certificate;
* provenance.

A checked certificate cannot silently close dependencies that the certificate does not actually discharge.

---

# 10. Separate current semantic memory from semantic history

Current 0.3 declares:

[
\Theta_{t+1}
============

\Theta_t\cup{\lambda}
]

and calls this the monotone ratchet. 

That conflicts with the later versioned reconsolidation machinery, where retained relations can be challenged and receive successor versions while the predecessor remains historical. 

Replace this with two objects.

### Current warranted semantic representation

[
M_S^t
]

may:

* gain;
* weaken;
* split;
* merge;
* supersede;
* deactivate;
* rebind;
* compress;
* reopen.

Therefore:

[
M_S^t
\not\subseteq
M_S^{t+1}
]

in general.

### Authoritative semantic history

[
H_{\le t}^{sem}
]

is append-only:

[
\boxed{
H_{\le t}^{sem}
\subseteq
H_{\le t+1}^{sem}.
}
]

The new monotonicity law is:

[
\boxed{
\textbf{
THE ACTIVE REPRESENTATION IS NOT MONOTONIC;
AUTHORITATIVE REPRESENTATION HISTORY IS.
}}
]

This is the proper repair to §30 and §119. The same conclusion is identified in the repair audit. 

---

# 11. Rewrite compression §119 to carry residue

Current §119 only says a distinction may be removed when protected consequence, transition, and control semantics remain preserved. 

That is no longer sufficient for 0.3.

Compression must produce:

[
\boxed{
Compress(S)
\longrightarrow
(K,r)
}
]

where:

* (K): compressed active representation;
* (r): residual/reopening package.

Require at least:

[
\boxed{
r=
(
regen,
\rho,
\partial^-,
prov,
debt,
fallback
).
}
]

Compression must preserve:

1. protected consequence;
2. protected transition semantics;
3. protected control semantics;
4. reconstruction of protected continuation;
5. open dependency residue;
6. authoritative ancestry;
7. reopening conditions.

---

# 12. Add the dependency-residue transition law

For any semantic/representational transition:

[
\Sigma_t
\xrightarrow{\Delta}
\Sigma_{t+1},
]

require:

[
\boxed{
\partial^-_{t+1}
================

Transport_\Delta
\left(
\partial^-*t
\setminus
Discharged*\Delta
\setminus
ClosedIrrelevant_\Delta
\right)
\cup
NewOpen_\Delta.
}
]

An open dependency may leave active representation only if it is:

### Discharged

Independent warrant closes it.

### Closed as consequence-null

Its current irrelevance is actually established under a protected horizon, and a reopening condition is retained.

### Transported

The dependency survives in a successor representation or obligation.

Never:

[
\boxed{
\text{representation changed}
\Rightarrow
\text{dependency disappeared}.
}
]

This is the most important addition to compression/rebind safety.

---

# 13. Preserve the current (\Diamond/\Box) equations

No repair.

Keep:

[
\boxed{
\Diamond_{S\circ R}
===================

\Diamond_R\circ\Diamond_S
}
]

and:

[
\boxed{
\Box_{S\circ R}
===============

\Box_R\circ\Box_S.
}
]

They are correct for the current relation convention. 

If there is a separate theorem asserting naïve composition of:

[
Must_R(Q)
=========

Dom(R)\cap\Box_R(Q),
]

that theorem should be checked independently because executability/domain conditions make `Must` composition subtler.

But Fix 03 as described must not alter §6.

---

# 14. Replace the backend execution lifecycle

Current generic backend architecture is:

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



This bypasses the immutable `ExternalReturn` object that 0.3 separately defines. 

Replace it with:

[
\boxed{
Plan_e(O)\to AttemptPlan_e
}
]

[
\boxed{
Encode_e(O,AttemptPlan_e)\to Query_e
}
]

[
\boxed{
Attempt_e(AttemptPlan_e,Query_e)\to AttemptOutcome_e
}
]

then, only when an external return actually exists:

[
\boxed{
AttemptOutcome_e
================

RETURNED(r)
\Rightarrow
r:ExternalReturn_e.
}
]

Then:

[
\boxed{
Decode_e(ExternalReturn_e)\to DecodedResult_e
}
]

and:

[
\boxed{
Check_e(ExternalReturn_e,DecodedResult_e)
\to WarrantStatus.
}
]

The raw return is therefore structurally unavoidable.

---

# 15. Add `AttemptOutcome`

Do not use one `Unknown` value for failures at different stages.

Define:

```text
AttemptOutcome :=
    NO_ATTEMPT(reason)

  | NOT_PRESENTED(
        attempt_id,
        route_id,
        reason
    )

  | CAPTURE_FAILED(
        attempt_id,
        route_id,
        diagnostics
    )

  | RETURNED(
        external_return_id
    )
```

These must remain distinct:

[
\boxed{
\text{no attempt}
\neq
\text{not presented}
\neq
\text{capture failed}
\neq
\text{returned null}
\neq
\text{semantic unknown}.
}
]

`Unknown` remains legal as an **epistemic result**. Current 0.3 rightly protects unknown as a possible conclusion when inquiry cannot distinguish something. 

What changes is that `Unknown` must cease to be overloaded as transport/execution/capture status.

---

# 16. Add `ReturnRoute`

Current `ExternalReturn` has only:

```text
source
raw_payload
source_revision
```

plus its attempt ID. 

Add a route object:

```text
ReturnRoute {
    id

    backend_id
    adapter_id
    adapter_version?

    endpoint_or_channel?
    transport?
    execution_environment?

    request_or_action_identity
    transforms[]

    source_identity?
}
```

Then:

```text
ExternalReturn {
    id

    attempt_id
    route_id

    source_id?
    source_revision?

    raw_payload
    captured_at

    immutable: true
}
```

The distinction is:

[
\boxed{
\text{what source was addressed}
\neq
\text{what route produced this captured return}.
}
]

Warrant must be able to inspect that route.

---

# 17. Split raw return from decoded semantic result

Replace the current generic `Result` object with an explicitly interpreted object:

```text
DecodedResult {
    id

    external_return_id
    decoder_id
    decoder_version?

    kind
    proposition_or_relation

    scope
    interpreted_assumptions[]

    witness_or_certificate?
}
```

The key relation becomes:

[
\boxed{
ExternalReturn
\neq
DecodedResult.
}
]

A bad decoder therefore cannot mutate or replace the actuality it interpreted.

This strengthens 0.3's existing invariant:

[
ExternalReturn
\neq
Interpretation(ExternalReturn).
]



---

# 18. Keep semantic result types, but move them to the decode layer

Current return taxonomy contains:

* Witness;
* Counterexample;
* Separator;
* EquivalenceCertificate;
* Conflict;
* Prerequisite;
* ReachabilityWitness;
* UnreachabilityCertificate;
* Success;
* Failure;
* Unknown. 

These should no longer be called canonical **external return types**.

They are canonical **decoded epistemic/result roles**.

So rename §114 accordingly.

The actual environment may return:

* bytes;
* text;
* JSON;
* numeric vector;
* empty payload;
* process exit status;
* sensor sample;
* proof object;
* null;
* arbitrary native result.

Only the decoder assigns:

[
Witness,\ Counterexample,\ Success,\ldots
]

---

# 19. Rework `Mismatch`

`Mismatch` should reference actual returned material only when an actual return exists.

Keep:

```text
Mismatch {
    prediction_id
    actual_return_id
    difference_claim_id
    protected_consequence_changed
    classification
}
```

for returned outcomes.

For:

* `NOT_PRESENTED`;
* `CAPTURE_FAILED`;

record an attempt/protocol failure, not a fake prediction mismatch against an imagined return.

A prediction may separately include expectations about whether a return should be produced, but those are different claims.

---

# 20. Separate authoritative state from derived working state

Current runtime state contains seventeen top-level entries including:

* (\mathcal P_t);
* (\mathcal F_t);
* (\rho_t);
* (\Theta_t);
* (\mathcal M_t=(M_E,M_S,M_P,M_L));

even though those objects partly duplicate one another. 

`InquiryState` repeats the same duplication in implementation form. 

Replace this with the rule:

[
\boxed{
\textbf{
EVERY SEMANTIC OBJECT HAS ONE AUTHORITATIVE OWNER.
OTHER OCCURRENCES ARE REFERENCES OR REGENERABLE VIEWS.
}}
]

---

# 21. Make memory stores authoritative

Use:

[
\boxed{
\mathcal M_t
============

(
M_E^t,
M_S^t,
M_P^t,
M_L^t
).
}
]

Then define:

### Semantic theory

[
\boxed{
\Theta_t:=SemanticView(M_S^t).
}
]

Do not store a separate authoritative (\Theta_t).

### Probe state

[
\boxed{
\mathcal P_t
:=
ProbeView(M_E^t,M_P^t).
}
]

Because:

* probe contracts/procedures belong in procedural memory;
* probe events/traces belong in episodic memory.

So:

[
\mathcal P_t\neq M_P^t.
]

### Reopening state

[
\boxed{
\rho_t
:=
ReopenView(M_L^t,\gamma_t,\Phi_t).
}
]

Do not independently maintain reopening predicates in two stores.

The repair analysis correctly identifies this ownership problem and the required `ProbeView` distinction. 

---

# 22. Make working context explicitly derived

0.3 already says:

[
\gamma_t
========

Reconstruct(\mathcal M_t,c_t,\Phi_t,K_t).
]



Follow that through consistently.

Treat:

[
\gamma_t
]

as reconstructed working context, not separately authoritative state.

Likewise:

[
\mathcal F_t
============

BuildField(
\gamma_t,
q_t,
\Phi_t,
\mathcal P_t,
\rho_t,\ldots
).
]

And:

[
\mu_t
=====

Schedule(
\mathcal O_t,
\gamma_t,
\mathcal F_t,\ldots
).
]

These are runtime views.

---

# 23. Replace the canonical state tuple

Use an authoritative state approximately of the form:

[
\boxed{
\Sigma_t^{auth}
===============

(
\mathfrak B,
\Phi_t,
B_t,
\alpha_t,
\widehat R_t,
\mathcal C_t,
\mathcal O_t,
\mathcal W_t,
\mathcal M_t,
\Pi_t,
\mathcal A_t,
H_t^{auth}
).
}
]

Where:

* (\mathfrak B): binding;
* (\Phi_t): protected consequence profile;
* (B_t): active distinction basis;
* (\alpha_t): abstraction;
* (\widehat R_t): abstract transition structure;
* (\mathcal C_t): candidate graph;
* (\mathcal O_t): obligations;
* (\mathcal W_t): support/warrant structure;
* (\mathcal M_t): memory stores;
* (\Pi_t): predictions/mismatches;
* (\mathcal A_t): attempts/routes/returns/reconstruction/deltas;
* (H_t^{auth}): append-only authoritative version/provenance ancestry.

Then reconstruct:

[
\boxed{
\Sigma_t^{work}
===============

(
\gamma_t,
\mathcal F_t,
\Theta_t,
\mathcal P_t,
\rho_t,
\mu_t
)
}
]

from authoritative state.

The exact tuple count is unimportant.

The ownership distinction is important.

---

# 24. Update the intermediate abstract-transition state

Current intermediate state stores both:

[
\mathcal P_t,\Theta_t,W_t
]

directly. 

Either:

1. explicitly declare (\mathcal I_t) a **derived materialized view**, or
2. replace those fields with references to authoritative memory/warrant owners.

Do not maintain an independent semantic truth store inside the abstract-transition system.

---

# 25. Update the formal controller responsibilities

Current controller says:

> maintain guard and warrant graph. 

Replace with:

```text
maintain support environments
maintain support minimality
maintain nogoods
maintain open dependency boundaries
maintain certificate/proof references
maintain authoritative ancestry
maintain obligations generated by open dependencies
maintain derived activation views
```

It must also prevent:

```text
dependency vanished from active representation
```

from being interpreted as:

```text
dependency discharged
```

---

# 26. Extend the prediction/attempt manager

Current Layer 2B already preserves prediction seals, attempts, and raw returns. 

Extend it to own:

```text
AttemptPlan
VariationAttempt
AttemptOutcome
ReturnRoute
ExternalReturn
Mismatch
```

Its lifecycle becomes:

```text
PLAN
→ SEAL
→ ATTEMPT
→ OUTCOME
→ [EXTERNAL RETURN if returned]
→ DECODE
→ RECONSTRUCT
```

Not:

```text
RUN
→ RESULT
```

---

# 27. Let open dependencies generate inquiry

This is an architectural gain, not just bookkeeping.

Given:

[
\partial^-\lambda
=================

{d_1,\ldots,d_n},
]

the scheduler can ask:

[
\boxed{
\text{Which open dependency would most consequentially change
whether a support environment closes?}
}
]

Then select a probe/method capable of discriminating that dependency.

Thus:

[
\boxed{
\partial^-
\to
Obligation
\to
Question
\to
Probe
\to
Return
\to
SupportClosure.
}
]

This should be added explicitly to obligation generation and scheduling.

---

# 28. Update the main runtime algorithm

The repaired main loop should become:

[
\boxed{
\begin{array}{c}
\textbf{RECONSTRUCT WORKING STATE}\
\downarrow\
\textbf{SELECT LIVE OBLIGATION OR OPEN DEPENDENCY}\
\downarrow\
\textbf{SELECT/REUSE PROBE OR ACTION}\
\downarrow\
\textbf{PLAN + SEAL}\
\downarrow\
\textbf{ATTEMPT}\
\downarrow\
\textbf{CLASSIFY ATTEMPT OUTCOME}\
\downarrow\
\textbf{PRESERVE EXTERNAL RETURN, IF ANY}\
\downarrow\
\textbf{DECODE / INTERPRET}\
\downarrow\
\textbf{COMPARE WITH PREDICTION + PROBE HISTORY}\
\downarrow\
\textbf{RECONSTRUCT CANDIDATE SUCCESSOR}\
\downarrow\
\textbf{STRETCH / SQUEEZE / ATTACK}\
\downarrow\
\textbf{COMPUTE SUPPORT + OPEN DEPENDENCY BOUNDARY}\
\downarrow\
\textbf{DISCHARGE / WARRANT}\
\downarrow\
\textbf{VERSION / LEARN}\
\downarrow\
\textbf{COMPRESS WITH RESIDUE}\
\downarrow\
\textbf{RECONSTRUCT NEXT WORKING STATE}\
\circlearrowleft
\end{array}
}
]

The important change is that a return is no longer allowed to jump straight from backend execution to semantic update.

---

# 29. Replace System Invariant III

### Current

> Every retained hard relation has guard, scope, dependencies, warrant. 

### Replace with

[
\boxed{
\textbf{
EVERY RETAINED HARD RELATION HAS EXPLICIT APPLICABILITY,
MINIMAL SUPPORT ENVIRONMENTS,
OPEN-DEPENDENCY STATUS,
SCOPE, WARRANT, AND PROVENANCE.
}}
]

---

# 30. Replace System Invariant VII

### Delete

> Positive warrant remains acyclic. 

### Replace with

[
\boxed{
\textbf{
NO CLAIM OR SUPPORT RECURRENCE MAY SUPPLY THE UNDISCHARGED
EPISTEMIC SUPPORT REQUIRED FOR ITS OWN ACCEPTANCE.
}}
]

and:

[
\boxed{
\textbf{
ALL UNACCOUNTED DEPENDENCIES OF A RETAINED HARD RELATION
REMAIN EXPOSED.
}}
]

Add separately:

[
\boxed{
\textbf{
AUTHORITATIVE VERSION ANCESTRY IS ACYCLIC AND APPEND-ONLY.
}}
]

---

# 31. Strengthen the compression invariant

Current Invariant VI only protects consequence/transition/control-visible distinctions. 

Add:

[
\boxed{
\textbf{
COMPRESSION MAY NOT ERASE AN OPEN DEPENDENCY, WARRANT ROUTE,
AUTHORITATIVE ANCESTRY, OR REOPENING CONDITION.
}}
]

---

# 32. Add return-lifecycle invariants

Add:

[
\boxed{
NO_ATTEMPT
\neq
NOT_PRESENTED
\neq
CAPTURE_FAILED
\neq
RETURNED(NULL)
\neq
UNKNOWN.
}
]

Add:

[
\boxed{
ExternalReturn
\neq
DecodedResult
\neq
Warrant.
}
]

Add:

[
\boxed{
\textbf{
EVERY EXTERNAL RETURN RETAINS THE ROUTE BY WHICH IT ENTERED THE SYSTEM.
}}
]

---

# 33. Add state-ownership invariant

[
\boxed{
\textbf{
NO SEMANTIC OBJECT HAS TWO INDEPENDENT AUTHORITATIVE STORES.
}}
]

Derived views may be cached.

They must be regenerable from their authoritative owners.

---

# 34. Update reconsolidation

Current 0.3 already correctly says:

[
\lambda_t
\to
Challenge
\to
MemoryPatchCandidate
\to
Warrant
\to
\lambda_{t+1}.
]



Keep this.

But require successor construction to transport:

[
\partial^-_{\lambda_t}
]

into:

[
\partial^-*{\lambda*{t+1}}
]

unless each disappearing dependency is explicitly discharged or licensed irrelevant.

Also retain:

[
pred(\lambda_{t+1})=\lambda_t.
]

---

# 35. Update semantic consolidation

Keep 0.3's:

[
M_E
\xrightarrow{Consolidate}
Claim[Generalization]
\xrightarrow{Attack+Warrant}
M_S.
]



But every proposed generalization must now construct:

* candidate support environments;
* open dependency boundary;
* applicability;
* scope;
* challenge obligations.

A generalization cannot be promoted merely because its certificate checks if hidden dependencies remain.

---

# 36. Do not globally eliminate the word `guard`

This is important.

The repair affects the use of a **single guard as the epistemic support representation of a learned lemma**.

Other guards remain legitimate:

* probe applicability guards;
* scope guards;
* temporal guards;
* comparison guards;
* reopening guards;
* native backend applicability conditions.

0.3 uses guards for several such purposes. 

So do not perform a blind textual replacement of every `guard`.

The distinction should become:

[
\boxed{
\text{applicability guard}
\neq
\text{support environment}.
}
]

---

# 37. Update terminology throughout the document

Global replacements required:

### Replace

`warrant DAG`

with:

`warrant/support structure`

except where discussing the obsolete 0.3 mechanism historically.

### Replace

`Positive warrant remains acyclic`

with the new support-closure / no-self-discharge invariant.

### Replace

`guard and warrant graph`

with:

`support environments, open dependencies, nogoods, certificates, and ancestry`.

### Replace

`warranted guarded relation`

where it means evidential support with:

`conditionally warranted relation with explicit support`.

Do not replace ordinary applicability/reopening uses of “guard.”

### Replace

`Theta/MS`

dual-authority language with one canonical semantic store:

[
M_S
]

and use (\Theta) only as a mathematical view if useful.

### Replace

“return type” for Witness/Counterexample/etc.

with:

“decoded semantic result type.”

---

# 38. Required acceptance fixtures

Add these as blocking conformance tests:

```text
ACYCLIC_UNDISCHARGED_DEPENDENCY_IS_NOT_UNCONDITIONAL_WARRANT

RAW_SUPPORT_CYCLE_DOES_NOT_SELF_DISCHARGE

CHECKED_CYCLIC_CERTIFICATE_MAY_DISCHARGE_WHEN_ITS_PROOF_DISCIPLINE_LICENSES_IT

ALTERNATE_SUPPORT_ENVIRONMENT_SURVIVES_DEACTIVATION

NOGOOD_REMOVES_ONLY_AFFECTED_SUPPORT_ENVIRONMENTS

OPEN_DEPENDENCY_GENERATES_OBLIGATION

OPEN_DEPENDENCY_SURVIVES_COMPRESSION

OPEN_DEPENDENCY_SURVIVES_REBIND_UNLESS_DISCHARGED_OR_TRANSPORTED

ACTIVE_REPRESENTATION_MAY_REVISE_WHILE_HISTORY_REMAINS_APPEND_ONLY

DIAMOND_COMPOSITION_REMAINS_REVERSE_ORDER

BOX_COMPOSITION_REMAINS_REVERSE_ORDER

NO_ATTEMPT_IS_NOT_NULL_RETURN

NOT_PRESENTED_IS_NOT_NULL_RETURN

CAPTURE_FAILURE_IS_NOT_NULL_RETURN

NULL_PAYLOAD_CAN_BE_AN_ACTUAL_EXTERNAL_RETURN

RETURN_ROUTE_IS_PRESERVED

EXTERNAL_RETURN_IS_NOT_DECODED_RESULT

DECODED_RESULT_IS_NOT_WARRANT

SEMANTIC_MEMORY_HAS_ONE_AUTHORITY

PROBE_VIEW_REBUILDS_FROM_EPISODIC_AND_PROCEDURAL_MEMORY

REOPEN_VIEW_REBUILDS_FROM_LATENT_MEMORY

WORKING_CONTEXT_REBUILDS_FROM_AUTHORITATIVE_STATE

COMPRESSION_RETURNS_REGENERATION_AND_REOPENING_RESIDUE

COMPRESSED_DEPENDENCY_CANNOT_DISAPPEAR_WITHOUT_DISPOSITION
```

These extend the fixture set already proposed in the repair audit. 

---

# 39. What does **not** change from 0.3

The repair should not destabilize the parts that are already correct.

Keep:

* question → provisional claim rather than fact;
* recurrent probe identity;
* ordered probe traces;
* fresh observation before comparison where possible;
* perception as provisional;
* (A/U/I) relevance partition;
* relational retrieval;
* prediction sealing;
* pattern separation/completion;
* reconstructive memory;
* episodic versus semantic learning;
* versioned reconsolidation;
* representation gaps;
* learned probes;
* self-cleaning;
* stretch/squeeze;
* necessity/sufficiency/prerequisite attack;
* native methods/backends;
* protected-consequence-relative abstraction;
* `Unknown` as a legitimate epistemic status;
* (\Diamond/\Box) composition exactly as presently written.

The cognition architecture already establishes most of those mechanisms correctly.  

---

# 40. The repaired architecture in one picture

The important change to 0.3 is:

[
\boxed{
\begin{array}{c}
\textbf{AUTHORITATIVE RETAINED STATE}\
M_E,\ M_S,\ M_P,\ M_L,\ \mathcal W,\ Hist,\ldots\
\downarrow\
\textbf{RECONSTRUCT WORKING STATE}\
\gamma,\mathcal F,\Theta,\mathcal P,\rho\
\downarrow\
\textbf{OPEN OBLIGATION / }\partial^-\
\downarrow\
\textbf{QUESTION / PROBE / ACTION}\
\downarrow\
\textbf{SEALED PLAN / PREDICTION}\
\downarrow\
\textbf{ATTEMPT}\
\downarrow\
\textbf{ATTEMPT OUTCOME}\
\downarrow\
\textbf{EXTERNAL RETURN IF ACTUALLY RETURNED}\
\downarrow\
\textbf{DECODED INTERPRETATION}\
\downarrow\
\textbf{COMPARE / ATTACK / RECONSTRUCT}\
\downarrow\
\textbf{SUPPORT ENVIRONMENTS + OPEN DEPENDENCY}\
\downarrow\
\textbf{INDEPENDENT WARRANT}\
\downarrow\
\textbf{VERSIONED SEMANTIC UPDATE}\
\downarrow\
\textbf{COMPRESSION WITH RESIDUE}\
\downarrow\
\textbf{AUTHORITATIVE HISTORY APPEND}\
\downarrow\
\textbf{RECONSTRUCT AGAIN}.
\end{array}}
]

And the repaired governing laws become:

[
\boxed{
\begin{aligned}
&\textbf{Questions create claims, not facts.}\
&\textbf{Repeated comparable probes create perception, not warrant.}\
&\textbf{Warrant is closed exposed dependence under explicit support conditions.}\
&\textbf{A recurrence cannot discharge its own epistemic dependency merely by recurring.}\
&\textbf{Proof topology is not epistemic support topology.}\
&\textbf{The active representation may revise; authoritative ancestry does not rewrite.}\
&\textbf{An external return is not its interpretation.}\
&\textbf{Failure to access a return is not a null return.}\
&\textbf{Compression preserves dependency residue, regeneration, provenance, and reopening.}\
&\textbf{Every semantic object has one authoritative owner.}\
&\textbf{Every consequential residual, including an open dependency, generates the next inquiry.}
\end{aligned}}
]

That is the repair I would apply to 0.3 before making further conceptual additions. It does not make the framework larger in principle; it replaces several proxy structures—DAG, single guard, generic `Unknown`, duplicated state, bare compression—with the exact relations those proxies were imperfectly standing in for.
