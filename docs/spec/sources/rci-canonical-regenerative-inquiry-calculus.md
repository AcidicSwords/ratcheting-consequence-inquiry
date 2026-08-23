# Regenerative Inquiry Calculus

## Candidate canonical operator, question, behavior, abstraction, and self-revision kernel

**Status:** candidate semantic rebind; not yet repository authority  
**Scope:** The Invariant of Good Reasoning + Ratcheting Consequence Inquiry  
**Purpose:** Replace the remaining collection of adjacent concepts with one typed compositional structure that regenerates question formation, answer structure, interaction, retained state, compression, reopening, learning, and project self-revision while preserving the existing actuality and warrant boundaries.

---

# 0. Result

The smallest structure found in the current reconstruction has four layers:

\[
\boxed{
\textbf{COMPOSITIONAL SYNTAX}
\;+\;
\textbf{DEPENDENT QUESTION SIGNATURE}
\;+\;
\textbf{BEHAVIORAL DYNAMICS}
\;+\;
\textbf{NON-SELF-LICENSING WARRANT}.
}
\]

They are linked by exact maps and compatibility conditions.

A question is not fundamentally a sentence, claim role, or named question family. A question is a **typed operation with a dependent result type**. For a repertoire \(Q\), every question \(q\in Q\) has an answer type

\[
\boxed{A(q).}
\]

One unresolved inquiry step has the polynomial/container form

\[
\boxed{P_Q(X)=\sum_{q\in Q}X^{A(q)}.}
\tag{0.1}
\]

An element is exactly a question \(q\) plus, for every possible answer \(a\in A(q)\), a continuation \(\kappa(a)\in X\):

\[
\boxed{(q,\kappa),\qquad \kappa:A(q)\to X.}
\tag{0.2}
\]

A finite inquiry program therefore has the canonical grammar

\[
\boxed{
K::=Return(z)\mid Ask(q,\kappa),
\qquad
\kappa:A(q)\to K.
}
\tag{0.3}
\]

The answer is **not** an argument to `Ask`. It is supplied later by the lawful discharge route and selects one continuation. This corrects the earlier abstract form `Step(q,a,κ)`.

The current reasoning representation is executable only if protected observations and protected continuations descend through its quotient. The current reasoning grammar is revisable only through a successor relation that preserves still-valid protected behavior, adds strict gain, and receives independent warrant.

Everything else below is a derivation or specialization of this structure.

---

# I. Constitutional separations

The rebind changes the semantic center. It does not change the project's epistemic constitution.

\[
\boxed{\text{represented operator}\neq\text{actualized operation};}
\]
\[
\boxed{\text{generated answer}\neq\text{actual return};}
\]
\[
\boxed{\text{raw return}\neq\text{interpretation};}
\]
\[
\boxed{\text{interpretation}\neq\text{warrant};}
\]
\[
\boxed{\text{warrant}\neq\text{semantic promotion};}
\]
\[
\boxed{\text{working nondistinction}\neq\text{exact behavioral equivalence};}
\]
\[
\boxed{\text{current-output sufficiency}\neq\text{future-transition sufficiency};}
\]
\[
\boxed{\text{semantic quotient}\neq\text{concrete encoding};}
\]
\[
\boxed{\text{factorization residue}\neq\text{open epistemic dependency};}
\]
\[
\boxed{\text{question semantics}\neq\text{question discharge authority};}
\]
\[
\boxed{\text{semantic unification}\neq\text{governance-role collapse};}
\]
\[
\boxed{\text{self-application}\neq\text{self-validation}.}
\]

These separations specify when two structures may not be identified.

---

# II. Binding and typed composition

## 1. Binding

Let \(\mathbb B\) denote a binding. A binding supplies

\[
\boxed{
\mathbb B=(\mathsf{Int},\mathsf G,\circ,\mathsf{Rel},\mathsf{Act},\mathsf{Check},\mathsf W,\mathcal H,\mathcal R)
}
\tag{2.1}
\]

where \(\mathsf{Int}\) is a family of compositional interfaces, \(\mathsf G\) the admitted primitive operator repertoire, \(\circ\) lawful partial serial composition, \(\mathsf{Rel}\) a binding-native relation vocabulary, \(\mathsf{Act}\) actualization channels, \(\mathsf{Check}\) validation relations, \(\mathsf W\) warrant policy/ancestry, \(\mathcal H\) the protected future-use horizon, and \(\mathcal R\) the resource horizon.

Order, metric, topology, probability, Boolean structure, linear structure, causality, control, rewriting, and similar structures are binding-specific.

## 2. Interfaces and operators

For \(A,B\in\mathsf{Int}_{\mathbb B}\):

\[
\boxed{f:A\to_{\mathbb B}B.}
\tag{2.2}
\]

This states source, target, and binding-relative admissibility only. It does not universally imply determinism, reversibility, causality, totality, executability, or actuality.

When identities are admitted:

\[
\boxed{1_A:A\to A.}
\tag{2.3}
\]

For \(f:A\to B\) and \(g:B\to C\):

\[
\boxed{g\circ f:A\to C.}
\tag{2.4}
\]

with associativity whenever typed:

\[
h\circ(g\circ f)=(h\circ g)\circ f.
\tag{2.5}
\]

## 3. Generated operator language

Let \(\mathsf G_t(A,B)\) be the admitted primitive generators available at time \(t\). The freely generated terms are

\[
\boxed{
\mathsf{Tm}_t(A,B)=\operatorname{Free}_{\circ}(\mathsf G_t)(A,B).
}
\tag{2.6}
\]

A represented path is

\[
\boxed{\pi=(f_1,\ldots,f_n)}
\]

with composite

\[
\boxed{\llbracket\pi\rrbracket=f_n\circ\cdots\circ f_1.}
\tag{2.7}
\]

The composite and its factorization remain distinct because future use may inspect the factorization.

---

# III. Relation schemas and open relations

## 4. Typed relation schema

A relation schema is

\[
\boxed{R\hookrightarrow X_1\times\cdots\times X_n.}
\tag{3.1}
\]

Its signature is

\[
\boxed{\operatorname{sig}(R)=(x_1:X_1,\ldots,x_n:X_n).}
\tag{3.2}
\]

A complete assignment \(\gamma\) produces a proposition

