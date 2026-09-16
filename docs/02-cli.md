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

## dtu-lite launch

```bash
dtu-lite launch --profile <name-or-path> [--timeout-seconds 600]
```

`lib.launch()`, printed as JSON. Compose's progress goes to stderr while it runs, so the JSON on stdout stays clean. Exits 1 with the cause and remedy on any launch failure; the remedy names the `destroy` command that clears whatever started.

## dtu-lite exec

```bash
dtu-lite exec --id <id> --command "<shell command>" [--user <user>] [--workdir <path>] [--timeout-seconds 300]
dtu-lite exec --id <id> [--user <user>] [--workdir <path>]
```

With `--command`, `lib.execute()`: prints the `ExecResult` as JSON and exits with the command's own exit code, so `dtu-lite exec ... --command "curl -sf ..." && ...` does the right thing. The JSON is on stdout whatever the code.

Without `--command`, `lib.shell()`: attaches an interactive shell to the terminal, prints nothing, and exits with the shell's exit code. Without a terminal it exits 1 with `no-tty`.

## dtu-lite destroy

```bash
dtu-lite destroy --id <id>
```

`lib.destroy()`, printed as JSON.

## Adding a command

Each command gets a section here: the invocation shape with its options and defaults, which library function it calls, and what it prints and exits with. Argument meanings belong in the library reference, not here.
