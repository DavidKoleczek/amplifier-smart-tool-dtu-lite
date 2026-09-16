---
name: dtu-lite
description: >-
  Stands up an isolated, realistic environment from a profile on Docker Compose so software can be tested as though actually deployed. Use when passing tests on your machine is not enough evidence and code must run against real dependencies, published local repositories, and rewritten URLs without touching the host. Drive it from the command line as `dtu-lite`, or from Python through
  `dtu_lite.lib`. Triggers on "dtu-lite".
license: MIT
---

# Using dtu-lite

Stands up an isolated, realistic environment from a profile on Docker Compose so software can be tested as though actually deployed. Use when passing tests on your machine is not enough evidence and code must run against real dependencies, published local repositories, and rewritten URLs without touching the host.

## Install

From a clone of the repository:

```bash
# as a CLI
uv tool install .

# as a library, from another project
uv add /path/to/dtu-lite
```

## Use it

Run `dtu-lite --help`. It prints the tool's skill: when to use it, every capability,
worked invocations, sharp edges, and which files to read. Follow it. Confirm every argument
against `dtu-lite <command> --help` rather than memory.
