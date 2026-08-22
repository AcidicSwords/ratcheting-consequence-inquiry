# Goal: Build Ratcheting Consequence Inquiry as a Working Reference System

Build the Ratcheting Consequence Inquiry (RCI) project defined by the repository's
RCI specification into a coherent, runnable, tested reference implementation.

The implementation specification is the source of truth for what RCI means.
The repository and its executable behavior are the source of truth for what currently
exists. Follow all applicable AGENTS.md instructions and repository-local conventions.

Your job is not merely to reproduce the specification in code or create illustrative
scaffolding. Your job is to make the specified process executable while preserving the
distinctions that make the architecture sound.

## Mission

Implement a system in which:

    formal obligation
        -> typed question contract
        -> plain-language question
        -> untrusted semantic answer
        -> typed provisional claim
        -> lawful claim composition
        -> conflict / counterexample / boundary / prerequisite / support
        -> optional lazy formalization
        -> independent discharge or verification
        -> guarded warranted relation
        -> abstraction refinement or compression
        -> next consequential obligation
        -> recursion

The system must remain well-defined even when semantic answers are poor, inconsistent,
vague, or wrong.

Questions determine the ROLE of the claim being requested.
Answers supply only its semantic PAYLOAD.
A generated claim is never automatically a fact.
Only appropriate warrant may promote a provisional claim into retained hard knowledge.

Contradictions in provisional claims are inquiry events, not fatal errors and not licenses
for arbitrary inference.

The permanent epistemic ratchet is the guarded warranted relation store, not the raw
conversation history and not the current candidate possibility set.

## Architectural invariants

Preserve these throughout the implementation:

1. Claim/fact separation
   Claim[T] must never silently become Warranted[T].

2. Typed question composition
   Every question contract declares the kinds of referents it consumes and the claim
   role it produces. The controller, not the semantic generator, determines this role.

3. Lazy semantic formalization
   Answers may remain opaque typed claims until a consequential operation requires deeper
   structure. Do not require perfect natural-language-to-logic parsing as a prerequisite
   for the system to function.

4. Local contradiction
   Candidate claims may conflict. A contradiction creates a ResolveConflict obligation.
   It must not cause logical explosion or arbitrary deletion of claims.

5. Mandatory adversarial pressure
   Every claimed necessity must be attacked by seeking the consequence without it.
   Every claimed sufficiency must be attacked by seeking the condition without the
   consequence.
   Every claimed prerequisite must be attacked by seeking a route that avoids it.

6. Stretch / squeeze geometry
   Within a consequence class, seek maximal useful variation to destroy incidental
   commonality.
   Across consequence classes, seek minimal consequential differences to locate the
   boundary.

7. Description/control separation
   A relation that predicts or factors a consequence is not automatically actionable.
   Control requires a separately warranted succession or implementation relation.

8. Conditional warrant
   Hard learned relations carry guard, scope, provenance, dependencies, and warrant.
   When a guard stops applying, the relation becomes inactive rather than being erased.

9. Consequence-relative abstraction
   Split representations when protected consequences distinguish states currently merged.
   Merge distinctions only when no protected consequence, protected transition behavior,
   or required control guarantee can inspect them.

10. Acyclic warrant
    Control flow may recurse. Positive warrant may not justify itself.

11. Unknown is valid
    Failure to find a counterexample is not proof of necessity.
    Failure to find a path is not proof of impossibility.
    Failure to distinguish is not proof of equivalence unless the available warrant
    licenses that conclusion.

12. Ratcheting progress
    Search and generation may wander. Retained state should change only through a
    consequential, nonredundant update: new warrant, eliminated possibility, false
    equivalence split, justified equivalence, localized boundary, falsified claim,
    established prerequisite, obstruction, reopening condition, or changed obligation.

## Working method

Use the repository-grounded recursive coding ratchet continuously:

    CONTRACT
        What executable consequence distinguishes success from failure?

    LOCATE
        Where in the current repository is that behavior represented or produced?

    BISECT
        What is the smallest reproducible difference that changes the consequence?

    ATTACK
        Can the current explanation be falsified by a counterexample or alternate path?

    CHANGE
        What is the smallest implementation change that crosses the established boundary?

    VERIFY
        What independent executable return establishes whether the predicted consequence
        actually occurred?

    MINIMIZE / LEARN
        What part of the implementation or explanation can be removed while preserving
        the verified result, and what reusable invariant or test should remain?

    RECUR
        What consequential implementation residual remains?

Do not mechanically narrate this loop. Use it to control the work.

When an implementation assumption fails, do not patch around it blindly. Determine which
assumption, abstraction, interface, or invariant failed; repair the smallest failing
piece; then rerun the affected verification.

## Target architecture

The implementation should converge toward these separable components, while respecting
the actual repository structure:

    InquiryState
        binding
        context
        protected consequences
        candidate claim graph
        warranted conditional theory
        predicate/distinction basis
        abstraction
        transition representation
        obligation set
        warrant dependency graph
        inquiry mode

    QuestionContract
        id
        input roles/types
        output claim role
        well-typedness/precondition
        renderer
        binder
        optional reifier
        verifier/discharge policy
        state update
        next-obligation rules

    Claim
        id
        question role
        bound referents
        semantic payload
        scope
        provenance
        status
        representation level
        dependencies
        conflicts

    FormalCandidate
        source claim
        formal type
        expression/relation
        carrier
        assumptions
        scope

    WarrantedLemma
        guard
        relation
        scope
        warrant class
        dependencies
        certificate/provenance
        source claims

    Obligation
        kind
        carrier
        bound arguments
        scope
        parent obligations
        priority
        status

    BackendAdapter
        encode obligation
        execute query
        decode result
        check warrant

