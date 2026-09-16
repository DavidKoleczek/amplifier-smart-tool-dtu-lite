---
name: dtu-lite
description: >-
  Stands up an isolated, realistic environment from a profile on Docker Compose so software can be cloned, installed, run, and experienced like a real user would, without touching the host. Use when passing tests on your machine is not enough evidence and code must be exercised as though actually deployed. Drive it from the command line as `dtu-lite`, or from Python through `dtu_lite.lib`. Triggers on "dtu-lite".
license: MIT
metadata:
  author: DavidKoleczek
  version: "0.1.0"
  repository: https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite
---

# dtu-lite

Stands up an isolated, realistic environment from a profile on Docker Compose so software can be cloned, installed, run, and experienced like a real user would, without touching the host. Use when passing tests on your machine is not enough evidence and code must be exercised as though actually deployed.

## Install

```bash
# as a CLI
uv tool install git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite

# as a library, from another project
uv add "dtu-lite @ git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite"

# once, without installing
uvx --from git+https://github.com/DavidKoleczek/amplifier-smart-tool-dtu-lite dtu-lite --help
```

Verify with `dtu-lite manifest`, which needs no credentials. The repository is private, so these commands need git access to it.

## Use it

Run `dtu-lite --help`. It prints the tool's skill: when to use it, every capability,
worked invocations, sharp edges, and which files to read. Follow it. Confirm every argument
against `dtu-lite <command> --help` rather than memory.
