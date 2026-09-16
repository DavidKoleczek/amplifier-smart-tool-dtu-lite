# Library Reference

Every capability of DTU Lite is reachable from `dtu_lite.lib`.
All other surfaces, including the CLI, are thin wrappers over the library and add no capability of their own.

Each capability has a section with its signature. The other sections, `Failures`, `Profiles`, and `Universe`, define what the capabilities share.
Data shapes are shown as the classes in `dtu_lite/schemas.py`, since that is what a caller gets back.

## Docker access

Everything that touches Docker goes through [python-on-whales](https://github.com/gabrieldemarmiesse/python-on-whales), which drives the `docker` CLI and its Compose plugin from Python with typed results.
It is the only maintained Python route to `docker compose`; the official `docker` SDK speaks the Engine API and has no Compose support, and Compose is what a universe is.
The trade is that the Docker CLI must be on `PATH`, which Docker Desktop and Docker Engine both provide and `check` confirms.
The one place the library runs the CLI itself is `execute` and `shell`: they take the `docker compose ... exec` command python-on-whales builds and run it through `subprocess`, since that is where a timeout, the exit code, and the caller's terminal are.
File transfers use `docker cp` rather than `docker compose cp`, which fails on whole directories.

## Failures

Every failure the library can name is one exception:

```python
class DtuLiteError(Exception):
    code: str  # stable slug to branch on, such as "port-in-use"
    message: str  # what went wrong, with the specifics: the service, the port, the variable
    remedy: str  # what to do about it
```

`str(error)` is the message followed by the remedy, which is what the CLI prints. Each capability lists the codes it raises. Anything else that escapes is a bug.

A result that carries a verdict (`HostReport.ok`, `ProfileReport.ok`) is never raised as an error when the verdict is negative. The verdict is the answer.

## Check

Whether this host can run a universe: the Docker CLI on `PATH`, a daemon answering behind it, and the Compose plugin.
Deterministic; needs no model provider.

```python
def check() -> HostReport
```

```python
class HostReport:
    platform: Literal["linux", "macos", "windows"]
    ok: bool  # every prerequisite present
    docker_version: str | None  # None until the daemon answers
    compose_version: str | None  # None until the plugin answers
    prerequisites: list[Prerequisite]  # in probe order; stops at the first one missing


class Prerequisite:
    name: str  # "docker-cli", "docker-daemon", "docker-compose"
    present: bool
    detail: str  # the version or path when present, otherwise what the probe saw
    remedy: str | None  # set only when not present
```

## Profiles

A profile is a Compose file with an `x-dtu` block; [the profile reference](03-profile.md) is the schema.
Every `profile` argument in this library accepts the same three forms:

- A name, such as `copilot-cli`: the directory `.agents/digital-twin-universe/copilot-cli/`, searched for from the working directory upward to the git root.
- A path to a Compose file.
- A path to a directory, which must hold `compose.yaml` or `docker-compose.yaml`, or, failing both, a `Dockerfile` (not yet implemented).

When a name is not found in the project, it is looked for under the examples shipped inside the package, so `copilot-cli` launches on a fresh install with nothing copied. The name form never accepts a path separator.
Whatever the form, the result is the entry point: a Compose file, or a lone `Dockerfile`, which is treated as a one-service profile with that service as the twin.
When nothing is found, the capability raises `profile-not-found`, saying what it looked for and where.

## Examples

`examples/` in the installed package holds profiles that are complete and known to launch. Each is a directory under the examples root, in the same shape as `.agents/digital-twin-universe/<name>/`, and the skill lists its `compose.yaml` under `<skill_resources>` so an agent reading `--help` can open it and find the `Dockerfile` and anything else it names beside it.

```
examples/
  copilot-cli/      GitHub Copilot CLI installed as a user would, signed in with the host's GH_TOKEN
```

The examples root is `skill_directory() / "examples"`.

## Validate profile

Not yet implemented as a capability; `launch` runs steps 1 to 3 below and stops on any error.

Whether a profile can be launched, and what would be unrealistic about it if it were.
Deterministic. Needs the Docker CLI for `docker compose config`, which does the Compose-side validation.

```python
def validate_profile(profile: str | Path) -> ProfileReport
```

Checks run in this order and every problem is reported, not only the first:

1. Profile resolution.
2. `docker compose config`, with the host's environment. This is Compose's own validation, and it also resolves interpolation, so an unset `${GH_TOKEN:?message}` surfaces here with its message.
3. `x-dtu` against its schema.
4. The universe invariants (errors) and realism checks (warnings) listed in the profile reference.

```python
class ProfileReport:
    path: Path  # the Compose file or Dockerfile that was resolved
    name: str  # the Compose project name base
    twin_machine: str  # the service that will be the twin
    services: list[str]
    ok: bool  # no errors; warnings do not affect it
    errors: list[Finding]
    warnings: list[Finding]


class Finding:
    code: str  # stable slug, such as "twin-missing" or "bind-mount"
    location: str | None  # where in the file, such as "services.copilot.volumes[0]"; None for the whole file
    message: str
    remedy: str
```

Raises `profile-not-found` and `docker-unavailable`.

## Universe

A universe is one Compose project. Its `id` is the project's name, `dtu-<profile name>-<4 hex>`, so `docker compose -p <id> logs` reaches the same stack by hand and `list` can tell two launches of one profile apart.

What the tool renders for a universe lives in its state directory, `~/.dtu-lite/universes/<id>/`: `dtu.yaml`, the overlay (not yet rendered), and `universe.json`, the record: id, name, description, profile path, twin, and creation time. Everything else about a universe is in Docker.
The record is how an id leads back to a universe: every capability that takes an `id` reads it first and raises `universe-not-found` when it is missing. A stack whose directory was deleted by hand is no longer a universe to the tool; `docker compose -p <id> down --volumes` clears it.

Every capability that acts on a universe returns this:

```python
class Universe:
    id: str
    name: str
    description: str | None
    profile_path: Path
    twin_machine: str
    state: Literal["starting", "running", "degraded", "stopped"]
    services: list[Service]
    urls: list[Url]  # the twin's published ports, named by x-dtu.urls (not yet honored: every port is `/`, unlabeled)
    state_path: Path
    created_at: datetime


class Service:
    name: str
    state: str  # Compose's word: "running", "exited", "created", ...
    health: Literal["starting", "healthy", "unhealthy"] | None  # None when it has no healthcheck
    image: str


class Url:
    url: str  # "http://localhost:8410/chat/"
    port: int
    path: str
    label: str | None
```

`state` is `running` when every service is up and healthy, `starting` while any is still becoming healthy, `degraded` when any has exited or is unhealthy, and `stopped` when none is running.

## Launch

From a profile to a running, ready universe, in one call.

```python
def launch(profile: str | Path, timeout_seconds: int = 600) -> Universe
```

Validates the profile and stops on any error. Assigns an id, renders the overlay, then brings the stack up in the order the overlay needs: the `git` and `gateway` services first when the profile calls for them, then image builds with the universe's network in place, then everything else. Returns when every healthcheck passes.
Today, with no overlay, that is `docker compose -p <id> -f <profile> up --build --wait`; Compose's progress is passed through to stderr.

When something fails after containers have started, they are left running so `doctor` and `docker compose logs` have something to read. `destroy` clears them; every failure's remedy names the command.

Raises:

- `profile-not-found`, `profile-invalid` (the report's errors), `docker-unavailable`
- `env-missing`: the variable, and the message the profile gave it
- `port-in-use`: the port, and who holds it when Docker says
- `build-failed`: the service, and the last lines of build output
- `unhealthy`: the service, its healthcheck, and the last lines of its logs
- `timeout`: what was still starting when `timeout_seconds` ran out
- `launch-failed`: anything else Compose refused, with the last lines of its output

## List

Every universe launched from this machine, running or not, oldest first.

```python
def list_universes() -> list[Universe]
```

Every record in the state directory, each measured against Docker in one pass. A universe whose containers are gone appears as `stopped` with no services. An empty machine returns an empty list without touching Docker.

Raises `docker-unavailable`.

## Status

One universe, measured now. `launch` returns the same measurement.

```python
def status(id: str) -> Universe
```

Raises `universe-not-found` and `docker-unavailable`.

## Execute

Run one command in the twin and get its result.

```python
def execute(
    id: str,
    command: str,
    user: str | None = None,        # default: the twin's own user
    workdir: str | None = None,     # default: the twin's own working directory
    timeout_seconds: int = 300,
) -> ExecResult
```

```python
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
```

The command runs through a login shell (`sh -lc`), so `PATH` changes an installer made in `~/.profile` apply, the way they would in a person's terminal.
A non-zero exit is a result, not a failure: `execute(id, "curl -sf localhost:8000/health")` returning `22` is the answer.

Raises `universe-not-found`, `twin-not-running` (with the twin's state), `docker-unavailable`, and `timeout`. On `timeout` the command is abandoned, not killed; whatever it started is still running in the twin.

## Shell

An interactive shell in the twin, attached to the caller's terminal.

```python
def shell(id: str, user: str | None = None, workdir: str | None = None) -> int
```

Returns the shell's exit code when the person leaves it. The shell is `bash -l` when the image has bash, `sh -l` otherwise. In practice only the CLI calls this; it is in the library so the CLI adds nothing.

Raises `universe-not-found`, `twin-not-running`, `docker-unavailable`, and `no-tty` when the caller has no terminal.

## Push and pull files

Copy between the host and the twin.

```python
def push_files(id: str, source: Path, destination: str) -> Transfer
def pull_files(id: str, source: str, destination: Path) -> Transfer
```

```python
class Transfer:
    source: str
    destination: str  # where the copy landed, after the rules below
    files: int  # how many files were copied; a file counts one
```

Same rules as `docker cp`: when the destination is an existing directory the source is placed inside it under its own name, otherwise the source lands at the destination path itself, and the destination's parent must exist. A path in the twin is resolved against `/`, as `docker cp` does, not the twin's working directory.
Pushed files end up owned by the twin's user. `docker cp` alone would leave them owned by `root`, which is a trap when the twin runs as a user.

Raises `universe-not-found`, `twin-not-running`, `source-not-found` (the host path for a push, the twin path for a pull), `transfer-failed` (what `docker cp` refused, with its message), and `docker-unavailable`.

## Destroy

Remove a universe: every container, network, and volume, and its state directory. Built images stay, so the next `launch` of the same profile is fast.

```python
def destroy(id: str) -> Destroyed
```

```python
class Destroyed:
    id: str
    removed: list[str]  # names of the containers, networks, and volumes taken down
```

Raises `universe-not-found` and `docker-unavailable`.

## Intelligence

Model-backed capabilities run through the `Intelligence` protocol in `dtu_lite.intelligence.interface`:

```python
class Intelligence(Protocol):
    implementation: str

    def preflight(self) -> None: ...
    def run(self, request: AgentRequest) -> AgentResult: ...
```

`preflight` raises `DtuLiteError` naming what to configure when the implementation cannot run.
`run` executes one agent: `AgentRequest` holds the prompt, model, optional workspace, and optional output schema; `AgentResult` holds the text, structured output, or error.
Setting `AgentRequest.resume` to an earlier `AgentResult.session_id` continues that session instead of starting a fresh one, so the agent keeps what it learned.

`default_intelligence()` returns the shipped implementation, `CopilotIntelligence`, built on the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) and signed in through the GitHub CLI.
Another implementation is a module satisfying the protocol and a branch in that factory.

## Manifest

The tool's `SMART_TOOL.md` as structured data: the frontmatter as fields, the Markdown below it as `Manifest.body`.

```python
def load_manifest() -> Manifest
```

## Skill

What an agent reads once it has decided to drive the tool: the manifest body and the capability list, wrapped so the reader knows where the tool's files are.
The CLI's `--help` prints exactly this.

```python
def skill() -> str
```

The installed package root, resolved at runtime, where the files the skill names can be read.

```python
def skill_directory() -> Path
```

The files the skill lists under `<skill_resources>`, as paths relative to `skill_directory()`. Every one ships inside the package, so each resolves after installation.

```python
def skill_resources() -> list[str]
```

The tool's canonical source, read from the package metadata's `[project.urls]` `Repository` entry, or `None` when the package declares none.
The skill carries it so a caller that can run the tool but not read its files still reaches the documentation.

```python
def repository_url() -> str | None
```

## Adding a capability

A capability's code goes in `dtu_lite/capabilities/<name>/`, with its prompts and templates beside it, and `lib.py` gets a facade function that imports it and is the only caller of it.
Each capability of the library gets a section here: what it does and when to reach for it, the signature `lib.py` exposes, what each argument means, and what it returns or raises, with the result shape shown as its class.
Model-backed capabilities say so, and take `model` and `reasoning_effort`, defaulting to `DEFAULT_INTELLIGENCE_MODEL` and `low` from `dtu_lite.schemas`.