The exact implementation language, module boundaries, and representation choices should
follow repository conventions unless the specification requires otherwise.

## Question system

The full typed question library in the RCI specification is normative.

Do not implement it as a giant hard-coded conversational checklist.

Implement question families as typed contracts whose surface wording can vary while their
formal input/output roles remain stable.

The first useful vertical slice should demonstrate that:

    an obligation selects a question contract;
    the question is rendered;
    an arbitrary semantic answer is accepted as an untrusted Claim[role];
    that claim can participate in lawful subsequent question composition;
    contradictory claims remain representable;
    contradiction produces a repair obligation;
    claims can be promoted only through an explicit warrant path;
    a warranted guarded relation changes active inquiry state;
    the resulting residual selects another question.

This vertical slice is more important than prematurely implementing every formal backend.

## Formal machinery

Introduce formal machinery incrementally and behind interfaces.

Where appropriate, use or model the established structures identified by the specification:

    relational / predicate-transformer semantics for succession;
    predicate abstraction and abstraction/concretization for representations;
    CEGAR-style separator refinement;
    SAT/SMT for necessity and sufficiency attacks;
    MUS/MCS or equivalent conflict localization;
    CHC/PDR-style recursive obligations where appropriate;
    conditional assumption environments for guarded warrant;
    control-refinement relations for abstract-to-concrete action guarantees.

Do not force a formal backend where opaque typed claims are sufficient.
Do not keep claims opaque when a consequential operation requires formal checking.

## Development sequence

Prefer successive verified vertical slices over a large speculative implementation.

Establish, in roughly dependency order:

    A. repository/project skeleton and executable test path;
    B. typed QuestionContract / Claim / Obligation core;
    C. candidate claim graph and contradiction handling;
    D. recursive question-selection and state-update loop;
    E. guarded warranted lemma store and warrant DAG;
    F. lazy reification boundary;
    G. one simple formal discharge backend, preferably sufficient to demonstrate
       necessity/sufficiency counterexample checking;
    H. refinement/compression behavior;
    I. recursive prerequisite / actualization behavior;
    J. additional solver, retrieval, observation, or control backends only after the
       common interface is stable.

This order is a dependency guide, not permission to ignore better evidence from the
repository. If the existing project already establishes later layers, preserve and test
them rather than rebuilding them.

## Testing requirements

Treat the specification's laws as executable invariants wherever practical.

At minimum, build tests demonstrating:

    arbitrary semantic payload cannot directly become hard knowledge;
    conflicting candidate claims do not explode the theory;
    conflict creates a repair obligation;
    necessity claims produce consequence-without-it attacks;
    sufficiency claims produce condition-without-consequence attacks;
    prerequisite claims produce target-without-prerequisite attacks;
    guard deactivation makes a lemma inactive without erasing its warrant;
    abstraction refinement can conservatively recover the previous abstraction;
    protected-consequence-distinct states cannot be compressed together;
    descriptive factorization alone cannot produce a control certificate;
    unknown / unresolved is preserved when warrant is insufficient;
    verified successful updates survive recursion without being silently rediscovered
    as unsupported assumptions.

Run all relevant repository validation after meaningful changes and before declaring a
milestone complete.

## Documentation requirements

Keep the RCI specification as the semantic source of truth.

Keep implementation documentation close to code and concise. If architecture or a
formal contract changes, update the corresponding documentation in the same change.

Do not turn AGENTS.md into the full project specification. It should remain a concise map
to the relevant architecture, test, and design documents.

When the implementation reveals an ambiguity or contradiction in the specification:

    identify the exact conflicting claims;
    determine whether the conflict is definitional, representational, architectural,
    or genuinely semantic;
    prefer the smallest repair that preserves established invariants;
    document the decision and its consequence;
    add a regression test when the issue is executable.

Do not silently reinterpret the specification simply to make implementation easier.

## Autonomy and user interaction

Work autonomously from the repository, specification, tools, tests, and available
documentation whenever possible.

Do not ask the user to resolve information that can be discovered from the repository or
tested directly.

Ask only when an unresolved external choice materially changes the architecture or
desired behavior and cannot be resolved from existing evidence.

When several implementations remain valid, prefer the smallest one that preserves the
required abstractions and leaves clean extension points.

## Definition of success

The project is successful when the repository contains a coherent runnable implementation
in which the question-driven inquiry loop is real rather than descriptive:

    questions instantiate typed provisional claims;
    bad semantic answers remain containable;
    claims compose into further lawful inquiry;
    contradictions generate localized repair;
    consequential claims can be independently checked;
    warrant is conditional and provenance-preserving;
    representation can refine and compress;
    actualization remains distinct from description;
    the inquiry recursively turns unresolved consequential residuals into new obligations;
    and the behavior is demonstrated by executable tests.

Do not optimize for the amount of code produced.

Optimize for the smallest implementation in which these invariants are visibly true,
mechanically testable where possible, and capable of being extended into the full RCI
architecture described by the specification.

Begin by inspecting the repository, all applicable AGENTS.md files, the RCI specification,
existing architecture, and existing tests. Determine the smallest missing vertical slice
that materially advances this goal, implement it, verify it, ratchet what was learned
into tests/documentation, and continue recursively from the remaining consequential
residual.