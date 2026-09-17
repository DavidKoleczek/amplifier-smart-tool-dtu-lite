"""Top level entry point for the DTU Lite library."""

from pathlib import Path

from dtu_lite.capabilities.check import check as check_module
from dtu_lite.capabilities.universe import destroy as destroy_module
from dtu_lite.capabilities.universe import execute as execute_module
from dtu_lite.capabilities.universe import files as files_module
from dtu_lite.capabilities.universe import launch as launch_module
from dtu_lite.capabilities.universe import status as status_module
from dtu_lite.capabilities.universe import validate as validate_module
from dtu_lite.core import manifest
from dtu_lite.core import skill as skill_module
from dtu_lite.schemas import Destroyed, ExecResult, HostReport, Manifest, ProfileReport, Transfer, Universe


def load_manifest() -> Manifest:
    """The tool's manifest as structured data, read from the SMART_TOOL.md shipped inside the package."""
    return manifest.load_manifest()


def skill() -> str:
    """The tool's skill: the manifest body and the capability list, wrapped so a reader knows where its files are."""
    return skill_module.skill()


def skill_directory() -> Path:
    """The installed package root, where the files the skill names can be read."""
    return skill_module.skill_directory()


def skill_resources() -> list[str]:
    """The files the skill lists, as paths relative to the skill directory. Every one ships inside the package."""
    return skill_module.skill_resources()


def repository_url() -> str | None:
    """The tool's canonical source, from the package metadata, or None when the package declares none."""
    return skill_module.repository_url()


def check() -> HostReport:
    """Whether this host can run a universe: the Docker CLI, a reachable daemon, and the Compose plugin."""
    return check_module.check()


def validate_profile(profile: str | Path) -> ProfileReport:
    """Whether a profile can be launched, and what would be unrealistic about it if it were."""
    return validate_module.validate_profile(profile)


def launch(profile: str | Path, timeout_seconds: int = 600) -> Universe:
    """From a profile to a running, ready universe: validated, recorded, brought up, and waited on."""
    return launch_module.launch(profile, timeout_seconds)


def list_universes() -> list[Universe]:
    """Every universe launched from this machine, oldest first, each measured against Docker now."""
    return status_module.list_universes()


def status(id: str) -> Universe:
    """One universe, measured against Docker now."""
    return status_module.status(id)


def execute(
    id: str,
    command: str,
    user: str | None = None,
    workdir: str | None = None,
    timeout_seconds: int = 300,
) -> ExecResult:
    """Run one command in the twin through a login shell. A non-zero exit is a result, not a failure."""
    return execute_module.execute(id, command, user, workdir, timeout_seconds)


def shell(id: str, user: str | None = None, workdir: str | None = None) -> int:
    """An interactive shell in the twin, attached to this terminal; returns its exit code."""
    return execute_module.shell(id, user, workdir)


def push_files(id: str, source: Path, destination: str) -> Transfer:
    """Copy a host file or directory into the twin with `docker cp` semantics, owned by the twin's user."""
    return files_module.push_files(id, source, destination)


def pull_files(id: str, source: str, destination: Path) -> Transfer:
    """Copy a file or directory out of the twin onto the host with `docker cp` semantics."""
    return files_module.pull_files(id, source, destination)


def destroy(id: str) -> Destroyed:
    """Remove a universe: every container, network, and volume, and its state directory. Images stay."""
    return destroy_module.destroy(id)
