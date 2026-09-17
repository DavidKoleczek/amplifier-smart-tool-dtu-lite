"""Command line entry point for DTU Lite."""

import json
from pathlib import Path
from typing import Annotated

import typer

from dtu_lite import lib
from dtu_lite.schemas import DEFAULT_INTELLIGENCE_MODEL, DtuLiteError, ReasoningEffort

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    # Every command answers both flags. The root callback claims `--help` for the skill below, and Click drops a
    # help option name already taken by a parameter, which leaves the root's generated summary on `-h`.
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _print_skill(value: bool) -> None:
    """Answer the root `--help` with the skill the library composes, leaving `-h` to Typer."""
    if value:
        typer.echo(lib.skill())
        raise typer.Exit()


@app.callback()
def cli(
    help: Annotated[
        bool,
        typer.Option(
            "--help", is_eager=True, callback=_print_skill, help="This tool's skill, for an agent driving it."
        ),
    ] = False,
) -> None:
    """Stands up an isolated, realistic environment from a profile on Docker Compose so software can be tested as though actually deployed. Use when passing tests on your machine is not enough evidence and code must run against real dependencies, published local repositories, and rewritten URLs without touching the host"""


@app.command()
def manifest() -> None:
    """Print the tool's manifest as JSON. Deterministic."""
    typer.echo(lib.load_manifest().model_dump_json(indent=2))


@app.command()
def check() -> None:
    """Report whether this host can run a universe: Docker CLI, daemon, and Compose plugin. Deterministic.

    Prints the report as JSON. Exits 0 when everything is present, 1 when something is missing.
    """
    report = lib.check()
    typer.echo(report.model_dump_json(indent=2))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def install(
    yes: Annotated[
        bool, typer.Option("--yes", help="Run the plan's unattended steps; otherwise only show and save it.")
    ] = False,
    accept_license: Annotated[
        bool,
        typer.Option("--accept-license", help="Explicitly accept Docker Desktop's Subscription Service Agreement."),
    ] = False,
    model: Annotated[
        str, typer.Option(help="The intelligence model used to plan and repair.")
    ] = DEFAULT_INTELLIGENCE_MODEL,
    reasoning_effort: Annotated[ReasoningEffort, typer.Option(help="The model's reasoning effort.")] = "low",
    timeout_seconds: Annotated[
        int, typer.Option(min=1, help="Deadline for the whole run, including downloads and startup.")
    ] = 1200,
) -> None:
    """Get Docker working on this host. Model-backed: reads the official Docker docs for this platform and plans
    the install; runs the unattended steps with --yes. Deterministic when Docker is already present.

    Prints InstallReport JSON on stdout, step progress on stderr. Exits 0 on ready or installed, 1 on planned,
    action-required or failed. Raises docs-unreachable, plan-rejected, install-timeout, or a gh preflight error
    with the cause and remedy. Never prompts on stdin.
    """
    report = lib.install(yes, accept_license, model, reasoning_effort, timeout_seconds)
    typer.echo(report.model_dump_json(indent=2))
    if report.outcome not in ("ready", "installed"):
        raise typer.Exit(code=1)


@app.command("validate-profile")
def validate_profile(
    profile: Annotated[
        str, typer.Option(help="A profile name, a Compose file, or a directory holding one. See `--help` for names.")
    ],
) -> None:
    """Check a profile without launching it: Compose, `x-dtu`, the universe invariants, and realism. Deterministic.

    Prints the report as JSON. Exits 0 when it has no errors, 1 when it has any; warnings never change the code.
    Exits 1 with the cause and remedy when the profile cannot be found or Docker is unusable.
    """
    report = lib.validate_profile(profile)
    typer.echo(report.model_dump_json(indent=2))
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def launch(
    profile: Annotated[
        str, typer.Option(help="A profile name, a Compose file, or a directory holding one. See `--help` for names.")
    ],
    timeout_seconds: Annotated[int, typer.Option(help="How long to wait for every healthcheck.")] = 600,
) -> None:
    """Launch a universe from a profile and wait until it is ready. Deterministic.

    Prints the universe as JSON, with its id for `exec` and `destroy`. Compose's progress goes to stderr.
    Exits 1 with the cause and remedy when the profile is invalid, a variable is unset, a port is taken,
    a build fails, or a service never becomes healthy.
    """
    typer.echo(lib.launch(profile, timeout_seconds).model_dump_json(indent=2))


