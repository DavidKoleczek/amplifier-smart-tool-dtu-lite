"""Fixtures shared by the test suite: Docker availability, host ports, state isolation, and git repositories."""

from collections.abc import Callable
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from dtu_lite import lib
from dtu_lite.capabilities.universe import state

NEEDS_DOCKER = "needs_docker"
# A committer the host's global git config cannot change, so a commit works on a machine with no identity set.
GIT = ("git", "-c", "user.email=test@dtu.invalid", "-c", "user.name=DTU Test", "-c", "commit.gpgsign=false")

MakeRepository = Callable[[str, dict[str, str]], Path]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip every `needs_docker` test at once when this machine has no usable daemon, probing only if one asks."""
    if not any(item.get_closest_marker(NEEDS_DOCKER) for item in items):
        return
    if shutil.which("docker") is not None and lib.check().ok:
        return
    skip = pytest.mark.skip(reason="needs a usable Docker daemon")
    for item in items:
        if item.get_closest_marker(NEEDS_DOCKER):
            item.add_marker(skip)


@pytest.fixture
def free_port() -> int:
    """A host port nothing holds right now.

    Binding to port 0 and closing leaves a window in which something else could take it, but that window is far
    smaller than the collision rate of hand-picked literals, and losing it surfaces as the named `port-in-use`.
    """
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def state_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Universe records under the test's own directory, so a test never sees or removes a real universe."""
    monkeypatch.setattr(state, "STATE_ROOT", tmp_path / "state")
    return tmp_path / "state"


@pytest.fixture
def make_repository(tmp_path: Path) -> MakeRepository:
    """Build a git repository on the host with one commit, for a profile to serve."""

    def make(name: str, files: dict[str, str]) -> Path:
        repository = tmp_path / "repositories" / name
        repository.mkdir(parents=True)
        for relative, content in files.items():
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        subprocess.run(["git", "init", "-b", "main", "-q"], cwd=repository, check=True)
        subprocess.run([*GIT, "add", "."], cwd=repository, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", "initial"], cwd=repository, check=True)
        return repository

    return make


@pytest.fixture
def served_repository(make_repository: MakeRepository) -> Path:
    """An installable repository with a known marker in its committed content and in its console script."""
    return make_repository(
        "probe",
        {
            "MARKER.txt": "served-from-the-universe\n",
            "pyproject.toml": (
                "[project]\n"
                'name = "dtu-probe"\n'
                'version = "0.1.0"\n'
                'requires-python = ">=3.10"\n'
                "[project.scripts]\n"
                'dtu-probe = "dtu_probe:main"\n'
                "[build-system]\n"
                'requires = ["hatchling"]\n'
                'build-backend = "hatchling.build"\n'
            ),
            "src/dtu_probe/__init__.py": 'def main() -> None:\n    print("dtu-probe-installed")\n',
        },
    )
