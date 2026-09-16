"""Command line entry point for DTU Lite."""

from typing import Annotated

import typer

from dtu_lite import lib
from dtu_lite.schemas import DtuLiteError

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


def main() -> int:
    try:
        app()
    except DtuLiteError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
