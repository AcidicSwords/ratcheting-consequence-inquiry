Correct. The previous version accidentally depended on context the other agent will not have. The game example should be removed entirely, and the principle should be stated generically enough to stand on its own.

Use this version instead.

# Retention, Reconstruction, and Reacquisition

## Purpose

RCI should not define memory only as the ability to reproduce previously retained content.

A learned structure may cease to be directly recallable or reconstructible while still materially changing how quickly, cheaply, or reliably that structure can be learned again.

A person may, for example, be unable to solve a class of problems years after learning it, yet reacquire the competence much faster than someone encountering it for the first time. The earlier learning therefore remains consequential even when direct recall fails.

Hence:

[
\boxed{
\text{failure of recall}
\neq
\text{absence of retained learning}.
}
]

Retention must include not only what can presently be used or reconstructed, but also what changes the future cost or path of reacquisition.

The governing principle is:

[
\boxed{
\textbf{
RETAIN THE SMALLEST RELATIONAL STATE FROM WHICH PROTECTED FUTURE
COMPETENCE CAN BE USED, RECONSTRUCTED, OR REACQUIRED AT ACCEPTABLE COST.
}}
]

This extends regenerative sufficiency. It does not replace it.

---

## 1. Retained state and future competence

Let

[
m\in\mathcal M
]

be retained state.

Let

[
k\in\mathcal K
]

be a target competence.

A competence may be any consequentially usable structure, including:

* a relation;
* a distinction;
* a predictive model;
* a procedure;
* a control capability;
* a representation;
* a question or probe repertoire;
* a method-selection rule;
* a theorem or explanation;
* a skill.

Let

[
c\in\mathcal C
]

be a future cue or context.

Let

[
e\in\mathcal E^\ast
]

be a finite stream of new evidence, instruction, interaction, practice, observation, or experiment available during recovery.

Let

[
\mathcal H
]

be the protected future-interaction horizon.

Recovery need not reproduce the historical representation of the competence.

It is sufficient to recover some

[
k'
]

such that

[
\boxed{
k'\equiv_{\mathcal H}k,
}
]