\[
\boxed{R[\gamma].}
\tag{3.3}
\]

A claim may carry this proposition. Completeness of the assignment does not imply positive standing.

## 5. Open relation

Let \(I\subseteq\{1,\ldots,n\}\) be the open ports and \(\beta\) bind all others. The completion fiber is

\[
\boxed{
\operatorname{Fib}_{I}(R\mid\beta)
=
\left\{a_I\in\prod_{i\in I}X_i:R[\beta\oplus a_I]\right\}.
}
\tag{3.4}
\]

The corresponding question is

\[
\boxed{?_{I}R[\beta].}
\tag{3.5}
\]

Thus

\[
\boxed{
\text{relation}\to\text{partial binding}\to\text{question}\to\text{complete binding}\to\text{proposition}.
}
\tag{3.6}
\]

## 6. Discharge class

Every executable relation schema declares how its open ports may lawfully be discharged:

\[
\boxed{
mode(R)\in\{Derived,Candidate,Actual,Checked,Warrant\}.
}
\tag{3.7}
\]

`Derived` permits pure registered derivation; `Candidate` permits provisional semantic generation; `Actual` requires an actual interaction return; `Checked` requires an admitted independent checker; `Warrant` requires the standing warrant policy.

This preserves the existing authority boundaries inside one relation language.

---

# IV. Question signatures as dependent operations

## 7. Question repertoire

A question repertoire is a dependent signature

\[
\boxed{\mathcal Q=(Q,A)}
\tag{4.1}
\]

with question \(q\in Q\) and complete answer type

\[
\boxed{A(q).}
\tag{4.2}
\]

The question identity determines the complete answer type before any answer is observed.

## 8. One inquiry node

For any continuation carrier \(X\):

\[
\boxed{P_{\mathcal Q}(X)=\sum_{q\in Q}X^{A(q)}.}
\tag{4.3}
\]

An element is

\[
\boxed{(q,\kappa),\qquad \kappa:A(q)\to X.}
\tag{4.4}
\]

The question supplies the operation; the dependent answer type supplies the alternatives; the continuation function supplies the next state for each alternative.

## 9. Finite inquiry programs

For result type \(Z\):

\[
\boxed{
\mathsf{Prog}_{\mathcal Q}(Z)
\cong
Z+P_{\mathcal Q}(\mathsf{Prog}_{\mathcal Q}(Z)).
}
\tag{4.5}
\]

Concrete grammar:

\[
\boxed{
K::=Return(z)\mid Ask(q,\kappa),\qquad\kappa:A(q)\to K.
}
\tag{4.6}
\]

If `ask(q)` is viewed as an algebraic operation returning \(A(q)\):

\[
\boxed{Ask(q,\kappa)\equiv ask(q)\bind\kappa.}
\tag{4.7}
\]

## 10. Potentially unbounded inquiry

A reference semantics for potentially unbounded recursive inquiry is

\[
\boxed{
\mathsf{ITree}_{\mathcal Q}(Z)
\simeq
\nu X.\;Z+P_{\mathcal Q}(X).
}
\tag{4.8}
\]

The implementation need not use coinductive types; actual execution remains resource-bounded.

---

# V. Question semantics as quotient classifiers

## 11. Applicability and classifier

For question \(q\), let \(X_q\) be the typed carrier on which it is interpreted and \(D_q\hookrightarrow X_q\) its applicability region. Define

\[
\boxed{\pi_q:D_q\twoheadrightarrow A(q).}
\tag{5.1}
\]

The question signature supplies the complete answer type. The classifier supplies the binding-relative semantics assigning applicable completions to complete answers.

## 12. Answer fibers

For \(a\in A(q)\):

\[
\boxed{F_q(a)=\pi_q^{-1}(\{a\}).}
\tag{5.2}
\]

When \(\pi_q\) is total over \(D_q\):

\[
\boxed{D_q=\biguplus_{a\in A(q)}F_q(a).}
\tag{5.3}
\]

Complete answer cells are therefore mutually exclusive and exhaustive inside the applicability region.

## 13. Question-induced equivalence

\[
\boxed{x\sim_q y\iff\pi_q(x)=\pi_q(y).}
\tag{5.4}
\]

Equivalently:

\[
\boxed{\ker(\pi_q)=\{(x,y):x\sim_q y\}.}
\tag{5.5}
\]

This relation records exactly which distinctions the question ignores. It is local to the question and must not be identified with global protected behavioral equivalence.

## 14. Sibling complement and exterior

For complete answer \(a\):

\[
\boxed{\operatorname{Alt}_q(a)=A(q)\setminus\{a\}.}
\tag{5.6}
\]

Its sibling complement is

\[
\boxed{F_q(\operatorname{Alt}_q(a))=\biguplus_{b\neq a}F_q(b).}
\tag{5.7}
\]

The applicability exterior is

\[
\boxed{E_q=X_q\setminus D_q.}
\tag{5.8}
\]

Hence

\[
\boxed{
X_q\setminus F_q(a)
=
F_q(\operatorname{Alt}_q(a))\uplus E_q.
}
\tag{5.9}
\]

This permanently separates a different answer inside the same frame from failure of the frame's applicability.

## 15. Partial responses

Let \(Y_q\) be a decoded response carrier and define

\[
\boxed{\delta_q:Y_q\rightharpoonup\mathcal P_+(A(q)).}
\tag{5.10}
\]

For a response \(y\), a singleton \(\delta_q(y)\) is a complete answer; a proper multi-element subset is a partial answer; \(\delta_q(y)=A(q)\) is nondiscriminating; undefined means malformed/unsupported under this decoder.

The remaining completion field is

\[
\boxed{F_q(\delta_q(y))=\biguplus_{a\in\delta_q(y)}F_q(a).}
\tag{5.11}
\]

The excluded answer set is

\[
\boxed{A(q)\setminus\delta_q(y).}
\tag{5.12}
\]

---

# VI. Refinement, abstraction, combination

## 16. Precision preorder

For questions \(q,r\) on a common applicable carrier, define

\[
\boxed{q\preceq r}
\tag{6.1}
\]

iff there exists \(c:A(r)\to A(q)\) with

\[
\boxed{\pi_q=c\circ\pi_r.}
\tag{6.2}
\]

Equivalently:

\[
\boxed{\ker(\pi_r)\subseteq\ker(\pi_q).}
\tag{6.3}
\]

