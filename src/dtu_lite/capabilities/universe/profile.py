"""Profile resolution: from a name or path to a Compose file, read through `docker compose config`."""

from pathlib import Path
import re
from typing import Any, NamedTuple

from python_on_whales.exceptions import DockerException

from dtu_lite.capabilities.universe.compose import compose_client, translate_docker_error
from dtu_lite.schemas import DtuLiteError

PROFILE_DIRECTORY = Path(".agents") / "digital-twin-universe"
EXAMPLES_DIRECTORY = Path(__file__).parents[2] / "examples"
COMPOSE_FILE_NAMES = ("compose.yaml", "docker-compose.yaml")
X_DTU = "x-dtu"
IMPLICIT_TWIN = "twin"

ENV_MISSING_PATTERN = re.compile(r"required variable (?P<name>\w+) is missing a value: ?(?P<message>.*)")


class Profile(NamedTuple):
    """A profile after Compose has validated and interpolated it."""

    path: Path
    name: str
    description: str | None
    twin_machine: str
    services: list[str]


def resolve_path(profile: str | Path) -> Path:
    """The Compose file a profile argument names: a path to a file or directory, or a profile name."""
    candidate = Path(profile)
    if candidate.is_file():
        return candidate.resolve()
    if candidate.is_dir():
        return _compose_file_in(candidate)
    name = str(profile)
    if Path(name).name != name:
        raise DtuLiteError(
            "profile-not-found",
            f"{name} does not exist.",
            "Pass a path to a Compose file, a directory holding one, or a profile name.",
        )
    searched = _profile_directories(name)
    for directory in searched:
        if directory.is_dir():
            return _compose_file_in(directory)
    raise DtuLiteError(
        "profile-not-found",
        f"No profile named {name!r}. Looked for: {', '.join(str(directory) for directory in searched)}.",
        f"Create `{PROFILE_DIRECTORY / name}/compose.yaml` in this project, or pass a path to a Compose file.",
    )


def load(profile: str | Path) -> Profile:
    """Resolve a profile and read it back through `docker compose config`, which validates and interpolates it."""
    path = resolve_path(profile)
    try:
        config = compose_client(compose_files=[path]).compose.config(return_json=True)
    except DockerException as error:
        raise _profile_error(path, error) from error
    return _profile_from_config(path, config)


def _profile_from_config(path: Path, config: dict[str, Any]) -> Profile:
    services = list(config.get("services") or {})
    extension = config.get(X_DTU) or {}
    twin_machine = extension.get("twin_machine")
    if twin_machine is None:
        twin_machine = services[0] if len(services) == 1 else IMPLICIT_TWIN
    if twin_machine not in services:
        raise DtuLiteError(
            "profile-invalid",
            f"{path} names no twin: `{X_DTU}.twin_machine` is {twin_machine!r} and the services are {services}.",
            f"Set `{X_DTU}.twin_machine` to the service the software under test runs in.",
        )
    return Profile(
        path=path,
        name=config["name"],
        description=extension.get("description"),
        twin_machine=twin_machine,
        services=services,
    )


def _profile_error(path: Path, error: DockerException) -> DtuLiteError:
    translated = translate_docker_error(error)
    if translated is not None:
        return translated
    stderr = (error.stderr or "").strip()
    missing = ENV_MISSING_PATTERN.search(stderr)
    if missing is not None:
        name = missing.group("name")
        message = missing.group("message").strip() or f"the profile requires {name}"
        return DtuLiteError(
            "env-missing",
            f"{path} needs the environment variable {name}, which is not set: {message}",
            f"Export {name} on the host before launching; it is read at launch and never written to a file.",
        )
    return DtuLiteError(
        "profile-invalid",
        f"`docker compose config` rejected {path}: {stderr}",
        "Fix the Compose file; the message above is Compose's own.",
    )


def _compose_file_in(directory: Path) -> Path:
    for name in COMPOSE_FILE_NAMES:
        if (directory / name).is_file():
            return (directory / name).resolve()
    raise DtuLiteError(
        "profile-not-found",
        f"{directory} holds none of {', '.join(COMPOSE_FILE_NAMES)}.",
        "Add a Compose file to the directory, or pass the path to one directly.",
    )


def _profile_directories(name: str) -> list[Path]:
    """Where a profile name is looked for: `.agents/digital-twin-universe/<name>` from here up to the git root, then the shipped examples."""
    directories: list[Path] = []
    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        directories.append(directory / PROFILE_DIRECTORY / name)
        if (directory / ".git").exists():
            break
    directories.append(EXAMPLES_DIRECTORY / name)
    return directories