meaning that (k') preserves the distinctions and operations required by the protected future.

Therefore:

[
\boxed{
\text{historical identity}
\neq
\text{future consequential sufficiency}.
}
]

---

## 2. Distinguish use, reconstruction, and reacquisition

These are different relations and must not be collapsed.

### Present use

[
\boxed{
Use_{\mathcal H}(m,c,k)
}
]

holds when the retained state already permits competent protected use of (k) in context (c).

No substantial reconstruction or new learning is required.

---

### Reconstruction

[
\boxed{
Reconstruct_{\mathcal H}(m,c)
\rightsquigarrow
k'
\equiv_{\mathcal H}k.
}
]

The required working structure is not presently active, but retained structure plus an appropriate cue can regenerate it.

Reconstruction may require computation, search, or memory activation, but not substantial new external learning evidence.

---

### Reacquisition

[
\boxed{
Reacquire_{\mathcal H}(m,c,e)
\rightsquigarrow
k'
\equiv_{\mathcal H}k.
}
]

The retained state is insufficient for direct reconstruction, so new evidence, instruction, interaction, or practice is required.

The defining property of retained learning is not merely that reacquisition eventually succeeds.

It is that the prior state (m) makes reacquisition better than learning from an appropriate baseline without the relevant retained structure.

Thus:

[
\boxed{
\text{reacquisition}
\neq
\text{learning from zero}.
}
]

---

## 3. Reacquisition advantage

Let

[
m_\bot
]

denote a baseline state lacking the relevant retained learning.

For a recovery procedure (\pi), let:

[
\boxed{
C(\pi)
======

(
T,I,K,D,R,\ldots
)
}
]

be its cost vector, where a binding may include:

* (T): time or latency;
* (I): number of interactions, trials, observations, or examples;
* (K): computation;
* (D): external data or instruction;
* (R): risk, destructiveness, or experimental cost;
* other consequential resources.

Do not assume these costs admit a universal scalarization.

Define the attainable recovery-cost frontier:

[
\boxed{
\mathfrak C_{\mathcal H}(m,c,k)
===============================

Frontier
\left{
C(\pi):
\pi(m,c,e)
\rightsquigarrow
k'
\equiv_{\mathcal H}k
\right}.
}
]

Define the baseline frontier:

[
\boxed{
\mathfrak C_{\mathcal H}^{0}(c,k)
=================================

\mathfrak C_{\mathcal H}(m_\bot,c,k).
}
]

Then retained state (m) exhibits a reacquisition advantage for (k) when:

[
\boxed{
\mathfrak C_{\mathcal H}(m,c,k)
\prec
\mathfrak C_{\mathcal H}^{0}(c,k),
}
]

where (\prec) denotes an appropriate strict Pareto improvement or other warranted cost ordering.

This is evidence that learning survives even when direct recall or reconstruction does not.

---

## 4. Scalar savings when a binding permits one

If a binding supplies a scalar recovery cost (C), define:

[
C_0(k,c)
========

\inf_{\pi}
C!\left(
\pi:m_\bot,c\rightsquigarrow k
\right)
]

and:

[
C_m(k,c)
========

\inf_{\pi}
C!\left(
\pi:m,c\rightsquigarrow k
\right).
]

Absolute savings are:

[
\boxed{
Savings(m;k,c)
==============

C_0(k,c)-C_m(k,c).
}
]

When (C_0(k,c)>0), normalized savings may be defined as:

[
\boxed{
S(m;k,c)
========

1-
\frac{C_m(k,c)}{C_0(k,c)}.
}
]

Then:

[
S(m;k,c)>0
]

is evidence of retained learning.

In particular:

[
\boxed{
Recall(m,c,k)=0
\not\Rightarrow
S(m;k,c)=0.
}
]

A system may fail to recall something while retaining a substantial advantage in learning it again.

---

## 5. Retention is relational

Do not turn these recovery relations into rigid memory object types.

The same retained state may be immediately usable for one competence, reconstructive for another, and useful only for accelerated reacquisition of a third.

Define relations such as:

[
\boxed{
Executable_{\mathcal H}(m,c,k)
}
]

[
\boxed{
Reconstructible_{\mathcal H}(m,c,k)
}
]

and:

[
\boxed{
Reacquirable_{\mathcal H}^{B}(m,c,k),
}
]

where (B) is an admissible future recovery budget.

A retained object is therefore characterized by what future recovery operations it supports, not by a nominal memory category.

---

## 6. Three forms of retained competence must remain distinct

Preserve:

[
\boxed{
\text{retaining a result}
\neq
\text{retaining enough to reconstruct the result}
\neq
\text{retaining enough to relearn the result efficiently}.
}
]

A system may lose direct access to a learned relation while retaining structures such as:

* useful distinctions;
* useful probes or questions;
* likely prerequisite relations;
* representations that expose the relevant structure;
* search order;
* known boundaries;
* counterexamples;
* familiar transformations;
* method-selection cues;
* characteristic failure modes;
* recognition of relevant patterns.

These remnants may be insufficient to reproduce the old answer.

They may nevertheless substantially constrain the future search space.

Therefore a retained structure can function as a **reacquisition scaffold**.

---

## 7. Reacquisition scaffold

A reacquisition scaffold is retained structure that does not itself regenerate a target competence but materially changes the future inquiry required to recover it.

Let:

[
s_k\subseteq m
]

be such a scaffold.

It may contain:

[
\boxed{
s_k=
(
Cues,
Probes,
Representations,
Methods,
Boundaries,
Failures,
Prerequisites,
Provenance
).
}
]

Not every component is required.

The criterion is functional:

[
\boxed{
s_k
\text{ is a reacquisition scaffold for }k
}
]

iff conditioning future inquiry on (s_k) produces a warranted improvement in the recovery frontier for (k).

Thus:

[
\boxed{
\mathfrak C_{\mathcal H}(s_k,c,k)
\prec
\mathfrak C_{\mathcal H}^{0}(c,k).
}
]

The scaffold need not contain the historical solution.

It need only prevent future inquiry from beginning from the same undifferentiated state as a novice.

---

## 8. Learning changes future acquisition geometry

Learning should not be identified only with storing propositions.

A learning transition:

[
m_t
\xrightarrow{L}
m_{t+1}
]

is consequential whenever it changes future capacity to:

* perceive;
* distinguish;
* predict;
* act;
* reconstruct;
* inquire;
* or reacquire.

One exact criterion is that, for some (k,c,\mathcal H),

[
\boxed{
\mathfrak C_{\mathcal H}(m_{t+1},c,k)
\prec
\mathfrak C_{\mathcal H}(m_t,c,k).
}
]

Thus prior learning can survive as a deformation of future search even after the explicit learned content is inaccessible.

This gives:

[
\boxed{
\textbf{
LEARNING IS A WARRANTED DEFORMATION OF RETAINED RELATIONAL STATE
THAT CHANGES FUTURE CAPACITY TO PERCEIVE, ACT, RECONSTRUCT,
OR ACQUIRE CONSEQUENTIAL STRUCTURE.
}}
]

---

## 9. Revised memory criterion

Memory should consequently not be defined solely by successful recall.

Use:

[
\boxed{
\textbf{
MEMORY IS RETAINED RELATIONAL STRUCTURE THAT CHANGES
WHAT FUTURE CONSEQUENTIAL COMPETENCE CAN BE USED,
RECONSTRUCTED, OR REACQUIRED, AND AT WHAT COST.
}}
]

A past learning event therefore remains present in memory whenever the resulting retained state materially changes future recovery relative to an appropriate baseline.

Hence:

[
\boxed{
\text{current inaccessibility}
\neq
\text{historical erasure}.
}
]

---

## 10. Reopening must include relearning

A reopening condition:

[
\rho
]

must not be defined only as a trigger for restoring hidden structure.

Depending on the retained package, reopening may produce:

[
\boxed{
\rho
\to
\begin{cases}
Use(k),\
Reconstruct(k),\
Reacquire(k),\
RetrieveProvenance(k).
\end{cases}
}
]

Thus reopening can mean:

* reactivate an existing competence;
* reconstruct a latent competence;
* launch accelerated relearning;
* recover historical evidence from which inquiry must restart.

A compression remains useful even when it cannot restore the old representation directly, provided it preserves a licensed future recovery path.

---

## 11. Reacquisition is inquiry

Reacquisition should use the ordinary RCI machinery.

Given an open competence (k) and retained scaffold (s_k):

[
\boxed{
Reacquire(k\mid s_k)
}
]

creates an inquiry obligation.

The recurrence is:

[
\boxed{
\text{REOPEN}
\to
\text{ACTIVATE RETAINED SCAFFOLD}
\to
\text{ORIENT}
\to
\text{PROBE}
\to
\text{COMPARE}
\to
\text{RECONSTRUCT CANDIDATES}
\to
\text{ATTACK}
\to
\text{WARRANT}
\to
\text{RELEARN}.
}
]

This is not ordinary retrieval.

It is new inquiry whose search space has already been deformed by prior learning.

---

## 12. Extend `RetentionPackage`

The retention object should support direct use, reconstruction, direct consequence evaluation, and reacquisition independently.

A suitable abstract structure is:

```text
RetentionPackage {
    id

    protected_horizon
    retained_representation

    direct_use_contract?
    reconstruction_contract?
    direct_consequence_evaluator?

    reacquisition_scaffold?
    reacquisition_cues[]
    reacquisition_probes[]
    reacquisition_methods[]
    known_boundaries[]
    known_failure_regions[]
    known_prerequisites[]

    expected_reacquisition_frontier?
    baseline_learning_reference?

    support_refs[]
    warrant_refs[]
    provenance_refs[]

    compression_debt
    reopening_conditions[]
    fallback
}
```

No field should be required merely because another mode of recovery exists.

A retained package may support:

[
Use
]

without reconstruction,

[
Reconstruct
]

without new learning,

or only:

[
Reacquire.
]

---

## 13. Generalize regenerative sufficiency

The previous criterion:

[
\text{retain enough to regenerate protected future competence}
]

is too narrow if “regenerate” is interpreted as direct reconstruction.

Define a retained state (m) as regeneratively sufficient under recovery licence (\mathcal L) when:

[
\boxed{
\forall k\in\mathcal K_{\mathcal H},
\quad
\exists \pi:
m
\xrightarrow[\mathcal L]{\pi}
k'
\equiv_{\mathcal H}k.
}
]

The permitted recovery procedure (\pi) may instantiate:

* direct use;
* reconstruction;
* direct consequence regeneration;
* reacquisition.

The recovery licence (\mathcal L) specifies admissible bounds on:

* consequence fidelity;
* latency;
* computation;
* external evidence;
* interaction;
* risk;
* resource use.

Therefore:

[
\boxed{
\textbf{
REGENERATIVE SUFFICIENCY MEANS PRESERVING A LICENSED PATH
BACK TO PROTECTED FUTURE COMPETENCE,
NOT NECESSARILY PRESERVING ITS CURRENT EXPLICIT REPRESENTATION.
}}
]

---

## 14. Compression should optimize future recovery, not immediate recall

Do not define optimal memory as:

[
\max InformationRetained.
]

Do not define it as:

[
\max Recall.
]

And do not define it merely as:

[
\min Storage
]

subject to direct reconstruction.

Instead seek a retained state (m') minimizing active/storage/interference cost subject to an acceptable future recovery profile:

[
\boxed{
\min_{m'}
RetentionCost(m')
}
]

subject to:

[
\boxed{
\forall k\in\mathcal K_{\mathcal H},
\qquad
\mathfrak C_{\mathcal H}(m',c,k)
\preceq
B_{k,c},
}
]

where (B_{k,c}) is the licensed recovery frontier or budget for that competence.

Some competencies may require immediate availability.

Others may only require reconstruction.

Still others may safely be retained only as rapid reacquisition potential.

---

## 15. Forgetting is graded loss of recovery capacity

Forgetting is not simply deletion.

A competence may become:

[
\boxed{
\text{immediately usable}
\to
\text{reconstructible}
\to
\text{cheaply reacquirable}
\to
\text{recoverable only through provenance}
\to
\text{effectively lost}.
}
]

These are not mandatory stages or nominal types.

They express progressively weaker recovery relations.

Thus:

[
\boxed{
\textbf{
FORGETTING IS REDUCTION OF RETAINED FUTURE RECOVERY CAPACITY.
}}
]

And:

[
\boxed{
\textbf{
OPTIMAL FORGETTING REDUCES ACTIVE RETAINED STRUCTURE
WHILE PRESERVING AN ACCEPTABLE FUTURE RECOVERY PROFILE.
}}
]

---

## 16. The open future constrains compression

Future relevance is not completely known.

Therefore minimizing retained state relative only to currently known tasks can destroy future learning capacity.

Maintain:

[
\Sigma
======

A_{\mathcal H}
\dot\cup
U_{\mathcal H}
\dot\cup
I_{\mathcal H},
]

where:

* (A_{\mathcal H}): currently consequential structure;
* (U_{\mathcal H}): structure whose relevance remains unresolved;
* (I_{\mathcal H}): structure established consequence-null under the current protected horizon and applicable conditions.

Only (I_{\mathcal H}) licenses aggressive compression.

Even there, provenance, reopening, or reacquisition structure may remain required.

Therefore:

[
\boxed{
\text{not currently required}
\neq
\text{safely forgotten}.
}
]

---

## 17. Revised definitions

### Perception

[
\boxed{
\textbf{
PERCEPTION IS THE DISCOVERY OF CONSEQUENTIAL DIFFERENCE THROUGH
RELATIONAL PROJECTION OVER A CHANGING STATE.
}}
]

### Reasoning

[
\boxed{
\textbf{
REASONING IS THE CONSTRAINED DEFORMATION OF RELATIONAL
REPRESENTATION AROUND CONSEQUENTIAL DIFFERENCES,
POSSIBILITIES, AND OPEN DEPENDENCIES.
}}
]

### Learning

[
\boxed{
\textbf{
LEARNING IS A WARRANTED CHANGE IN RETAINED RELATIONAL STATE
THAT CHANGES FUTURE CAPACITY TO PERCEIVE, ACT, RECONSTRUCT,
OR REACQUIRE.
}}
]

### Memory

[
\boxed{
\textbf{
MEMORY IS RETAINED RELATIONAL STRUCTURE THAT CHANGES WHAT
FUTURE CONSEQUENTIAL COMPETENCE CAN BE USED, RECONSTRUCTED,
OR REACQUIRED, AND AT WHAT COST.
}}
]

### Forgetting

[
\boxed{
\textbf{
FORGETTING IS REDUCTION OF RETAINED FUTURE RECOVERY CAPACITY.
IT IS WARRANTED ONLY WHILE THE RESULTING RECOVERY PROFILE REMAINS
ACCEPTABLE UNDER THE PROTECTED FUTURE.
}}
]

---

## 18. Permanent distinctions

Add these to the project:

[
\boxed{
\text{failure to recall}
\neq
\text{absence of retained learning}
}
]

[
\boxed{
\text{recall}
\neq
\text{reconstruction}
\neq
\text{reacquisition}
}
]

[
\boxed{
\text{reacquisition}
\neq
\text{learning from zero}
}
]

[
\boxed{
\text{retaining an answer}
\neq
\text{retaining a reconstruction path}
\neq
\text{retaining a relearning advantage}
}
]

[
\boxed{
\text{current inaccessibility}
\neq
\text{historical erasure}
}
]

[
\boxed{
\text{not currently useful}
\neq
\text{safely forgettable}
}
]

[
\boxed{
\text{minimal current representation}
\neq
\text{optimal memory under an open future}.
}
]

---

## 19. Governing retention law

The project-level law should be:

[
\boxed{
\begin{minipage}{0.88\linewidth}
\centering
\textbf{
Do not measure retention only by what can presently be recalled.
A past learning episode remains retained whenever it materially changes
the future cost, path, or attainable fidelity of consequential recovery.
Compress active structure as far as protected future use permits, but
preserve enough relational organization, probes, cues, provenance,
and reopening structure that important competence can still be used,
reconstructed, or reacquired within its licensed future cost.
}
\end{minipage}
}
]

Its compact form is:

[
\boxed{
\textbf{
MEMORY IS NOT ONLY WHAT CAN BE RECALLED.
IT IS ALSO WHAT MAKES FUTURE LEARNING NO LONGER START FROM ZERO.
}}
]

And the optimization criterion is:

[
\boxed{
\textbf{
MINIMIZE RETAINED STORAGE AND INTERFERENCE
SUBJECT TO ACCEPTABLE FUTURE CONSEQUENCE FIDELITY
AND ACCEPTABLE USE, RECONSTRUCTION, OR REACQUISITION COST.
}}
]

This version is self-contained and does not assume the agent has seen the game-environment example.
