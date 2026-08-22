# ADR-0012: Recursive project inquiry and repertoire succession

- Status: accepted for G3R
- Date: 2026-08-22
- Requirements: RCI-072 through RCI-076 and RCI-078

## Decision

Treat the verified repository as an ordinary, explicitly typed RCI binding without
creating a second ledger. The binding records a clean `ProjectAnchor`, a demonstrated
`CapabilityLimitation`, inert question/method/successor candidates, a deterministic
partial-order `CapabilityFrontier`, and an immutable `ImplementationGoalContract`.

Theory, question/probe repertoire, method repertoire, representation, Goal
decomposition, and implementation are separate successor kinds. A generated question
is schedulable only after versioned admission and only inside the
`recursive-project-v1` profile. It must expose at least two consequentially distinct
returns and name typed referents, preconditions, comparison policy, downstream
consumers, and falsifying attacks. Admission cannot suppress ordinary inquiry.

A method binding must name the relation, its native field and method, preserved primary
sources, assumptions, applicability checks, license, and whether an adapter is missing.
Admission does not install code. A missing adapter opens a sealed implementation Goal.

Candidate dominance is a partial order over exact shared pins, predecessor
preservation, typed gains, and exact comparable cost axes. Unknown costs and differing
gain sets remain incomparable. The policy selects the smallest reversible candidate
with a lawful discriminator; without one it returns `Unknown`.

## Native-method correspondence

G3R uses counterexample-guided refinement for failed candidates, active-query learning
only where teacher/equivalence assumptions really exist, and typed algorithm-selection
portfolios rather than a universal score. Generate-and-validate patches remain exposed
to independent attacks because tests selected by the patch author can overfit.

Primary method sources preserved for this decision:

- Clarke et al., *Counterexample-Guided Abstraction Refinement*, for the
  candidate/counterexample/refinement recurrence:
  <https://web.stanford.edu/class/cs357/cegar.pdf>;
- Angluin, *Learning Regular Sets from Queries and Counterexamples*, only where the
  membership/equivalence-query assumptions are actually available:
  <https://homepages.math.uic.edu/~lreyzin/papers/angluin87.pdf>;
- Rice, *The Algorithm Selection Problem*, for typed problem/algorithm/performance
  spaces rather than one universal method ranking:
  <https://dblp.org/rec/journals/ac/Rice76>;
- Smith et al., *Is the Cure Worse than the Disease? Overfitting in Automated Program
  Repair*, for the requirement that candidate-selected tests cannot be the sole
  acceptance authority: <https://people.cs.umass.edu/~brun/pubs/pubs/Smith15fse.pdf>.

## Consequences

The plan becomes an object of inquiry but not disposable history. G3A-L remains deferred
until the G3R frontier dispositions it. No new dependency, model authority, arbitrary
question code, source-writing port, or universal scalar quality score is introduced.
