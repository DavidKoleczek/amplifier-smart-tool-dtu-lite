"""Check: whether this host can run a universe."""

import platform
import shutil

from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException

from dtu_lite.schemas import HostReport, Platform, Prerequisite

DOCKER_INSTALL_URL = "https://docs.docker.com/get-started/get-docker/"
COMPOSE_INSTALL_URL = "https://docs.docker.com/compose/install/"
START_DAEMON_REMEDY = "Start Docker: open Docker Desktop, or on Linux run `sudo systemctl start docker`, then rerun."

PLATFORMS: dict[str, Platform] = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}


def check() -> HostReport:
    """Probe the Docker CLI, the daemon behind it, and the Compose plugin, stopping at the first one missing."""
    prerequisites = [_probe_cli()]
    if prerequisites[-1].present:
        prerequisites.append(_probe_daemon())
    if prerequisites[-1].present:
        prerequisites.append(_probe_compose())
    versions = {prerequisite.name: prerequisite.detail for prerequisite in prerequisites if prerequisite.present}
    return HostReport(
        platform=host_platform(),
        ok=all(prerequisite.present for prerequisite in prerequisites),
        docker_version=versions.get("docker-daemon"),
        compose_version=versions.get("docker-compose"),
        prerequisites=prerequisites,
    )


def host_platform() -> Platform:
    """The platform this process runs on, in the names the manifest uses."""
    system = platform.system()
    if system not in PLATFORMS:
        raise RuntimeError(f"DTU Lite runs on Linux, macOS, and Windows; this host reports {system!r}.")
    return PLATFORMS[system]


def _probe_cli() -> Prerequisite:
    path = shutil.which("docker")
    if path is None:
        return Prerequisite(
            name="docker-cli",
            present=False,
            detail="`docker` is not on PATH",
            remedy=f"Install Docker Desktop or Docker Engine from {DOCKER_INSTALL_URL} and open a new shell.",
        )
    return Prerequisite(name="docker-cli", present=True, detail=path)


def _probe_daemon() -> Prerequisite:
    try:
        version = DockerClient().version()
    except DockerException as error:
        return Prerequisite(
            name="docker-daemon", present=False, detail=_first_line(error.stderr), remedy=START_DAEMON_REMEDY
        )
    server_version = version.server.version if version.server is not None else None
    if server_version is None:
        return Prerequisite(
            name="docker-daemon",
            present=False,
            detail="`docker version` reported no server version",
            remedy=START_DAEMON_REMEDY,
        )
    return Prerequisite(name="docker-daemon", present=True, detail=server_version)


def _probe_compose() -> Prerequisite:
    try:
        version = DockerClient().compose.version()
    except DockerException as error:
        return Prerequisite(
            name="docker-compose",
            present=False,
            detail=_first_line(error.stderr),
            remedy=f"Install the Compose plugin from {COMPOSE_INSTALL_URL}; Docker Desktop ships it.",
        )
    return Prerequisite(
        name="docker-compose", present=True, detail=version.strip().removeprefix("Docker Compose version ")
    )


def _first_line(text: str | None) -> str:
    lines = (text or "").strip().splitlines()
    return lines[0] if lines else "no output"
