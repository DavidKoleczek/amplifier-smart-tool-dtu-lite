"""End to end against the local Docker daemon: launch, exec, destroy. Skipped where Docker is not usable."""

import os
from pathlib import Path
import shutil

import pytest

from dtu_lite import lib
from dtu_lite.capabilities.universe import state
from dtu_lite.capabilities.universe.profile import EXAMPLES_DIRECTORY
from dtu_lite.schemas import DtuLiteError

DOCKER_READY = shutil.which("docker") is not None and lib.check().ok
needs_docker = pytest.mark.skipif(not DOCKER_READY, reason="needs a usable Docker daemon")

ALPINE_PROFILE = """\
name: live
x-dtu:
  description: A twin that does nothing
  twin_machine: box
services:
  box:
    image: alpine:3.20
    command: sleep infinity
    ports: ["{port}:80"]
    healthcheck:
      test: [CMD, "true"]
      interval: 1s
"""


@pytest.fixture
def state_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(state, "STATE_ROOT", tmp_path / "state")
    return tmp_path / "state"


@needs_docker
def test_launch_exec_destroy_round_trip(tmp_path: Path, state_root: Path) -> None:
    profile = tmp_path / "compose.yaml"
    profile.write_text(ALPINE_PROFILE.format(port=18590))

    universe = lib.launch(profile, timeout_seconds=120)
    try:
        assert universe.id.startswith("dtu-live-")
        assert universe.state == "running"
        assert universe.twin_machine == "box"
        assert universe.description == "A twin that does nothing"
        assert [service.name for service in universe.services] == ["box"]
        assert universe.services[0].health == "healthy"
        assert [url.url for url in universe.urls] == ["http://localhost:18590/"]
        assert (state_root / universe.id / "universe.json").is_file()

        result = lib.execute(universe.id, "echo out; echo err >&2; exit 4")
        assert (result.exit_code, result.stdout, result.stderr) == (4, "out\n", "err\n")

        placed = lib.execute(universe.id, "pwd; id -un", workdir="/tmp")
        assert placed.stdout == "/tmp\nroot\n"

        with pytest.raises(DtuLiteError) as raised:
            lib.execute(universe.id, "sleep 30", timeout_seconds=1)
        assert raised.value.code == "timeout"
    finally:
        destroyed = lib.destroy(universe.id)

    assert f"{universe.id}-box-1" in destroyed.removed
    assert f"{universe.id}_default" in destroyed.removed
    assert not (state_root / universe.id).exists()
    with pytest.raises(DtuLiteError) as raised:
        lib.execute(universe.id, "true")
    assert raised.value.code == "universe-not-found"


@needs_docker
def test_a_failing_healthcheck_names_the_container_and_leaves_it_for_inspection(
    tmp_path: Path, state_root: Path
) -> None:
    profile = tmp_path / "compose.yaml"
    profile.write_text(ALPINE_PROFILE.format(port=18591).replace('[CMD, "true"]', '[CMD, "false"]\n      retries: 1'))

    with pytest.raises(DtuLiteError) as raised:
        lib.launch(profile, timeout_seconds=120)

    assert raised.value.code == "unhealthy"
    ids = [path.name for path in state_root.iterdir()]
    assert len(ids) == 1
    assert ids[0] in raised.value.remedy
    lib.destroy(ids[0])


@needs_docker
@pytest.mark.skipif(not os.environ.get("GH_TOKEN"), reason="needs GH_TOKEN for the copilot-cli example")
def test_the_shipped_copilot_example_launches_by_name(state_root: Path) -> None:
    universe = lib.launch("copilot-cli", timeout_seconds=600)
    try:
        assert universe.profile_path == (EXAMPLES_DIRECTORY / "copilot-cli" / "compose.yaml").resolve()
        assert universe.state == "running"

        result = lib.execute(universe.id, "id -un; copilot --version")
        assert result.exit_code == 0
        assert result.stdout.startswith("user\nGitHub Copilot CLI")
    finally:
        lib.destroy(universe.id)
