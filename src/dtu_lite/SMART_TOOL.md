---
smart_tool_format: 1
name: dtu-lite
version: 0.1.0
description: >-
  Stands up an isolated, realistic environment from a profile on Docker Compose so software can be cloned, installed, run, and experienced like a real user would, without touching the host. Use when passing tests on your machine is not enough evidence and code must be exercised as though actually deployed
use_cases:
  - Drive a CLI such as OpenAI Codex as a real user would, with its config files and API keys provisioned, without touching the local setup
  - Run a web app against real dependencies such as Postgres and open it from the host's browser as if it were deployed
  - Install and exercise unpublished local repositories as though they were already on GitHub
  - Reproduce a failure in a disposable environment that leaves the host untouched
platforms:
  - linux
  - macos
  - windows
requires:
  - name: docker
    purpose: >-
      Every universe is a Docker Compose project. Without Docker nothing can be launched;
      `dtu-lite check` reports whether it is present and usable, and `dtu-lite install` offers
      to install it.
    install: https://docs.docker.com/get-started/get-docker/
  - name: gh
    purpose: >-
      Generates the token that signs in to GitHub Copilot. Without it, the model-backed
      capabilities cannot authenticate.
    optional: true
    install: https://cli.github.com/
  - name: github-copilot-subscription
    purpose: >-
      A Copilot subscription on the account signed in to gh powers the model-backed
      capabilities. Without it, only the deterministic capabilities run.
    optional: true
    install: https://github.com/github/copilot-cli#prerequisites
---

Stands up an isolated, realistic environment from a profile on Docker Compose so software can be cloned, installed, run, and experienced like a real user would, without touching the host. Use when passing tests on your machine is not enough evidence and code must be exercised as though actually deployed.

**The library is the tool.** `dtu_lite.lib` holds every capability. The CLI is a thin
wrapper over it, so anything you can do from the shell you can also do from Python.

## When to reach for it

- Passing tests on your machine is not enough evidence, and the code has to run against the
  dependencies, ports, and network it is deployed with.
- A CLI has to be driven the way a person would: `exec` opens a shell in the twin as the
  provisioned user, with config files in place and API keys passed through from the host.
- Something running in the twin has to be reached from the host: exposed ports are forwarded to
  `http://localhost:<port>` and `launch` reports the URLs.
- Local repositories are not published yet, and you want to install them over `https://` as if
  they already were.
- A host must stay untouched: no DNS changes, no firewall rules, no daemons beyond Docker.

## Command surfaces

Deterministic commands run with no model provider configured. Today those are `check`,
`validate-profile`, `launch`, `list`, `status`, `exec`, `file-push`, `file-pull`, and `destroy`; the capability
list below is authoritative. `install` is model-backed unless Docker is already usable, and says so
in its help text. Serve commands run a local web UI over the same
library.

## Before writing code

Run `dtu-lite check` first. It reports whether Docker is present and usable and exits 1 with a
`remedy` per missing prerequisite when it is not. Use `dtu-lite install` to plan the fix;
universe commands need Docker to be usable.
Confirm every capability and argument against `dtu-lite <command> --help` before using it.
Do not fill gaps from memory. The library source beside this file, `lib.py`, carries the
signatures. The repository's `docs/01-library.md`, `docs/02-cli.md`, and `docs/03-profile.md`
carry the rest.

## A first universe

A profile is a Compose file with an `x-dtu` block. `launch --profile <name>` looks for
`.agents/digital-twin-universe-lite/<name>/` in the project, then in the examples shipped under the
skill directory, so the shipped ones launch by name with nothing copied:

```bash
export GH_TOKEN="$(gh auth token)"          # the profile reads it at launch, never writes it
dtu-lite launch --profile copilot-cli       # prints the universe, with its id
dtu-lite exec --id <id> --command 'copilot --version'
dtu-lite exec --id <id>                     # interactive shell as the twin's user
dtu-lite file-push --id <id> --source ./src --destination /home/user
dtu-lite file-pull --id <id> --source /home/user/out.log --destination ./
dtu-lite status --id <id>                   # measured now; `list` shows every universe
dtu-lite destroy --id <id>
```

`examples/copilot-cli/` under the skill directory is that profile: GitHub Copilot CLI installed
the way its README says, as a created user, signed in with the host's token. Read it before
writing a profile of your own; `docs/03-profile.md` in the repository is the schema.
`examples/hello/` is the smallest universe, an Alpine twin with nothing installed: launch it to
try `exec` on a machine you have not used the tool on before.

Every universe launched from this machine leaves a directory under `~/.dtu-lite/universes/<id>/`
until it is destroyed, and its containers keep running. Destroy what you launch.

## Install

```bash
# as a CLI
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite

# as a library, from another project
uv add "dtu-lite @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite"

# once, without installing
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite dtu-lite --help
```

Verify with `dtu-lite manifest`, which needs no credentials. To upgrade, run
`uv tool upgrade dtu-lite`. The repository is private, so these commands need git access to it.

## Prerequisites

Docker is what universes are built on: `dtu-lite check` reports whether it is present and
usable. `dtu-lite install` reads the official docs at run time and plans Docker Desktop's installer
on Windows and macOS, or Docker's apt/dnf repositories on Linux. It only acts with `--yes`.

```bash
dtu-lite install             # show and save a sourced plan; exits 1 for planned
dtu-lite install --yes       # run that plan if the host facts still match
# To explicitly accept Docker Desktop's terms, use the same choice on both calls:
dtu-lite install --accept-license
dtu-lite install --yes --accept-license
```

The report's `outcome` is `ready`, `planned`, `installed`, `action-required`, or `failed`;
only `ready` and `installed` exit 0, and `installed` means a universe was launched and ran on the
new Docker, not just that `check` passes. Follow its single `next` instruction when manual action
remains. No step prompts on stdin. Partial installation is reported, not rolled back.

Deterministic capabilities need only `uv` and Docker. Model-backed capabilities run through GitHub
Copilot, signed in as the GitHub CLI's user: `gh` must be installed and `gh auth login`
completed with an account that has a Copilot subscription. Without that, a model-backed
capability fails immediately and names what to configure; it never falls back to a
deterministic answer.

Runs on Linux, macOS, and Windows. The twin is a Linux container everywhere by default; on
Windows a profile can opt into Windows containers.

## Straight and smart paths

Deterministic capabilities run with no provider configured. Model-backed capabilities go
through GitHub Copilot, signed in as the GitHub CLI's user, and say so in their help text.

## Output and failure contract

Results go to stdout, diagnostics to stderr. A failure prints a message naming what went
wrong and how to fix it, and exits non-zero: 1 for a failure the tool can name, 2 for a
bad invocation. Never treat an empty result as success.

## Choosing a surface

Import the library from Python. Shell out to the CLI from anything that cannot import
Python in-process: a shell script, a CI job, or an agent that can run commands but not
load a Python object. Both reach the same capabilities.