Thus \(r\) is at least as discriminating as \(q\).

Strict refinement is strict kernel inclusion.

## 17. Local refinement after an answer

A successor question \(r\) refines answer \(a\) of \(q\) when

\[
\boxed{D_r\subseteq F_q(a)}
\tag{6.4}
\]

and \(r\) is nonconstant on \(D_r\). The new distinction is therefore one that the prior answer class deliberately left unresolved.

## 18. Abstraction

Abstraction is movement in the opposite direction of the same preorder. If

\[
\pi_q=c\circ\pi_r,
\]

then \(q\) is a coarsening of \(r\). No separate abstraction primitive is needed.

## 19. Joint refinement

On \(D_q\cap D_r\):

\[
\boxed{\pi_{q\otimes r}(x)=(\pi_q(x),\pi_r(x)).}
\tag{6.5}
\]

Then

\[
\boxed{\ker(\pi_{q\otimes r})=\ker(\pi_q)\cap\ker(\pi_r).}
\tag{6.6}
\]

and

\[
\boxed{F_{q\otimes r}(a,b)=F_q(a)\cap F_r(b).}
\tag{6.7}
\]

This is the exact structure for cross-cutting questions and overlapping local descriptions.

## 20. Boundary adjacency

No universal metric or linear axis is assumed. If a binding supplies elementary variation \(V_q\subseteq D_q\times D_q\), define

\[
\boxed{
Adj_q(a,b)
\iff
a\neq b\land\exists x\in F_q(a),y\in F_q(b):(x,y)\in V_q.
}
\tag{6.8}
\]

This induces a binding-relative answer graph \(G_q=(A(q),Adj_q)\). Without \(V_q\), answers are alternatives but not metrically adjacent.

---

# VII. Protected behavioral equivalence

## 21. Protected contexts

Let \(\mathcal H\) be the protected family of future contexts. For parallel terms \(f,g:A\to B\):

\[
\boxed{
f\equiv_{\mathcal H}g
\iff
\forall K\in\mathcal H,\quad
\operatorname{Con}_K(f)=\operatorname{Con}_K(g).
}
\tag{7.1}
\]

Define

\[
\boxed{
\operatorname{Sep}_{\mathcal H}(f,g)
=
\{K\in\mathcal H:\operatorname{Con}_K(f)\neq\operatorname{Con}_K(g)\}.
}
\tag{7.2}
\]

Then

\[
\boxed{f\not\equiv_{\mathcal H}g\iff\operatorname{Sep}_{\mathcal H}(f,g)\neq\varnothing.}
\tag{7.3}
\]

## 22. Horizon monotonicity

