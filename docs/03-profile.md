# Profile Reference

A profile is a [Compose file](https://docs.docker.com/reference/compose-file/) with one extra top-level block, `x-dtu`.
Compose ignores `x-*` keys, so the same file runs under plain `docker compose up`; `x-dtu` is what DTU Lite adds on top.
`validate-profile` checks it, and `launch` runs it together with an overlay the tool renders beside it.

Everything Compose can express, the profile expresses the Compose way; this page covers only what the tool reads from it and what it adds.

## Where profiles live

A profile usually belongs to the project it tests, under `.agents/digital-twin-universe/<profile-name>/`. `compose.yaml` is the entry point; the twin's `Dockerfile` and anything it copies in sit beside it.

```
.agents/digital-twin-universe/
  codex-cli/
    compose.yaml
    Dockerfile
    config.toml
  web-app-postgres/
    compose.yaml
    Dockerfile
```

`launch --profile codex-cli` resolves to that directory, searching from the working directory upward to the git root, so it works from any subdirectory of the project. `create-profile` writes here. Nothing else is special about the location: it is where an agent looks first, and where the next agent finds what the last one made.

An environment defined anywhere else launches by path. `launch --profile <path>` takes:

- A Compose file.
- A directory holding `compose.yaml` or `docker-compose.yaml`.
- A directory holding only a `Dockerfile`, which launches as a single-service universe with that service as the twin.

A Compose file without `x-dtu` is a valid profile when it has one service. Add `x-dtu` when it has several, or to serve repositories, rewrite hosts, or restrict egress.

## Example

GitHub Copilot CLI, installed the way its README says to and signed in with the host's `gh` token:

```yaml
# Base of the project name; launch appends a short id.
name: copilot-cli

x-dtu:
  description: GitHub Copilot CLI installed as a user would install it
  twin_machine: copilot

services:
  copilot:
    # The Dockerfile beside this file, built with the universe's network up.
    build: .
    # Read from the host at launch, never written to any file. Unset, it fails with this message.
    environment:
      GH_TOKEN: ${GH_TOKEN:?run `export GH_TOKEN=$(gh auth token)` on the host}
    # Keeps the twin up for exec.
    command: sleep infinity
    # launch waits for this before reporting ready.
    healthcheck:
      test: [CMD, copilot, --version]
```

```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git
RUN useradd -m user
# exec runs as this user, in WORKDIR.
USER user
WORKDIR /home/user
RUN curl -fsSL https://gh.io/copilot-install | bash
ENV PATH="/home/user/.local/bin:${PATH}"
```

Then:

```bash
export GH_TOKEN=$(gh auth token)
dtu-lite launch --profile copilot-cli
dtu-lite exec --id <id> --command 'copilot -p "Reply with exactly the word: dtu-ok" --silent'
dtu-lite exec --id <id>              # interactive: `copilot` opens its TUI, already signed in
```

`${GH_TOKEN:?message}` is Compose's own syntax; `validate-profile` and `launch` both honor it.

Three things make a service a good twin. It runs as a created user, not `root`, the way a person's machine does. Its `command` keeps running, because a base image with no long-running process exits and leaves nothing to `exec` into; anything that needs a secret or has to be up goes in `command`, since `build` does not see runtime environment. And it has a `healthcheck`, so `launch` knows when it is ready.

## `x-dtu`

### `description`

Optional. One or two sentences for `list` and the dashboard.

### `twin_machine`

A profile has one service the software under test is installed and run in, and any number of services it talks to. The first is the twin machine: the stand-in for the user's machine, and the implicit target of `exec`, `file-push`, `file-pull`, and `status`.

`twin_machine` names that service. It can be omitted when the file has one service, or when a service is named `twin`.

### `urls`

Optional. Names and paths for the URLs `launch` reports, by host port. Without it, every published port is reported as `http://localhost:<port>/`.

```yaml
urls:
  - port: 8410
    path: /chat/
    label: Chat UI
```

### `repositories`

Local git repositories served from inside the universe, so the twin can clone and install them from the URL they will have once released. Each has:

- `path`: a repository on the host, relative to the profile. The checked-out branch is served, working tree included, so uncommitted changes are tested too.
- `url`: optional. The URL the repository stands in for, such as `https://github.com/microsoft/amplifier-core`. A trailing `.git` or `/` is ignored. Without `url`, the repository is reachable only at the git server's own address, `http://git:3000/dtu/<repo>`.

A request matches a `url` when the host is the same and the path, with a `.git` at the repository boundary ignored, is the `url` path or continues from it with `/`. Query and fragment take no part, and the comparison ignores case, as GitHub and Gitea do. So `https://github.com/microsoft/amplifier` matches every way a tool reaches that repository over its host:

```
/microsoft/amplifier                                        pip and uv git+https, browsers
/microsoft/amplifier/                                       trailing slash
/microsoft/amplifier.git/info/refs?service=git-upload-pack  git clone, fetch
/microsoft/amplifier/info/refs?service=git-upload-pack      git clone without .git
/microsoft/amplifier.git/git-upload-pack                    git fetch
/microsoft/amplifier.git/git-receive-pack                   git push
/microsoft/amplifier.git/HEAD                               dumb http
/microsoft/amplifier/archive/refs/heads/main.tar.gz         pip install <archive url>
/microsoft/amplifier/releases/download/v1.0.0/x.whl         release assets
/microsoft/amplifier/raw/main/README.md                     raw files via github.com
/microsoft/amplifier?go-get=1                               go modules
/Microsoft/Amplifier.git/info/refs                          case differences
```

and no other repository, however close its name:

```
/microsoft/amplifier-foundation
/microsoft/amplifier_old
/microsoft/amplifierx
/microsoft/amplifier.js
/microsoft/amplifier.wiki.git
/microsoft/amplifier.github.io
/other/amplifier
```

The matched prefix is replaced by the served repository's path and the rest is kept, so `git clone`, `pip install git+https://...`, `uv tool install git+https://...`, and archive downloads all land on the served copy. When several `url`s share a host, the longest path wins.

The unit of rewriting is one repository: serve `amplifier-foundation` and every request for it, on any path, goes to the local copy, while `amplifier`, `amplifier-core`, and every `amplifier-bundle-*` still go to GitHub. To rewrite several, list each one.

Only that host is rewritten. Tools that reach a repository some other way are not: SSH clones are not HTTP; `gh` and uv's GitHub fast path use `api.github.com`; npm's `github:` specifier and GitHub tarballs use `codeload.github.com`; `raw.githubusercontent.com` is its own host. `launch` sets `UV_NO_GITHUB_FAST_PATH=true` so uv falls back to `git fetch`, which is rewritten. The rest go to the real host, and a served repository is not there.

The server is Gitea, so its web UI and API are there too, but nothing in the profile depends on that.

### `rewrites`

Optional. `host/path` prefixes routed to another URL, for anything that is not a repository. The target is usually a service in the same file, which is how a mock stands in for a real host:

```yaml
rewrites:
  - match: api.openai.com
    target: http://openai-mock:8080
```

The twin then calls `https://api.openai.com` with no configuration change and reaches the mock, TLS included. Same matching as `repositories`.

### `allow`

Optional. Hostnames the universe may reach. When present, everything else is refused at the gateway, and the refusal is in the gateway's logs. Served and rewritten hosts are always allowed.

## What `launch` adds

The overlay, rendered into the universe's state directory and run as a second `-f` file, never edits the profile:

- A `git` service when `repositories` is set, populated before anything that depends on it starts.
- A `gateway` service when any `repositories[].url`, `rewrites`, or `allow` is set. It is the only route out. It terminates TLS for rewritten hosts with a CA it mints on first start.
- On every service when the gateway is present: the CA mounted read-only and named in `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `GIT_SSL_CAINFO`, `NODE_EXTRA_CA_CERTS`, `PIP_CERT`, and `CURL_CA_BUNDLE`, with `UV_NATIVE_TLS=true` so uv uses it too; the gateway in `HTTP_PROXY` and `HTTPS_PROXY` with `NO_PROXY=localhost,127.0.0.1,::1`; `UV_NO_GITHUB_FAST_PATH=true` when a `github.com` URL is rewritten; the same values as `build.args` with `build.network` set to the universe's network; and `depends_on` the gateway.
- One network the whole universe shares.

The service names `git` and `gateway` are reserved. A profile with no `repositories[].url`, no `rewrites`, and no `allow` renders no gateway, no CA, and no proxy environment.

## What `validate-profile` checks

`docker compose config` first, so the Compose side is validated by Compose itself, interpolation included, and an unset `${NAME}` fails naming the variable. Then `x-dtu` against its schema, then the invariants that make the file a universe rather than just a Compose project. Errors:

- `x-dtu.twin_machine` names a service that is not in the file, or is missing when there are several services and none is named `twin`.
- A service is named `git` or `gateway`.
- A `repositories[].path` is not a git repository, or `url` has no host and path.
- A service sets `network_mode`, `networks`, `dns`, or `extra_hosts` while the gateway would be present, since each bypasses it.
- A service is gated behind a Compose `profiles:` entry that would leave the twin out.
- Windows and Linux services in one file.

Warnings, since each is legitimate sometimes but usually not what a realistic profile means:

- The twin has no `command`, `entrypoint`, or image `CMD` that keeps running.
- The twin bind-mounts a host path, which mutates the host and stands in for the clone and install a real user would do.
- The twin has no `healthcheck`, so `launch` cannot wait for it to be ready.
- The twin runs as `root`.

## Adapting an existing Compose file

A project that already has a `compose.yaml` and a `Dockerfile` is most of the way there:

1. Copy them into `.agents/digital-twin-universe/<profile-name>/` rather than pointing at the originals, since the profile will diverge from the development setup.
2. Add `x-dtu` with `twin_machine` naming the service the code under test runs in.
3. Replace bind mounts of source code with the clone and install a user would do. Declare the repository under `x-dtu.repositories` and have the `Dockerfile` or `command` install it from its URL.
4. Pass secrets as `${NAME}` in `environment` rather than through a committed `.env`.

A development Compose file mounts source and runs a dev server; a profile installs a release and runs it. Both are ordinary Compose files, so the change is in what the file says, not in how it is written.

## Less common Compose settings the tool honors

- `privileged: true` with a Docker-in-Docker image or an installed daemon gives a nested Docker daemon. This weakens the container boundary and is the profile's decision to make; Linux twins only.
- `platform: windows/amd64` on a Windows host in Windows containers mode gives a Windows twin.
- `depends_on` with `condition: service_healthy` orders dependencies before the twin; `launch` waits on every healthcheck in the file, not only the twin's.

## What the profile does not do

- Update in place. Change the profile and `launch` again; Docker's layer cache makes an unchanged `Dockerfile` prefix free.
- Override package indexes. Serve the repository and install from git instead.
