# Ratcheting Consequence Inquiry

[![CI](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/actions/workflows/ci.yml)

RCI is an offline-first Python 3.12 reference system for question-driven,
consequence-sensitive inquiry. Verified milestones G1, G2A, G2B, and G3A-H implement the event/effect
foundation, finite formalization and warrant, a bounded cognitive spine, deterministic
structural retrieval, provisional retention routes, measured reacquisition,
consolidation, versioned repair, semantic-field evaluation, and learned-probe admission.
RCI v0.5 preserves the v0.4 distinction between the replay-complete aggregate and a protected
consequence-sufficient retained state. G3A-H adds bounded exact history-state contracts,
finite transition fixtures, licensed retained-capability joins, path residue, reopening,
and a warranted representation ratchet. Verified G3R applies the same discipline to project
development: consequential limitations, inert question/method candidates, partial-order
successor frontiers, sealed implementation Goals, isolated exact-head evidence, fresh
review, and externally observed protected promotion. Verified G3Q implements the selected
smallest discriminator: an independently admitted, data-only generated question can become
safely schedulable while every unadmitted candidate remains inert. Other nondominated
roadmap successors remain explicit frontier members pending the next recursive selection.

The package includes immutable records, pure `decide`/`evolve` transitions, deterministic
replay, an append-only SQLite WAL ledger, content-addressed artifacts, finite reference
bindings, a Python SDK, and a Typer CLI. Start an offline manual inquiry with:

```text
uv sync --dev
uv run rci start example
uv run rci step example
uv run rci answer example "backup power is an alternate route"
uv run rci replay example
```

Inspect the full surface with `uv run rci --help`. Backlog reconciliation is dry-run by
default; its human-owned policy is tracked in `.rci/config.toml`.

The canonical development gate is:

```text
uv lock --check
uv sync --dev
uv run python -c "import rci"
uv run pytest -q -m "not optional"
uv sync --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src/rci tests
uv run pytest -q
uv run pytest -q tests/acceptance
uv run rci --help
uv build
```

Test execution requires no network service or credentials. OpenAI and Z3 integrations are
optional extras; Docker is supplementary and is not a local prerequisite.

The verified G1 baseline begins at commit
[`c282712a1ca9e3c166457a0a8beb7d8ee353ea31`](https://github.com/AcidicSwords/ratcheting-consequence-inquiry/commit/c282712a1ca9e3c166457a0a8beb7d8ee353ea31).
Hosted Windows, Linux, extras, and Docker verification is recorded in
[`docs/verification.md`](docs/verification.md).