If \(\mathcal H\subseteq\mathcal H'\), then

\[
\boxed{\equiv_{\mathcal H'}\subseteq\equiv_{\mathcal H}.}
\tag{7.4}
\]

Adding protected future contexts can split old behavioral classes but cannot merge classes already separated by the retained horizon.

## 23. Question-frame defect

\[
\boxed{FD_{\mathcal H}(q)=\ker(\pi_q)\setminus\equiv_{\mathcal H}.}
\tag{7.5}
\]

If nonempty, the question frame identifies distinctions that remain protected elsewhere. This is lawful for a local coordinate only if the surrounding retained structure preserves them. If the question frame is proposed as the whole replacement representation, require

\[
\boxed{FD_{\mathcal H}(q)=\varnothing.}
\tag{7.6}
\]

---

# VIII. Representation refinement and abstraction

## 24. Current representation

Let

\[
\boxed{\eta_t:X\to S_t}
\tag{8.1}
\]

be the current retained representation. Adding question coordinate \(\pi_q\) gives

\[
\boxed{\eta_{t+1}=\langle\eta_t,\pi_q\rangle.}
\tag{8.2}
\]

Therefore

\[
\boxed{\ker(\eta_{t+1})=\ker(\eta_t)\cap\ker(\pi_q).}
\tag{8.3}
\]

Acquiring a nonredundant discriminator is exact partition refinement.

## 25. Redundant/compiled question

The question adds no new semantic coordinate when

\[
\boxed{\ker(\eta_t)\subseteq\ker(\pi_q).}
\tag{8.4}
\]

Equivalently:

\[
\boxed{\exists\bar\pi_q:\pi_q=\bar\pi_q\circ\eta_t.}
\tag{8.5}
\]

Then the question may be executed as a readout from the current retained representation.

## 26. Safe abstraction

Let \(c:S_t\twoheadrightarrow S'\) and \(\eta'=c\circ\eta_t\). Exact protected abstraction requires

\[
\boxed{\ker(\eta')\subseteq\equiv_{\mathcal H}.}
\tag{8.6}
\]

Equivalently:

\[
\boxed{
\forall K\in\mathcal H,\quad
\exists\bar K:\operatorname{Con}_K=\bar K\circ\eta'.
}
\tag{8.7}
\]

---

# IX. Dynamic sufficiency

## 27. Deterministic continuation

For \(a:X\to X'\), \(\eta:X\to S\), and \(\eta':X'\to S'\), the continuation descends iff

\[
\boxed{
\exists\bar a:S\to S'\quad
\eta'\circ a=\bar a\circ\eta.
}
\tag{9.1}
\]

Equivalently:

\[
\boxed{
\eta(x)=\eta(y)
\Rightarrow
\eta'(a(x))=\eta'(a(y)).
}
\tag{9.2}
\]

This is the exact deterministic congruence condition.

## 28. General behavioral continuation

A binding-native dynamic system may be represented by a coalgebra

\[
\boxed{\gamma:X\to F(X).}
\tag{9.3}
\]

A quotient \(\eta:X\twoheadrightarrow\bar X\) is behaviorally executable when there exists

\[
\boxed{\bar\gamma:\bar X\to F(\bar X)}
\]

with

\[
\boxed{F(\eta)\circ\gamma=\bar\gamma\circ\eta.}
\tag{9.4}
\]

This is the general form of the current recursive-state/continuation condition.

---

# X. Inquiry dynamics

## 29. Autonomous next-question coalgebra

Let \(\Sigma\) be a retained inquiry state. A deterministic next-question policy has form

\[
\boxed{
\Gamma:\Sigma\to Z+\sum_{q\in Q}\Sigma^{A(q)}.
}
\tag{10.1}
\]

For state \(s\), either inquiry terminates with \(z\), or

\[
\Gamma(s)=(q,\kappa_s)
\]

where

\[
\kappa_s:A(q)\to\Sigma.
\]

This says exactly which question is generated next and which successor inquiry state follows each complete answer.

If several questions are incomparable, a binding may retain a frontier instead of forcing one scalar choice.

## 30. Actual discharge

For `Actual` questions, the program does not choose the answer. The actualization route establishes

\[
\boxed{!_{\mathbb B}q\Downarrow r}
\]

and decoding gives

\[
\boxed{\delta_q(r)=S\subseteq A(q).}
\]

A complete answer selects one continuation. A partial answer may preserve several branches or open a residual inquiry according to the binding.

---

# XI. Retention and generation

## 31. Retention algebra

Finite inquiry structure may be summarized by an algebra

\[
\boxed{\alpha:Z+P_{\mathcal Q}(M)\to M.}
\tag{11.1}
\]

Its induced catamorphism

\[
\boxed{fold_\alpha:\mathsf{Prog}_{\mathcal Q}(Z)\to M}
\tag{11.2}
\]

maps finite interaction structure into a retained representation.

This is a genuine recursion-scheme fold. It is not automatically lossless or sufficient.

## 32. Generative coalgebra

A retained representation may generate further inquiry by

\[
\boxed{\gamma:M\to Z+P_{\mathcal Q}(M).}
\tag{11.3}
\]

The algebra and coalgebra need not be inverses. Their compatibility is substantive.

## 33. Bialgebraic compatibility

At the general operator-grammar level, let \(T\) encode generated syntax and \(F\) behavior. A distributive law

\[
\boxed{\lambda:TF\Rightarrow FT}
\tag{11.4}
\]

specifies how generated syntax interacts with behavior. A compatible algebra/coalgebra pair

\[
\alpha:TX\to X,
\qquad
\gamma:X\to FX
\]

satisfies

\[
\boxed{
\gamma\circ\alpha
=
F\alpha\circ\lambda_X\circ T\gamma.
}
\tag{11.5}
\]

This is the strongest identified native structure for proving that behavior remains compositional under the generated operator language. It is a reference realization, not an imposed universal implementation.

---

# XII. Regenerative quotient contract

## 34. Quotient contract

Let \(q:X\twoheadrightarrow Y\), protected observations \(\mathcal H\), and protected continuations \(\mathcal A\). Define

\[
\boxed{RegQ(q;\mathcal H,\mathcal A)}
\]

when both consequence sufficiency and continuation descent hold.

### Consequence sufficiency

\[
\boxed{
\forall e\in\mathcal H,\quad
\exists\bar e:\operatorname{Con}_e=\bar e\circ q.
}
\tag{12.1}
\]

### Continuation descent

For each \(a:X\to X_a\), with successor quotient \(q_a:X_a\to Y_a\):

\[
\boxed{
\exists\bar a:Y\to Y_a:\quad q_a\circ a=\bar a\circ q.
}
\tag{12.2}
\]

A representation can satisfy (12.1) while failing (12.2). It then preserves current protected outputs but is not sufficient for recursive continuation.

## 35. Recovery structure

Let \(\rho_q\) denote retained recovery/provenance structure associated with \(q\). It may support provenance retrieval, factorization recovery, reconstruction, direct consequence evaluation, reacquisition, or restoration of a finer representation.

Literal inversion \(q^{-1}:Y\to X\) is not required.

## 36. Unlock field

\[
\boxed{
Unlock(q)=Unlock_{obs}(q)\cup Unlock_{dyn}(q)\cup Unlock_{ctx}(q).
}
\tag{12.3}
\]

where

\[
\boxed{
Unlock_{obs}(q)=\{e:\operatorname{Con}_e\text{ does not factor through }q\},
}
\tag{12.4}
\]

\[
\boxed{
Unlock_{dyn}(q)=\{a:a\text{ does not descend through }q\},
}
\tag{12.5}
\]

and \(Unlock_{ctx}\) contains binding, scope, applicability, assumptions, warrant, or recovery-contract changes that invalidate the license.

This one definition governs reopening of question-based abstractions, retained states, semantic compression, and promoted composites.

---

# XIII. Breakers and successor questions

## 37. Breaker of an answer class

For complete answer \(a\) to \(q\):

\[
\boxed{
Break_{\mathcal H}(q,a)
=
\{(x,y,K):x,y\in F_q(a),\;K\in\mathcal H,\;\operatorname{Con}_K(x)\neq\operatorname{Con}_K(y)\}.
}
\tag{13.1}
\]

A nonempty breaker set proves that the answer class is too coarse to replace the finer structure under that horizon.

## 38. Reopening condition

\[
\boxed{
Reopen(q,a;\mathcal H')
\iff
Break_{\mathcal H'}(q,a)\neq\varnothing.
}
\tag{13.2}
\]

## 39. Applicability exit

A sibling refinement remains inside \(D_q\). An applicability challenge asks whether membership in \(D_q\) itself still holds. These are distinct successor questions.


---

# XIV. Two orders: precision and improvement

A persistent ambiguity disappears once two orders are kept separate.

## 40. Precision order

For quotient/classifier maps \(q,r\) on a common carrier:

\[
\boxed{
q\preceq_{prec}r
\iff
\ker(r)\subseteq\ker(q).
}
\tag{14.1}
\]

Thus \(r\) is at least as precise as \(q\).

Refinement moves upward in this order. Abstraction moves downward.

## 41. Successor order

For complete reasoning representations/presentations \(R,R'\):

\[
\boxed{R'\succ_{\mathcal H}R}
\]

iff

\[
\boxed{
Preserve_{\mathcal H}(R',R)
\land
StrictGain_{\mathcal H}(R',R)
\land
Warranted(R').
}
\tag{14.2}
\]

This is not the precision order.

A justified refinement can be an improvement. A justified abstraction can also be an improvement when it removes inactive distinction, lowers future cost, improves compositionality, or improves recovery while preserving every protected capability.

Therefore neither implication holds universally:

\[
R'\succ R\Rightarrow R\preceq_{prec}R',
\]

\[
R'\succ R\Rightarrow R'\preceq_{prec}R.
\]

This is the exact reason that both splitting and merging can be epistemic progress.

---

# XV. Compilation and promoted operators

## 42. Definitional naming

For

\[
t=f_n\circ\cdots\circ f_1,
\]

a symbol

\[
m:=t
\]

is only a definitional abbreviation.

## 43. Operational promotion

A promoted implementation/operator \(m\) may replace the original composite when

\[
\boxed{m\equiv_{\mathcal H}t}
\tag{15.1}
\]

under the declared horizon and there is strict typed gain, for example lower future execution or inquiry cost.

A lawful promotion record must preserve:

- the defining composite/factorization;
- protected equivalence contract;
- horizon and applicability;
- gain evidence;
- provenance;
- recovery route;
- unlock conditions.

Promotion does not make \(m\) permanently primitive.

---

# XVI. Learning as change to the generative presentation

## 44. Reasoning presentation

Define

\[
\boxed{\mathsf{Pres}_t=\langle\mathsf G_t\mid\mathsf E_t\rangle}
\tag{16.1}
\]

where \(\mathsf G_t\) is the admitted generator repertoire and \(\mathsf E_t\) the standing equations, inequations, guards, applicability constraints, support relations, and composition laws.

The generated language is

\[
\boxed{\mathsf{Tm}_t=\operatorname{Free}(\mathsf G_t).}
\tag{16.2}
\]

Protected behavioral equivalence induces hom-wise quotients

\[
\boxed{\mathfrak A_t(A,B)=\mathsf{Tm}_t(A,B)/{\equiv_{\mathcal H_t}}.}
\tag{16.3}
\]

## 45. Primitive presentation changes

A warranted successor may:

### Add a generator

\[
\mathsf G_{t+1}=\mathsf G_t\cup\{g\}.
\]

### Add an equation / merge

\[
\mathsf E_{t+1}=\mathsf E_t\cup\{f\equiv_{\mathcal H}g\}.
\]

### Split an equation

A new separator establishes

\[
f\not\equiv_{\mathcal H'}g.
\]

### Add a question operation

\[
Q_t\subset Q_{t+1}.
\]

### Refine an answer frame

Replace \(\pi_q\) by a finer classifier under an explicit factor map.

### Promote a composite

Add a generator \(m\) with a licensed defining equivalence to an existing composite.

### Import a native method

Admit a new operator through a bridge that preserves the required relation and applicable assumptions.

### Rebind

Change interfaces, relation vocabulary, or composition structure when the required consequential relation is not expressible in the incumbent regime.

## 46. Learning criterion

Let \(\mathcal H_{learn}\) inspect future question generation, answer frames, separator availability, composition, promotion, quotienting, reopening, recovery, action selection, rebind behavior, and resource cost.

A warranted transition is learning only if

\[
\boxed{
\mathsf{Pres}_t\not\equiv_{\mathcal H_{learn}}\mathsf{Pres}_{t+1}.
}
\tag{16.4}
\]

---

# XVII. Canonical relation basis and generated questions

The standard question repertoire should be generated by opening ports of typed relations rather than treated as a complete taxonomy.

## 47. Portable relation basis

\[
\boxed{
Type,\;Comp,\;Con,\;Sep,\;Eq,\;Factor,\;Desc,\;Act,\;Support,\;Preserve,\;Gain,\;Successor,\;Recover.
}
\]

These are a portable basis, not an exhaustive ontology. Bindings may add native relations.

## 48. Composition

\[
\boxed{Comp(f,g,h)\iff h=g\circ f.}
\tag{17.1}
\]

Open \(h\): what is the composite?  
Open \(g\): what continuation after \(f\) yields \(h\)?  
Open \(f\): what predecessor before \(g\) yields \(h\)?

One relation therefore generates forward-construction and inverse/prerequisite questions.

## 49. Consequence

\[
\boxed{Con(K,f,y)\iff \operatorname{Con}_K(f)=y.}
\tag{17.2}
\]

Open \(y\): what consequence?  
Open \(K\): under what context?  
Open \(f\): what transformation gives that consequence?

## 50. Separation

\[
\boxed{Sep(K,f,g)\iff \operatorname{Con}_K(f)\neq\operatorname{Con}_K(g).}
\tag{17.3}
\]

Open \(K\): what context distinguishes \(f\) from \(g\)?

## 51. Factorization

\[
\boxed{Factor(e,q,\bar e)\iff \operatorname{Con}_e=\bar e\circ q.}
\tag{17.4}
\]

Open \(q\): through what representation does the protected consequence factor?  
Open \(\bar e\): what readout computes it?

## 52. Descent

\[
\boxed{Desc(q,a,\bar a)\iff q'\circ a=\bar a\circ q.}
\tag{17.5}
\]

Open \(\bar a\): what operation realizes this continuation on the retained representation?  
Open \(q\): what representation makes this continuation well defined?

## 53. Actualization

\[
\boxed{Act_{\mathbb B}(a,r)}
\tag{17.6}
\]

means actualizing \(a\) through binding \(\mathbb B\) produced raw return \(r\). The return port has discharge class `Actual`.

## 54. Successor

\[
\boxed{Successor_{\mathcal H}(R',R)}
\]

is derived from preservation, strict typed gain, and standing warrant.

Open \(R'\): what successor can lawfully replace \(R\)?

This is the canonical self-improvement question.

---

# XVIII. Existing question families as derived forms

The stable `core-v1` profile remains operationally valuable. It ceases to be the semantic ontology of all questions.

| Existing family | Formal derivation |
|---|---|
| obligation characterization | expose unresolved ports of the governing relation |
| same-class variation | find a transform under which protected consequence remains invariant |
| boundary crossing | find a transform under which protected consequence changes |
| factor proposal | open the representation/readout ports of `Factor` |
| necessity counterexample | search for protected consequence with proposed condition absent |
| sufficiency counterexample | search for proposed condition with protected consequence absent |
| conflict localization | expose the implicated port in support/conflict relations |
| residual characterization | expose unresolved fibers, failed factorizations, or open dependencies |

Terms such as “minimal,” “nearest,” “best,” and “extreme” are valid only when the binding supplies the order, metric, cost, or other comparison relation that gives them semantics. Otherwise retain a nondominated frontier.

---

# XIX. Probe and question relation

A probe is a question operation with an actual or independently checked discharge route plus an exact comparability contract.

A probe identity should therefore pin:

- question/frame identity;
- binding;
- scope;
- applicability;
- comparison semantics;
- protected horizon;
- discharge route.

Repeated probe events form a behavioral trace. A learned probe is an admitted extension of the question/operator signature whose evaluation demonstrates nonredundant protected discrimination.

---

# XX. Memory and recovery

## 55. Memory

Memory is retained structure whose presence changes future protected compositional/inquiry capacity or recovery cost.

It may retain:

- quotient coordinates;
- promoted operators;
- factorization;
- question frames;
- separator contexts;
- support/warrant ancestry;
- recovery routes;
- provenance;
- failed but reusable paths.

Direct recall is not the defining criterion.

## 56. Recovery family

\[
\boxed{Recover_{\mu,\mathcal H}(m,c,k)}
\]

with

\[
\mu\in\{Use,Reconstruct,Evaluate,Reacquire\}.
\]

These remain distinct because a representation may preserve one recovery capability while losing another.

---

# XXI. Self-revision

## 57. Meta-binding

Reify the current reasoning presentation

\[
\ulcorner\mathsf{Pres}_t\urcorner
\]

inside a meta-binding. The same relation/query calculus can then operate on question signatures, frames, operators, composition laws, quotient contracts, methods, source code, project goals, and validation machinery.

No untyped self-membership is required.

## 58. Candidate meta-operators

Examples include

\[
AddGenerator,
\quad
AddRelation,
\quad
RefineQuestion,
\quad
CoarsenQuestion,
\quad
AddSeparator,
\quad
PromoteComposite,
\quad
ChangeQuotient,
\quad
Rebind,
\quad
ChangeImplementation.
\]

Each is an ordinary candidate transformation subject to the same actuality and warrant boundaries.

## 59. Self-improvement query

\[
\boxed{?_{R'}Successor_{\mathcal H}(R',R_t).}
\tag{21.1}
\]

The returned successor is a candidate. It does not license itself. Its discriminator is committed before the relevant return, and promotion uses antecedently authorized external returns/checks/warrant.

---

# XXII. Failure localization

A failure should be localized to the smallest implicated relation.

## Syntax/generation defect

The required term cannot be generated from \(\mathsf G_t\).

## Typing/composition defect

The required terms exist but cannot lawfully compose.

## Question-signature defect

The necessary discriminator has no admitted question operation or answer type.

## Frame defect

A question exists but \(\pi_q\) merges a required distinction or has incorrect applicability.

## Observation defect

The protected context/probe repertoire cannot separate alternatives whose difference matters.

## Dynamic defect

The current quotient answers protected observations but a protected continuation does not descend.

## Recovery defect

The active quotient is semantically valid but required provenance/reconstruction/reacquisition capacity is absent.

## Warrant defect

A candidate relation is expressible and testable but lacks non-self-licensing support.

## Binding defect

The required relation cannot be represented in the incumbent language.

This classification replaces unnecessary proliferation of cognitive modules.

---

# XXIII. Repository propagation

The sealed event/evidence architecture remains authoritative. The semantic rebind enters as additive, versioned capability.

## 60. `rci.core`

No authority change. `InquiryState` remains the replay-complete aggregate. It is not the behavioral quotient. Ledger succession remains distinct from binding-level realized succession.

## 61. `rci.questions`

The long-term semantic seam should become:

```text
RelationSchema
QuestionSignature
QuestionFrame
FiberQuery
```

Reference shapes:

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

QuestionSignature {
    id
    version
    relation_schema_key
    bound_ports
    open_ports
    answer_type_ref
}

QuestionFrame {
    signature_key
    domain_policy_id
    classifier_semantics_id
    answer_decoder_id
    comparison_semantics_id
    protected_horizon_id
    reopening_policy_id
}
```

Existing `QuestionContract` remains a versioned compatibility/rendering contract. Do not mutate sealed schemas.

## 62. `rci.orchestration`

The abstract semantic program should be corrected from `Step(q,a,kappa)` to `Ask(q,kappa)` with

```text
kappa : AnswerType(q) -> Program
```

The implementation's existing effect lifecycle already supplies answers later, so this is primarily a semantic correction.

The deterministic scheduler remains the policy choosing among ready obligations.

## 63. `rci.probes`

`ProbeIdentity` already has almost exactly the right identity coordinates for an actualized question frame: contract, role, binding, scope, comparison semantics, applicability, and protected horizon.

A later schema may add an explicit frame reference. Existing traces, predictions, mismatches, raw-return linkage, and semantic deltas remain unchanged in authority meaning.

## 64. `rci.learning`

Generalize the semantics of `RepresentationGap` to distinguish:

```text
missing_relation
missing_operator
missing_question
frame_inadequate
missing_separator
quotient_inadequate
continuation_not_descended
recovery_inadequate
binding_inadequate
```

`LearnedProbeCandidate` becomes a specialized candidate signature/operator extension. Its holdout, redundancy, protected-behavior, attack, and controller checks are reusable admission evidence.

## 65. `rci.compression`

The verified G3A-H contracts are a concrete specialization of `RegQ`:

- consequence factorization -> (12.1);
- continuation compatibility -> (12.2);
- recursive update -> concrete descended operator;
- exact equivalence -> behavioral quotient;
- path residue -> factorization/recovery residue;
- reopening -> `Unlock`;
- representation successor -> capability successor order.

Do not replace these contracts. Add a semantic bridge showing they instantiate the more general structure.

## 66. `rci.formal`

The Boolean/finite-enum AST remains one binding-native relation language. It is not the universal question calculus.

## 67. `rci.memory`

Do not create another authoritative “operator memory” or “question memory” store. The new semantic structures should remain projections/references over existing admitted contracts, procedures, claims, returns, support, and retention records.

## 68. `rci.project`

Keep theory, question/probe, method, representation, evidence, implementation, and authority categories distinct because they authorize different mutations. Semantically they may all be represented as candidate changes to the current presentation or discharge machinery.

The project successor law remains preserve + strict gain + independent warrant.

---

# XXIV. Required new laws

## RQ-001 — Antecedent answer type

The answer type and classification frame of a question must be fixed before a returned answer is used to resolve it.

## RQ-002 — Complete-answer exclusivity

Inside the applicability region, complete answer fibers are mutually exclusive.

## RQ-003 — Exterior is not a sibling

Failure of applicability remains distinct from every alternative answer inside the frame.

## RQ-004 — Partial return is not a complete answer

A decoded response may leave several complete answer cells live.

## RQ-005 — Question equivalence is local

\(\sim_q\) may not be promoted to protected behavioral equivalence without factorization evidence.

## RQ-006 — Refinement is factorization order

A finer frame must determine the coarser answer through an explicit factor map.

## RQ-007 — Shared-port composition is typed

Joined questions must agree on shared relation interfaces.

## RQ-008 — Current output sufficiency does not imply state sufficiency

Protected future continuations must descend.

## RQ-009 — Every active quotient has an unlock contract

A retained abstraction must identify observation, continuation, context, or authority changes that invalidate its license.

## RQ-010 — Promotion preserves factorization provenance

A promoted composite may occlude its implementation path only under an explicit recovery/reopening contract.

## RQ-011 — Improvement is not precision monotonicity

Refinement and abstraction can each be warranted improvements.

## RQ-012 — Question learning is signature extension

A learned question changes the admitted dependent operation signature and is governed as a capability change.

## RQ-013 — Answer-dependent continuation is canonical

Every abstract question step associates each complete answer with a continuation.

## RQ-014 — Discharge authority is typed

Semantic generation cannot fill `Actual`, `Checked`, or `Warrant` ports.

## RQ-015 — Executable quotient is behavioral

Any quotient used as recursive reasoning state must preserve declared behavior and continuation structure.

## RQ-016 — Self-revision uses the same successor law

The reasoning language and implementation may propose successors but cannot provide their own positive warrant.

---

# XXV. Acceptance fixtures

A candidate implementation/formalization of this kernel must pass at least these cases.

1. **One relation, multiple questions.** Opening different ports of `Comp(f,g,h)` produces forward, predecessor, and continuation questions without new primitive question kinds.
2. **Frame-relative exclusion.** A complete answer excludes siblings while applicability exit remains separate.
3. **Partial response.** One return may leave several complete answer cells live.
4. **Refinement.** A successor question splits one prior answer fiber.
5. **Cross-cutting frame.** Two incomparable questions combine by joint refinement with kernel intersection.
6. **Redundant probe.** A probe whose classifier factors through the incumbent representation adds no semantic coordinate.
7. **Learned separator.** A new admitted probe refines the representation exactly when it separates an incumbent class.
8. **Current-answer-only failure.** A quotient preserves current consequence but fails a continuation-descent test and is not licensed as recursive state.
9. **Exact behavioral quotient.** Equivalent states remain equivalent under protected repeated interaction.
10. **Horizon reopening.** A new protected context splits an old quotient if it distinguishes members of one old class.
11. **Continuation reopening.** A new protected operation reopens a quotient if it fails to descend.
12. **Composite promotion.** A repeated operator/inquiry path is replaced under protected equivalence and measured strict gain.
13. **Promotion reopening.** A new protected use can reopen the defining factorization.
14. **Question generation.** A representation gap can produce an inert candidate new question signature/frame and cannot self-admit it.
15. **Self-improvement.** The current presentation can formulate a successor question about its own grammar, quotient, or implementation without self-warrant.
16. **Authority separation.** Repository event history remains distinct from behavioral process history and semantic quotient state.

---

# XXVI. Native mathematical correspondences

These are precedents for the relations above, not additional universal primitives.

## 69. Containers / polynomial functors

The form

\[
P(X)=\sum_{q\in Q}X^{A(q)}
\]

is the standard container/polynomial structure of **shapes** and dependent **positions**. In this binding, question identity is the shape and complete answers are positions; the continuation stored at each position is the answer-dependent future computation.

## 70. Free monads and algebraic effects

Treating `ask_q : A(q)` as an operation yields a free effectful program language. Handlers interpret the operation. This gives one question syntax with different lawful discharge routes without allowing syntax to grant itself authority.

## 71. Interaction trees

Potentially unbounded recursive interaction can be represented as a coinductive free-monad-like tree of events and continuations. This is a native reference model for long-running adaptive inquiry.

## 72. Coalgebra and partition refinement

Coalgebras model state-based behavior as \(X\to FX\). Behavioral equivalence and coalgebraic minimization provide the native form of a retained state that preserves repeated future observation/transition behavior.

## 73. Algebra / coalgebra recursion

Catamorphisms summarize inductively generated structure; coalgebras/anamorphic schemes generate continuing structure from a state. The project should use these notions only where their required functor/algebra structure is present.

## 74. Bialgebraic semantics

A distributive law between syntax and dynamics is the native structure for proving that operational behavior is compositional with respect to generated syntax. This is the strongest identified precedent for the project's composition/behavior compatibility requirement.

## 75. Abstract interpretation

Galois connections, abstraction/concretization, domain refinement, and reduced products are relevant when the retained representation is approximate rather than an exact quotient. They belong to approximate bindings.

## 76. Optics

Lenses/prisms/optics provide a useful implementation precedent for compositional focus and retained surrounding context. They are not required to define questions or exact retained state universally.

---

# XXVII. Revised operational recurrence

\[
\boxed{
\begin{aligned}
\mathsf{Pres}_t
&\to \text{open consequential relation}\\
&\to \text{typed question }q:A(q)\\
&\to Ask(q,\kappa)\\
&\to \text{lawful discharge route}\\
&\to r_t\\
&\to \text{decoded complete/partial answer field}\\
&\to \text{answer-indexed successor}\\
&\to \text{independent check/warrant}\\
&\to \text{representation/presentation update}\\
&\to \text{quotient refinement or abstraction}\\
&\to \text{promotion where reusable}\\
&\to \text{unlock test under changed horizon/repertoire}\\
&\to \mathsf{Pres}_{t+1}.
\end{aligned}
}
\tag{27.1}
\]

The next operation is generated by structural residue, including:

- an open relation port;
- multiple consequential answer cells;
- a protected separator inside a current quotient class;
- failed continuation descent;
- an open support prerequisite;
- a missing generator;
- a missing question operation;
- a missing native method;
- an invalid recovery route;
- binding insufficiency.

No fixed universal workflow is primitive.

---

# XXVIII. Revised canonical invariant

A bounded reasoner is represented by a typed compositional language, a dependent repertoire of inquiry operations, a behavior semantics, retained quotients of that behavior, and an independent warrant structure.

A question is an admitted dependent operation \(q\) with complete answer type \(A(q)\). Its semantic classifier \(\pi_q:D_q\to A(q)\) determines which distinctions count as different complete answers, which distinctions are ignored within one answer class, and which cases lie outside the question's applicability.

An inquiry program is answer-dependent composition. Asking \(q\) does not contain its answer; it supplies a continuation for every possible answer. The answer is supplied later by the discharge route authorized for that question. Semantic generation may propose candidate completions, but actual-return, checking, and warrant ports require their own authority.

Protected future interaction induces behavioral equivalence. A retained representation is exact only when every protected consequence factors through it. It is executable as state only when every protected future continuation also descends through it. The quotient may remain active without finer detail only while its observation, continuation, scope, applicability, recovery, and warrant contract remains valid.

Question refinement and representation refinement are the same kernel operation in different roles: both decrease an induced kernel equivalence. Safe abstraction increases a kernel only where protected behavior still factors. Because improvement is ordered by protected capability rather than raw precision, either refinement or abstraction can be a warranted successor.

A useful composite may be promoted into a reusable operator when its protected behavior matches the original composition and the promotion yields strict operational gain. Its defining factorization, provenance, recovery route, and unlock conditions remain governed by the declared contract.

Learning is a warranted change to future compositional and inquiry capacity. It may add a generator, relation, question, separator, native method, equation, promoted operator, finer or coarser licensed quotient, or a new binding. Memory is the retained structure by which such changes continue to affect future behavior or the cost of recovering it.

The reasoning presentation and implementation are themselves reified into a meta-binding. They may generate candidate successors and their own discriminators. A candidate may acquire standing only through antecedently authorized returns and warrant. Semantic and operational recurrence may continue; positive warrant may not circle.

---

# XXIX. Smallest retained form

If the remainder is lost, retain these equations.

### Typed composition

\[
f:A\to B,
\qquad
g:B\to C,
\qquad
g\circ f:A\to C.
\]

### Question signature

\[
\boxed{q\in Q,\qquad A(q)=\text{complete answer type}.}
\]

### One inquiry step

\[
\boxed{P_Q(X)=\sum_{q\in Q}X^{A(q)}.}
\]

### Inquiry program

\[
\boxed{K::=Return(z)\mid Ask(q,\kappa),\quad\kappa:A(q)\to K.}
\]

### Question semantics

\[
\boxed{\pi_q:D_q\to A(q).}
\]

### Answer fiber

\[
\boxed{F_q(a)=\pi_q^{-1}(a).}
\]

### Refinement

\[
\boxed{
q\preceq r
\iff
\exists c:\pi_q=c\circ\pi_r
\iff
\ker\pi_r\subseteq\ker\pi_q.
}
\]

### Joint refinement

\[
\boxed{\ker(\pi_{q\otimes r})=\ker(\pi_q)\cap\ker(\pi_r).}
\]

### Protected equivalence

\[
\boxed{
f\equiv_{\mathcal H}g
\iff
\forall K\in\mathcal H,\quad Con_K(f)=Con_K(g).
}
\]

### Exact abstraction

\[
\boxed{\forall K\in\mathcal H,\quad Con_K=\bar K\circ\eta.}
\]

### Dynamic descent

\[
\boxed{\eta'\circ a=\bar a\circ\eta.}
\]

### General behavioral quotient

\[
\boxed{F(\eta)\circ\gamma=\bar\gamma\circ\eta.}
\]

### Reopening

\[
\boxed{
Unlock(\eta)=\{\text{new protected observations/continuations/context changes that fail the quotient contract}\}.
}
\]

### Self-improvement

\[
\boxed{?_{R'}Successor_{\mathcal H}(R',R_t).}
\]

### Acceptance

\[
\boxed{Successor\Rightarrow Preserve\land StrictGain\land IndependentWarrant.}
\]

---

# XXX. Final statement

The project does not require separate foundational mechanisms for question formation, observation, retained state, abstraction, sequential behavior, compression, promotion, or self-improvement.

It requires

\[
\boxed{
\textbf{A TYPED GENERATIVE LANGUAGE OF OPERATIONS WHOSE BEHAVIOR IS
OBSERVED THROUGH DEPENDENT QUESTION/ANSWER INTERACTIONS,
QUOTIENTED ONLY BY PROTECTED BEHAVIORAL EQUIVALENCE,
AND CHANGED ONLY THROUGH INDEPENDENTLY WARRANTED SUCCESSION.}
}
\]

Questions supply dependent interaction coordinates. Answers select continuations. Repeated interaction defines behavior. Behavioral equivalence licenses quotienting. Congruence/coalgebra morphisms make the quotient executable. Factorization and recovery contracts make abstraction safe. Promotion compiles repeated compositions. Horizon or repertoire extension reopens insufficient quotients. The same transformation system applies to the reasoning language itself.

That is the proposed canonical kernel.

---

# Appendix A. Repository migration rule

Do not change the sealed implementation merely because this formalization is smaller.

The next project action should be an ordinary recursive-project limitation/successor inquiry.

**Limitation**

> The current semantic specification represents question contracts, learned probes, retained-state quotients, and recursive project successors through separate semantic constructions although their protected behavior may be regenerable from one dependent interaction signature plus behavioral quotient/congruence structure.

**Discriminator**

> Can the candidate kernel regenerate every protected capability of the sealed G1, G2A, G2B, G3A-H, G3R, G3Q, and G3G baselines, with fewer universal semantic primitives and no stronger universal assumptions?

Only if that discriminator passes should the normative specification be replaced.

---

# Appendix B. Source correspondence

The reconstruction preserves these established project findings:

- questions are partially bound relational completion fields;
- questions have completion and prerequisite directions;
- questions are consequential only when different completions lead to protected-different successors;
- transformations compose;
- positive warrant cannot be self-licensing;
- exact compression is consequence factorization;
- executable retained state additionally requires continuation compatibility;
- occlusion requires residual/reopening;
- promotion is stronger than naming;
- learning changes future question/transformation/distinction/search/reopening behavior;
- the current grammar is itself an ordinary inquiry object.

The reconstruction changes their organization by deriving them from the dependent interaction and behavioral quotient structure above.
