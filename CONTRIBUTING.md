# Contributing to DTU Lite

## Development Setup

### Prerequisites

Install:

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/): Manages Python environments
- [prek](https://github.com/j178/prek): Used for precommit hooks. Recommended to install through PyPI/uv with `uv tool install prek`. Use `uv tool upgrade prek` to update it.
- [GitHub CLI](https://cli.github.com/) for intelligence features with GitHub Copilot.
- [Node.js](https://nodejs.org/) 22+ and [pnpm](https://pnpm.io/installation), optional: only to change the dashboard's frontend. The compiled dashboard is committed, so running it needs neither.
- [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for intelligent features.

### Initial Setup

1. Clone this repository and change into it.

1. Run the development installation script (sets up the uv env, precommit hooks, and the `reference/` clones):

   ```bash
   uv run setup-for-dev.py
   ```

### Essential Development Commands

*Commands should be run from the repository root, unless otherwise specified.*

#### Precommit hooks

Setup precommit hooks:

```bash
prek install
```

Run precommit hooks manually:

```bash
prek run --all-files
```

#### Python Library Development

Create uv virtual environment and install dependencies:

```bash
uv sync --frozen --all-extras --all-groups
```

To update dependencies and the lock file:

```bash
uv sync -U --all-extras --all-groups
```

Lint code:

```bash
uv run ruff check --fix --config pyproject.toml
```

Format code (also formats code blocks in .md files):

```bash
uv run ruff format --config pyproject.toml
```

Type check:

```bash
uv run ty check .
```

Run tests:

```bash
uv run pytest
```

The full suite launches real universes and takes about a minute on up to eight xdist workers. While iterating, run what is relevant:

```bash
# Everything that does not launch a universe, a few seconds. Needs Docker for `docker compose config`.
uv run pytest -m "not live"

# One live file, or one test in it
uv run pytest tests/test_live_universe.py
uv run pytest tests/test_live_overlay.py -k served_repository

# In-process, for a debugger or -s
uv run pytest -n0 tests/test_live_universe.py -k round_trip -s
```

Each worker hands out host ports from its own range (`free_port` in `tests/conftest.py`), so parallel launches never collide on a port.

#### Dashboard Development

The dashboard is a Vite+TS+React app in `dashboard/`, served by the library from compiled assets in `src/dtu_lite/capabilities/dashboard/static/`.
Those assets are committed, because the tool installs from this git repository and must run with no Node present.
The `dashboard` precommit hook runs `uv run build-dashboard.py` whenever frontend source changes: with pnpm present it installs, lints, formats, type checks, and recompiles; without pnpm it says so and passes, since a Python-only change cannot have touched the frontend.

Install dependencies (also done by `setup-for-dev.py` when pnpm is present):

```bash
pnpm --dir dashboard install --frozen-lockfile
```

Run with hot reload (two terminals):

```bash
uv run dtu-lite dashboard --port 5199
pnpm --dir dashboard dev
```

The Vite dev server proxies `/api` to port 5199; set `DTU_LITE_API_URL` to point it elsewhere.

Lint, format, and type check:

```bash
pnpm --dir dashboard check
```

Compile the assets into the package, then commit them:

```bash
pnpm --dir dashboard build
```

#### References

`reference/` holds gitignored clones of the repositories worth reading while developing this tool. `uv run setup-for-dev.py` clones any that are missing.

#### Conformance

Run the spec's [conformance kit](https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance) against this repository.
The outer `uv run` puts this project's `dtu-lite` on `PATH` for the kit to invoke; the inner one runs the kit with its own inline dependencies:

```bash
uv run -- uv run --no-project https://raw.githubusercontent.com/microsoft/amplifier-smart-tools/main/conformance/run.py .
```