@app.command("list")
def list_() -> None:
    """List every universe launched from this machine, oldest first, measured now. Deterministic.

    Prints a JSON array of universes; an empty machine prints `[]`.
    """
    universes = lib.list_universes()
    typer.echo(json.dumps([universe.model_dump(mode="json") for universe in universes], indent=2))


@app.command()
def status(id: Annotated[str, typer.Option(help="The universe id `launch` printed.")]) -> None:
    """Measure one universe now: its state, services, and the URLs the host can open. Deterministic.

    Prints the universe as JSON, the same shape `launch` printed.
    """
    typer.echo(lib.status(id).model_dump_json(indent=2))


@app.command("exec")
def exec_(
    id: Annotated[str, typer.Option(help="The universe id `launch` printed.")],
    command: Annotated[
        str | None, typer.Option(help="Run this through a login shell in the twin. Omit for an interactive shell.")
    ] = None,
    user: Annotated[str | None, typer.Option(help="Run as this user instead of the twin's own.")] = None,
    workdir: Annotated[str | None, typer.Option(help="Run here instead of the twin's own working directory.")] = None,
    timeout_seconds: Annotated[int, typer.Option(help="How long a command may run; ignored for a shell.")] = 300,
) -> None:
    """Run a command in the twin, or open a shell in it. Deterministic.

    With --command, prints the result as JSON (exit_code, stdout, stderr) and exits with the command's own exit
    code. Without it, attaches an interactive login shell to this terminal and exits with the shell's exit code.
    """
    if command is None:
        raise typer.Exit(code=lib.shell(id, user, workdir))
    result = lib.execute(id, command, user, workdir, timeout_seconds)
    typer.echo(result.model_dump_json(indent=2))
    raise typer.Exit(code=result.exit_code)


@app.command("file-push")
def file_push(
    id: Annotated[str, typer.Option(help="The universe id `launch` printed.")],
    source: Annotated[Path, typer.Option(help="A file or directory on the host.")],
    destination: Annotated[
        str, typer.Option(help="A path in the twin; `docker cp` rules decide where the copy lands.")
    ],
) -> None:
    """Copy a file or directory from the host into the twin, owned by the twin's user. Deterministic.

    Prints the transfer as JSON: where the copy landed and how many files it holds.
    """
    typer.echo(lib.push_files(id, source, destination).model_dump_json(indent=2))


@app.command("file-pull")
def file_pull(
    id: Annotated[str, typer.Option(help="The universe id `launch` printed.")],
    source: Annotated[str, typer.Option(help="A file or directory in the twin.")],
    destination: Annotated[
        Path, typer.Option(help="A path on the host; `docker cp` rules decide where the copy lands.")
    ],
) -> None:
    """Copy a file or directory from the twin onto the host. Deterministic.

    Prints the transfer as JSON: where the copy landed and how many files it holds.
    """
    typer.echo(lib.pull_files(id, source, destination).model_dump_json(indent=2))


@app.command()
def destroy(id: Annotated[str, typer.Option(help="The universe id `launch` printed.")]) -> None:
    """Remove a universe: its containers, networks, volumes, and state. Built images stay. Deterministic.

    Prints what was removed as JSON.
    """
    typer.echo(lib.destroy(id).model_dump_json(indent=2))


def main() -> int:
    try:
        app()
    except DtuLiteError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
