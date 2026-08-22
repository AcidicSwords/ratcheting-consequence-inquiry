# AGENTS.md

## Project

This repository is developed as an evolving software system, not as a sequence of
isolated coding tasks.

Read repository-local specifications and instructions before making consequential
changes. Nearby code, executable behavior, tests, types, schemas, configuration, and
tool returns outrank generic implementation priors.

Use the repository's detailed coding/reasoning specification when present. Do not
mechanically narrate it.

---

## Working rhythm

For every consequential implementation obligation:

    CONTRACT
        -> FRESH OBSERVE
        -> COMPARE / LOCATE
        -> BISECT
        -> ATTACK
        -> CLASSIFY
        -> PLAN + SEAL
        -> CHANGE
        -> REOBSERVE
        -> RECONCILE + VERIFY
        -> CHALLENGE
        -> MINIMIZE
        -> LEARN
        -> RECORD / CLEAN
        -> RECUR

Prefer the smallest consequentially sufficient coherent change.

Minimum line count is not minimum engineering change.

---

## Treat the repository as the environment

Use recurring:

    tests
    builds
    type checks
    runtime calls
    traces
    logs
    benchmarks
    structural/code searches
    repository questions

as probes over the evolving system.

Where feasible:

    observe current state
        -> preserve the raw return
        -> then compare with prior comparable returns

Reuse an existing probe when it still observes the relevant relation.

Create a new probe when the current probe set cannot expose a consequential difference.

Same command text does not guarantee the same probe if its inputs, scope, or measurement
meaning changed.

---

## Generated explanations are provisional

Never silently collapse:

    diagnosis != fact

    prediction != actual return
    actual return != interpretation

    query != solve != execute

    possible != necessary

    not found != impossible
    not active != irrelevant
    not distinguished != equivalent

    description != control

    current reconstruction != historical fact

    operational compression != provenance deletion

    state mutation != learning

Repository inspection can establish repository facts within the inspected scope.
Executable behavior requires executable evidence.

---

## Plan before consequential execution

Before an edit, test, migration, destructive command, or other action whose result will
be used as evidence, establish when relevant:

    target
    source state
    assumptions
    proposed mechanism
    expected return
    protected non-regressions
    validation probes

Do not redefine these after observing the return.

Preserve raw tool/environment returns before interpretation.

---

## Attack claims

For a claimed necessity, ask:

    Can the result occur without it?

For a claimed sufficiency, ask:

    Can it remain while the result fails?

For a claimed prerequisite, ask:

    Can the target be reached another way?

Use repository search, focused tests, controlled edits, execution, or formal checks to
answer these whenever possible.

Do not preserve a diagnosis merely because previous work depends on it.

---

## Contradictions and self-repair

When an actual return contradicts the working model:

1. preserve the return;
2. identify the smallest failing assumption, guard, abstraction, dependency, scope, or
   representation;
3. create the corresponding engineering obligation;
4. construct a distinguishing fixture;
5. repair the smallest responsible structure;
6. rerun the affected probes.

If implementation exposes an unrepresented consequential choice in the specification,
treat that as a specification/representation problem.

Do not silently reinterpret the specification to make implementation easier.

---

## Verification

Run the strongest relevant repository-native checks after meaningful changes.

Re-run the same target and protection probes where comparable.

A patch is not evidence that the patch works.

A passing narrow test establishes only the behavior it can discriminate.

Do not claim executable success from plausible code alone.

---

## Learning and repository memory

Move durable learning out of transient chat where appropriate.

Prefer:

    bug -> regression test
    invalid state -> type/schema restriction
    interface assumption -> contract/integration test
    recurring invariant -> assertion/static rule
    architectural decision -> ADR/design note
    stable non-obvious project rule -> concise repository instruction

Do not turn transient hypotheses into durable repository rules.

A change counts as project learning when it changes future:

    probing
    reconstruction
    reasoning
    retrieval
    control
    or implementation behavior.

When current probes cannot expose an important distinction, create a better probe.

Retire probes that become demonstrably redundant.

---

## Context and compression

Keep active only repository structure that can currently:

    affect the target behavior
    discriminate a live explanation
    alter validation
    change a protected consequence

Do not treat everything outside active context as irrelevant.

Preserve the condition under which compressed or inactive structure would become
relevant again.

Reconstruct working context after consequential returns instead of continuing from stale
pre-return assumptions.

---

## Autonomy

Continue autonomously when:

    the protected consequence is clear;
    repository evidence can distinguish outcomes;
    changes are local or safely reversible;
    project invariants remain protected.

Ask the user only when a consequential external choice remains that cannot be resolved
from repository state, project specifications, tools, or safe reversible investigation.

Do not ask merely because multiple reasonable implementation patterns exist.

---

## Stop states

Keep distinct:

    VERIFIED
    IMPOSSIBLE_WITHIN_CURRENT_ENVIRONMENT
    BEHAVIORALLY_EQUIVALENT
    BLOCKED
    RESOURCE_BOUNDED
    UNKNOWN

Do not collapse lack of evidence into resolution.