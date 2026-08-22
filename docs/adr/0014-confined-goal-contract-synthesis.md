# ADR-0014: Confined implementation-Goal contract synthesis

- Status: accepted and implemented under G3G; hosted verification pending
- Date: 2026-08-22
- Requirements: RCI-073, RCI-074, RCI-076, and RCI-078

## Context

G3Q can turn an independently admitted, data-only question contract into an ordinary
project obligation. G3R can record a partial-order capability frontier and seal an
immutable `ImplementationGoalContract`. The join between those stages is still supplied
manually by the development orchestrator: a question return and selected frontier member
do not determine a candidate Goal record.

That manual join is useful and remains a lawful bypass, but it is not replayable project
reasoning. It also concentrates several observed development-agent failure modes in one
untyped step: framing drift, stale anchors, roadmap commitment by intuition, generated
command/path injection, post-return acceptance changes, and confusion between confidence
and independent evidence. The system must reduce those failures without granting itself
source, shell, Git, policy, credential, review, merge, release, or deployment authority.

User authorization remains the permission boundary for scoped development and account
actions; it is not treated as technical evidence that a design is correct. Conversely,
the user's decision not to adjudicate implementation details does not give the candidate
authority to weaken its own checks or promote itself.

## Decision

G3G will add a confined, deterministic Goal-candidate compiler between an exact admitted
project-question return and the existing Goal seal:

```text
owned admitted question + exact accepted decode/claim + downstream obligation
  + exact clean anchor + limitation + ready frontier + selected candidate
  -> inert ImplementationGoalCandidate
  -> independent GoalAdmissionDecision
  -> existing immutable ImplementationGoalContract
```

The compiler is a derivation, not a planner and not an actuator. It may compile only
versioned allowlisted profiles. The source claim, accepted decode, compiled question, and
downstream obligation must agree on the exact generated return class and source pins.
`Current`, `Desired`, the separator, expected returns,
predecessor preservation, assumptions, acceptance profile, mutation profile, rollback,
and reopening must be derived from exact owned records or fixed registry data. Returned
prose cannot supply executable commands or repository paths.

Acceptance commands come only from a versioned command registry. The generated profile
must include the complete predecessor gate plus one bounded focused discriminator; it
cannot delete, weaken, reorder, replace, or reinterpret a sealed predecessor check.
Mutation roots come only from a versioned repository-root registry and may never overlap
live authorities, `.github`, Git metadata, credentials, runtime policy, release, or
deployment surfaces. Unknown, stale, foreign, ambiguous, unmatched, or context-mismatched
inputs remain inert.

Generation is not admission. Admission requires an exact candidate fingerprint, a
versioned controller policy, evidence, and one total decision. A generated candidate
cannot admit, seal, execute, review, warrant, or promote itself. The existing
`ImplementationGoalContract` remains the only sealed development contract and its event
meaning is unchanged.

This is a procedural improvement to Codex's repository work, not a model-weight update or
a claim of intrinsic self-knowledge. The durable gain is that transient reasoning is
externalized into typed inputs, deterministic compilation, falsifying tests, immutable
records, and independent returns that a later context can replay or attack.

## Native-method correspondence

The design transports only narrow relations from established work:

- goal-oriented requirements engineering supplies refinement from high-level goals to
  operational constraints and explicit obstacle analysis; it does not make a generated
  Goal correct by itself: <https://www.cs.ucf.edu/~turgut/heng_than.pdf>;
- Jackson and Zave's requirements/specification distinction motivates keeping desired
  environment consequences separate from machine-controllable specification surfaces:
  <https://www.researchgate.net/publication/221553733_Deriving_Specifications_from_Requirements_An_Example>;
- counterexample-guided inductive synthesis supplies the bounded candidate/validator/
  counterexample recurrence and lawful no-solution result; G3G does not claim to synthesize
  programs or inherit a CEGIS correctness theorem:
  <https://people.csail.mit.edu/asolar/papers/thesis.pdf>;
- the existing typed algorithm-selection correspondence remains applicable to the
  nondominated method frontier and does not authorize a universal scalar score:
  <https://dblp.org/rec/journals/ac/Rice76>.

## Consequences

The next implementation Goal is G3G. G3A-L, native-method binding, isolated candidate
actuation, and G4 remain nondominated frontier members, not rejected work. G3G does not
install a method, execute a candidate, alter event meanings sealed through G3Q, add a
dependency, or broaden runtime authority. If the confined compiler cannot derive an exact
Goal without free-form semantic invention, it returns `Unknown` and leaves the manual
orchestrator boundary explicit.
