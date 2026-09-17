# DTU Lite Smart Tool

Stands up an isolated, realistic environment from a profile on Docker Compose so software can be tested as though actually deployed. Use when passing tests on your machine is not enough evidence and code must run against real dependencies, published local repositories, and rewritten URLs without touching the host.

DTU Lite is a [Smart Tool](https://github.com/microsoft/amplifier-smart-tools): a library with a thin CLI over it, whose model-backed capabilities sit behind an interface.

## Installation

Prerequisites:
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- [Docker](https://docs.docker.com/get-started/get-docker/), which every universe runs on.
- [GitHub CLI](https://cli.github.com/) signed in to an account with a [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for the model-backed capabilities.

`dtu-lite install` gets Docker working: review the plan, then use `dtu-lite install --yes` to apply it.

```bash
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite
```

To use it as a library:

```bash
uv add "dtu-lite @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite"
```

To run it once without installing:

```bash
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite dtu-lite --help
```

To teach a coding agent how to use it, install the [skill](skills/dtu-lite/SKILL.md):

```bash
npx skills add DavidKoleczek/amplifier-smart-tool-dtu-lite
```

To update:

```bash
uv tool upgrade dtu-lite
npx skills update dtu-lite   # add --global if the skill was installed globally
```

To uninstall:

```bash
uv tool uninstall dtu-lite
npx skills remove dtu-lite   # add --global if the skill was installed globally
```

Verify an install with `dtu-lite manifest`, which needs no prerequisites and no credentials. The repository is private, so every command above needs git access to it, for example through `gh auth setup-git`.

## Interface

```bash
# Print the tool's manifest as JSON
dtu-lite manifest

# Report whether this host can run a universe: Docker CLI, daemon, and Compose plugin
dtu-lite check

# Plan Docker setup from official docs (model-backed); add --yes to act
dtu-lite install

# Launch a universe from a profile name or Compose file and wait until it is ready
dtu-lite launch --profile <name-or-path>

# Every universe on this machine, or one measured now
dtu-lite list
dtu-lite status --id <id>

# Run a command in the twin, or open a shell in it
dtu-lite exec --id <id> --command "<command>"
dtu-lite exec --id <id>

# Copy files in and out of the twin
dtu-lite file-push --id <id> --source ./src --destination /workspace
dtu-lite file-pull --id <id> --source /var/log/app.log --destination ./

# Take it down
dtu-lite destroy --id <id>
```

Profiles live under `.agents/digital-twin-universe-lite/<name>/` in a project; the tool also ships ready-to-launch [examples](src/dtu_lite/examples). See the [profile reference](docs/03-profile.md).

See the [CLI reference](docs/02-cli.md) for every flag and the [library reference](docs/01-library.md) for the Python surface.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment.
