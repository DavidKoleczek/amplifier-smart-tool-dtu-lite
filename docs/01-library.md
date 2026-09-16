# Library Reference

Every capability of DTU Lite is reachable from `dtu_lite.lib`.
All other surfaces, including the CLI, are thin wrappers over the library and add no capability of their own.

## Docker access

Everything that touches Docker goes through [python-on-whales](https://github.com/gabrieldemarmiesse/python-on-whales), which drives the `docker` CLI and its Compose plugin from Python with typed results.
It is the only maintained Python route to `docker compose`; the official `docker` SDK speaks the Engine API and has no Compose support, and Compose is what a universe is.
The trade is that the Docker CLI must be on `PATH`, which Docker Desktop and Docker Engine both provide and `check` confirms.

## Check

Whether this host can run a universe: the Docker CLI on `PATH`, a daemon answering behind it, and the Compose plugin.
Deterministic; needs no model provider and never raises for a missing prerequisite, since a missing prerequisite is the answer.

```python
def check() -> HostReport
```

`HostReport` carries `platform` (`linux`, `macos`, or `windows`), `ok`, `docker_version`, `compose_version`, and `prerequisites`.
The probes run in dependency order, `docker-cli`, `docker-daemon`, `docker-compose`, and stop at the first one missing, so `prerequisites` lists only what was measured.
Each `Prerequisite` has `name`, `present`, `detail` (the version or path when present, otherwise what the probe saw), and `remedy`, set only when it is not present and saying what to do.
`docker_version` and `compose_version` are `None` until their probe passes.

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
Each capability of the library gets a section here: what it does and when to reach for it, the signature `lib.py` exposes, what each argument means, and what it returns or raises.
Model-backed capabilities say so, and take `model` and `reasoning_effort`, defaulting to `DEFAULT_INTELLIGENCE_MODEL` and `low` from `dtu_lite.schemas`.
