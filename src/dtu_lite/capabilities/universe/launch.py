"""Launch: from a profile to a running, ready universe."""

from pathlib import Path
import re
import sys

from python_on_whales import ClientNotFoundError
from python_on_whales.exceptions import DockerException

from dtu_lite.capabilities.universe import profile as profile_module
from dtu_lite.capabilities.universe import state
from dtu_lite.capabilities.universe.compose import compose_client, measure, translate_docker_error
from dtu_lite.capabilities.universe.state import UniverseRecord
from dtu_lite.schemas import DtuLiteError, Universe

LOG_TAIL = 20
PORT_IN_USE_PATTERN = re.compile(
    r"(?:failed to bind host port [^:]*:(?P<bound>\d+)/\w+: address already in use)"
    r"|(?:Bind for [^:]*:(?P<allocated>\d+) failed: port is already allocated)"
)
UNHEALTHY_PATTERN = re.compile(r"container (?P<container>\S+) is unhealthy")
TIMEOUT_MARKER = "application not healthy after"
BUILD_FAILED_MARKER = "failed to solve"


def launch(profile: str | Path, timeout_seconds: int = 600) -> Universe:
    """Validate the profile, record the universe, bring the stack up, and return once every healthcheck passes."""
    loaded = profile_module.load(profile)
    record = UniverseRecord(
        id=state.new_id(loaded.name),
        name=loaded.name,
        description=loaded.description,
        profile_path=loaded.path,
        twin_machine=loaded.twin_machine,
        created_at=state.now(),
    )
    state.write(record)
    client = compose_client(record.id, [loaded.path])
    try:
        # Compose reports progress on stderr; it is passed through so a person sees the build, and the
        # exception at the end carries the whole of it so a failure can be named.
        for _, line in client.compose.up(build=True, wait=True, wait_timeout=timeout_seconds, stream_logs=True):
            sys.stderr.write(line.decode(errors="replace"))
    except (ClientNotFoundError, DockerException) as error:
        raise _launch_error(record, timeout_seconds, error) from error
    return measure(record)


def _launch_error(record: UniverseRecord, timeout_seconds: int, error: Exception) -> DtuLiteError:
    translated = translate_docker_error(error)
    if translated is not None:
        return translated
    stderr = (getattr(error, "stderr", None) or "").strip()
    left_running = (
        f"Whatever started is left as is under `docker compose -p {record.id}` for inspection; "
        f"`dtu-lite destroy --id {record.id}` clears it."
    )
    port = PORT_IN_USE_PATTERN.search(stderr)
    if port is not None:
        number = port.group("bound") or port.group("allocated")
        return DtuLiteError(
            "port-in-use",
            f"Universe {record.id} could not publish port {number}: something on the host already holds it.",
            f"Free port {number} or change the host side of the `ports` entry in {record.profile_path}. {left_running}",
        )
    if BUILD_FAILED_MARKER in stderr:
        return DtuLiteError(
            "build-failed",
            f"An image build for universe {record.id} failed:\n{_tail(stderr)}",
            f"Fix the Dockerfile the profile at {record.profile_path} builds and launch again. {left_running}",
        )
    unhealthy = UNHEALTHY_PATTERN.search(stderr)
    if unhealthy is not None:
        container = unhealthy.group("container")
        return DtuLiteError(
            "unhealthy",
            f"Container {container} of universe {record.id} failed its healthcheck. Its last log lines:\n"
            f"{_container_logs(container)}",
            f"Fix what the healthcheck in {record.profile_path} probes, or the healthcheck itself. {left_running}",
        )
    if TIMEOUT_MARKER in stderr:
        return DtuLiteError(
            "timeout",
            f"Universe {record.id} was still starting after {timeout_seconds}s.",
            f"Raise `timeout_seconds`, or inspect it with `docker compose -p {record.id} ps` and `logs`. {left_running}",
        )
    return DtuLiteError(
        "launch-failed",
        f"`docker compose up` failed for universe {record.id}:\n{_tail(stderr)}",
        f"Read Compose's message above. {left_running}",
    )


def _container_logs(container: str) -> str:
    try:
        return str(compose_client().container.logs(container, tail=LOG_TAIL)).strip()
    except DockerException as error:
        return f"(logs unavailable: {(error.stderr or '').strip()})"


def _tail(text: str) -> str:
    return "\n".join(text.splitlines()[-LOG_TAIL:])
