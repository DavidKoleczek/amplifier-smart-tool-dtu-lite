# Vision

By default, AI generated software is verified in the environment it was built in. 
Agents claim it worked because the context says so, issues stay unsolved because nothing forced them to consider deployment details, and setup that happens to exist on the dev machine papers over what a real user would hit. 
There is a gap between "tests pass" and "this actually works in the real world."

DTU Lite closes that gap: a complete, isolated environment, stood up on demand from a profile on Docker Compose, that simulates the world the code will live in, 
so it can be cloned, installed, run, and experienced like a real user would. 
It answers "what will reality be like if this were actually deployed?" without touching the host.

Example uses:

- "I want to try out a CLI like OpenAI Codex as a real user would, with its config and API keys provisioned for me, without touching my local setup."
- "I want to run my web app against a real Postgres and open it in my browser, as if it were deployed."
- "I want to install my unpublished repositories as if they were already on GitHub, and see whether the install actually works."

It takes the learnings from [amplifier-bundle-digital-twin-universe](https://github.com/microsoft/amplifier-bundle-digital-twin-universe/) and [amplifier-bundle-gitea](https://github.com/microsoft/amplifier-bundle-gitea) and rebuilds them on Docker Compose, so anyone with Docker gets the same experience on Windows, macOS, and Linux. 
It is a fresh design rather than a port: it shares no profile schema, engine, or state with the original Digital Twin Universe.

## What a universe is

A universe is one Docker Compose project. Every part of it is a service in the same `compose.yaml`:

- The twin: the container the code under test runs in, provisioned from the profile so that it looks like a real user's machine: packages installed, config files in the correct places, and API keys passed through from the host's environment at launch rather than written into the rendered files.
- Dependencies the profile declares, such as a database or a cache.
- Gitea, when the profile publishes local repositories, so they can be cloned and installed over `https://` as if they were on GitHub.
- A gateway, when the profile rewrites URLs or restricts outbound traffic. It is the twin's only route out. 
  - It terminates TLS for rewritten hosts, routes matching `host/path` prefixes such as `github.com/org/repo` to Gitea, tunnels everything else to the real internet untouched, and enforces the allowlist.

The gateway mints a certificate authority the first time it starts. 
The tool owns getting that CA trusted in every image where code runs: it is mounted into every service, installed into the system store at start, and named in the environment variables that git, pip, uv, curl, requests, and Node each consult. 
Trust is a property of the universe, not something each client configures.

A profile with no rewrites and no allowlist renders no gateway, no CA, and no proxy environment. 
The twin sits on one ordinary network with direct internet access, and published repositories are reachable at their Gitea address.

All of this lives on a private Compose network. Nothing on the host is modified: no DNS changes, no firewall rules, no daemons beyond Docker itself.

The universe is reachable from the host in two ways. 
Ports the profile exposes are forwarded to localhost, so a web app in the twin opens in the host's browser at `http://localhost:<port>` and `launch` reports those URLs. 
`exec` runs a command or an interactive shell inside the twin as the provisioned user, so a CLI like OpenAI Codex can be driven exactly as a person would, with its config and keys already in place.

On Linux and macOS the twin is a Linux container. 
On Windows it is a Linux container by default, and a profile can opt into Windows containers when the software under test needs Windows itself, such as a `.exe` installer or PowerShell-first tooling. 
Both modes render the same kind of `compose.yaml` and answer to the same commands.

## Validating DTU Lite with itself

DTU Lite is held to its own standard: it is verified inside a universe, as a real user would install and run it, not on the machine it was developed on. 

A profile can ask for a Docker daemon inside the twin. 
The twin then runs a nested daemon (Docker-in-Docker) and any universe launched from within it lives entirely inside that daemon: the host's Docker sees one privileged container, nothing else. 
The self-validation profile publishes this repository through Gitea and rewrites its GitHub URL, so `uv tool install git+https://github.com/...` inside the twin installs the local checkout as if it were released. 
`exec` then drives `dtu-lite check`, `launch`, `exec`, and `destroy` against a sample profile, and a port the sample exposes is chained out through the twin so the host's browser reaches the inner universe.

Constraints this sets:

- The nested daemon is opt-in per profile, never on by default. It requires a privileged twin, since Docker alone offers no unprivileged path, and a privileged twin weakens the container boundary; the profile says so where it asks for it.
- Only a Linux twin can host a nested daemon. Windows containers cannot.
- `launch` inside the twin reports `localhost` URLs that are true inside the twin; the outer profile must expose the same port for the host to reach them.
- The inner daemon starts with an empty image cache, so the sample profile pulls its images on first use unless the profile keeps `/var/lib/docker` on a named volume.

## Goals

- Docker is the only prerequisite. `check` reports whether it is present and usable. `install` offers to install Docker Desktop or Docker Engine through the platform's package manager (winget, brew, apt/dnf) and only acts with explicit consent. If the system does not allow it, `install` says exactly what to do by hand.
- One interface on every OS. Every command takes the same flags and returns the same JSON on Windows, macOS, and Linux. Platform differences are absorbed inside the tool, never surfaced to the caller.
- From zero to a running universe in one command after Docker is present: `launch --profile profile.yaml`.
- The profile is small and owned by this tool. It describes the twin's base image, packages, files to provision, environment variables to pass through, dependencies, exposed ports, local repos to publish, and URLs to rewrite. The tool renders it into a `compose.yaml` and supporting files that a person can read, edit, and run with plain `docker compose`.
- Windows containers are an option, not a requirement. A profile on Windows can ask for a Windows twin; everything else about the tool stays the same.
- A dashboard, in the style of [mybench-smart-tool](https://github.com/DavidKoleczek/mybench-smart-tool), shows every universe on the machine, what it exposes, and its logs, and lets a person open, shell into, or destroy one without remembering ids.
- The same command set as the Digital Twin Universe smart tool, so agents and skills written against it need only relearn the profile. Deterministic commands run with no model provider configured:

```bash
dtu-lite check
dtu-lite validate-profile --file profile.yaml
dtu-lite launch --profile profile.yaml
dtu-lite list
dtu-lite status --id <id>
dtu-lite exec --id <id> --command "curl -sf localhost:8000/health"
dtu-lite exec --id <id>
dtu-lite file-push --id <id> --source ./src --destination /workspace
dtu-lite file-pull --id <id> --source /var/log/app.log --destination ./
dtu-lite destroy --id <id>
```

Smart commands are model-backed and say so in their help text:

```bash
dtu-lite install
dtu-lite create-profile --description "a FastAPI app on port 8000 using Postgres"
dtu-lite doctor --symptom "the twin cannot reach the database"
```

Serve commands run a local web UI over the same library:

```bash
dtu-lite dashboard
```

- Every result is one JSON document on stdout. Failures carry a stable `code` and a `remedy`.
- The Compose file is the escape hatch. Anything the tool cannot express can be done by editing the rendered `compose.yaml` and relaunching.

## Non-Goals

- Compatibility with the original Digital Twin Universe's profiles, engine, or Incus-based environments.
- VM-level isolation or kernel fidelity. A twin is a container; software that needs its own kernel, systemd as PID 1, or nested virtualization is out of scope. A nested Docker daemon is not virtualization and is in scope as an opt-in.
- Running universes on remote or multiple hosts.
- Managing Docker beyond installing it and confirming it works.

## Principles

- If it needs more than Docker, it does not ship.
- Render, then run. The tool never drives containers through hidden state; every universe is fully described by files on disk that `docker compose` understands.
- Host untouched. Rewriting, publishing, proxying, and certificate trust all happen inside the universe.
- The library is the tool. The CLI and any other surface are thin wrappers over it.
- Deterministic capabilities run with no model provider configured, and never refuse to load without one.
- The intelligence is behind an interface, so another implementation is a new module rather than a rewrite.
- The tool works on Windows, macOS, and Linux seamlessly.
