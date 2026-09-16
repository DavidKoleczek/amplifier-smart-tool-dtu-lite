"""Status and list: what the tool knows about a universe, measured against Docker now."""

from dtu_lite.capabilities.universe import state
from dtu_lite.capabilities.universe.compose import compose_containers, measure
from dtu_lite.schemas import Universe


def status(id: str) -> Universe:
    """One universe, measured now."""
    return measure(state.read(id))


def list_universes() -> list[Universe]:
    """Every universe launched from this machine, oldest first, each measured now."""
    records = state.read_all()
    if not records:
        return []
    containers = compose_containers()
    return [measure(record, containers.get(record.id, [])) for record in records]
