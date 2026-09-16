# DTU Lite Smart Tool

Stands up an isolated, realistic environment from a profile on Docker Compose so software can be tested as though actually deployed. Use when passing tests on your machine is not enough evidence and code must run against real dependencies, published local repositories, and rewritten URLs without touching the host.

DTU Lite is a [Smart Tool](https://github.com/microsoft/amplifier-smart-tools): a library with a thin CLI over it, whose model-backed capabilities sit behind an interface.

## Installation

Prerequisites:
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- [Docker](https://docs.docker.com/get-started/get-docker/), which every universe runs on.
- [GitHub CLI](https://cli.github.com/) signed in to an account with a [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for the model-backed capabilities.

From a clone of this repository:

```bash
uv tool install .
```

To use it as a library:

```bash
uv add /path/to/dtu-lite
```

To upgrade the CLI after pulling changes, run `uv tool install .` again with `--force`.

To teach a coding agent how to drive it, install the [skill](skills/dtu-lite/SKILL.md) at `skills/dtu-lite/` with your agent's skills client.

## Interface

```bash
# Print the tool's manifest as JSON
dtu-lite manifest
```

See the [CLI reference](docs/02-cli.md) for every flag and the [library reference](docs/01-library.md) for the Python surface.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment.
