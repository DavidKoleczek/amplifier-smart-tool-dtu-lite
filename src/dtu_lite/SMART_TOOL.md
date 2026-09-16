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

Deterministic commands (`check`, `validate-profile`, `launch`, `list`, `status`, `exec`,
`file-push`, `file-pull`, `destroy`) run with no model provider configured. Smart commands
(`install`, `create-profile`, `doctor`) are model-backed and say so in their help text. Serve
commands (`dashboard`) run a local web UI over the same library.

## Before writing code

Confirm every capability and argument against `dtu-lite <command> --help` before using it.
Do not fill gaps from memory. The library source beside this file, `lib.py`, carries the
signatures. The repository's `docs/01-library.md` and `docs/02-cli.md` carry the rest.

## Install

```bash
# as a CLI
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite

# as a library, from another project
uv add "dtu-lite @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite"
```

Verify with `dtu-lite manifest`, which needs no credentials. To upgrade, run
`uv tool upgrade dtu-lite`. The repository is private, so both commands need git access to it.

## Prerequisites

Docker is what universes are built on: `dtu-lite check` reports whether it is present and
usable, and `dtu-lite install` offers to install it through the platform's package manager.

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
