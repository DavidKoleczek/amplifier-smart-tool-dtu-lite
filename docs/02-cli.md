# CLI Reference

The CLI is a thin wrapper over the [library](01-library.md): one command per capability, taking the same arguments under the same names, and doing nothing the library does not. 
What each argument means and what a capability returns or raises is documented there. This page covers only what the CLI adds: the invocation shape, and what reaches stdout, stderr, and the exit code.

Results go to stdout and diagnostics to stderr. A failure the library can name prints its message to stderr and exits 1; a bad invocation exits 2.

## Help

```
dtu-lite -h                 terse summary for a person: the commands, a line each
dtu-lite --help             the tool's skill, written for an agent driving it
dtu-lite <command> --help   one command in full: arguments, defaults, exit codes
```

`--help` on the tool prints what `lib.skill()` returns; the CLI adds nothing of its own. Every command answers both `-h` and `--help` with the same per-command help.

## dtu-lite manifest

```bash
dtu-lite manifest
```

`lib.load_manifest()`, printed as JSON.

## dtu-lite check

```bash
dtu-lite check
```

`lib.check()`, printed as JSON. Exits 0 when the report says `ok`, 1 when a prerequisite is missing, so `dtu-lite check && dtu-lite launch ...` does the right thing. The report is on stdout either way.

## dtu-lite install

```bash
dtu-lite install [--yes] [--accept-license] [--model ...] [--reasoning-effort low] [--timeout-seconds 1200]
```

`lib.install()`, with `--yes` as `apply=True`, printed as JSON. One progress line per step goes to stderr while `--yes` runs, so a person watching a long download knows it is alive. Exits 0 on `ready` or `installed` and 1 otherwise, so `dtu-lite install --yes && dtu-lite launch ...` behaves like `check`.

## dtu-lite create-profile

```bash
dtu-lite create-profile --description "a FastAPI app on port 8000 using Postgres" [--project .] [--name web-app]
                        [--no-verify] [--keep] [--overwrite] [--max-attempts 3] [--model ...]
                        [--reasoning-effort low] [--timeout-seconds 1800]
```

`lib.create_profile()`, with `--no-verify` as `verify=False`, printed as JSON. One progress line per phase goes to stderr (authoring, validating, launching, checking, destroying, cleaning up); Compose's own progress goes there too through `launch`. The agent's own launches run inside its shell and are not echoed, so the authoring phase is simply long. Exits 0 on `created` or `validated`, 1 on `failed`, and 2 on `--keep` with `--no-verify`.

## dtu-lite validate-profile

```bash
dtu-lite validate-profile --profile <name-or-path>
```

`lib.validate_profile()`, printed as JSON. Exits 0 when the report has no errors and 1 when it has any, so `dtu-lite validate-profile --profile p && dtu-lite launch --profile p` does the right thing. Warnings never change the exit code. The report is on stdout either way.

## dtu-lite launch

```bash
dtu-lite launch --profile <name-or-path> [--timeout-seconds 600]
```

`lib.launch()`, printed as JSON. Compose's progress goes to stderr while it runs, so the JSON on stdout stays clean. Exits 1 with the cause and remedy on any launch failure; the remedy names the `destroy` command that clears whatever started.

## dtu-lite list

```bash
dtu-lite list
```

`lib.list_universes()`, printed as a JSON array. An empty machine prints `[]` and exits 0.

## dtu-lite status

```bash
dtu-lite status --id <id>
```

`lib.status()`, printed as JSON in the same shape `launch` prints.

## dtu-lite exec

```bash
dtu-lite exec --id <id> --command "<shell command>" [--user <user>] [--workdir <path>] [--timeout-seconds 300]
dtu-lite exec --id <id> [--user <user>] [--workdir <path>]
```

With `--command`, `lib.execute()`: prints the `ExecResult` as JSON and exits with the command's own exit code, so `dtu-lite exec ... --command "curl -sf ..." && ...` does the right thing. The JSON is on stdout whatever the code.

Without `--command`, `lib.shell()`: attaches an interactive shell to the terminal, prints nothing, and exits with the shell's exit code. Without a terminal it exits 1 with `no-tty`.

## dtu-lite file-push and file-pull

```bash
dtu-lite file-push --id <id> --source <host path> --destination <twin path>
dtu-lite file-pull --id <id> --source <twin path> --destination <host path>
```

`lib.push_files()` and `lib.pull_files()`, printed as JSON. Exits 1 with `source-not-found` when the source is missing on its side, and `transfer-failed` when `docker cp` refuses the paths.

## dtu-lite destroy

```bash
dtu-lite destroy --id <id>
```

`lib.destroy()`, printed as JSON.

## dtu-lite dashboard

```bash
dtu-lite dashboard [--port <n>] [--host 127.0.0.1]
```

`lib.serve_dashboard()`, printed as JSON: the URL to open and who can reach it. The command then keeps serving until Ctrl+C, which exits 0. Exits 1 with `port-in-use` when `--port` names a held port; without `--port` a free one is chosen.

## Adding a command

Each command gets a section here: the invocation shape with its options and defaults, which library function it calls, and what it prints and exits with. Argument meanings belong in the library reference, not here.
