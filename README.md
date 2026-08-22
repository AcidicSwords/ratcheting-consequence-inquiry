# Ratcheting Consequence Inquiry

RCI is an offline-first Python 3.12 reference system for question-driven,
consequence-sensitive inquiry. Milestone G1 implements the event/effect foundation,
Phase 1 inquiry kernel, Phase 2 finite formalization and warrant foundations, and a
bounded cognitive spine. Later research phases remain explicitly deferred.

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
