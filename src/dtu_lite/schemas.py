from datetime import datetime
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, Field

DEFAULT_INTELLIGENCE_MODEL = "gpt-6-astra"
ReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class DtuLiteError(Exception):
    """Raised for any failure the library can name and explain how to fix.

    `code` is a stable slug a caller can branch on, `message` says what went wrong with the specifics,
    and `remedy` says what to do about it.
    """

    def __init__(self, code: str, message: str, remedy: str) -> None:
        super().__init__(f"{message} {remedy}")
        self.code = code
        self.message = message
        self.remedy = remedy


# region: Manifest


class ManifestRequirement(BaseModel):
    """One environment prerequisite; `install` references documentation, never a command."""

    name: str
    purpose: str
    install: str
    optional: bool = False


class Manifest(BaseModel):
    """The structured form of SMART_TOOL.md."""

    smart_tool_format: int
    name: str = Field(pattern=SLUG_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    description: str
    use_cases: list[str]
    platforms: list[str]
    requires: list[ManifestRequirement] = Field(default_factory=list)
    body: str = Field(description="The Markdown below the frontmatter: the skill `--help` renders")


# endregion

# region: Skill


class Capability(NamedTuple):
    """One capability of the tool, as the skill's capability list presents it."""

    name: str
    summary: str
    model_backed: bool


# endregion

# region: Check

Platform = Literal["linux", "macos", "windows"]


class Prerequisite(BaseModel):
    """One thing a universe needs from the host, measured."""

    name: str
    present: bool
    detail: str = Field(description="The version when present, otherwise what the probe saw")
    remedy: str | None = Field(default=None, description="How to make it present, set only when it is not")


class HostReport(BaseModel):
    """Whether this host can run a universe, and why not when it cannot."""

    platform: Platform
    ok: bool
    docker_version: str | None
    compose_version: str | None
    prerequisites: list[Prerequisite]


# endregion

# region: Universe

UniverseState = Literal["starting", "running", "degraded", "stopped"]
Health = Literal["starting", "healthy", "unhealthy"]


class Service(BaseModel):
    """One Compose service of a universe, as Docker reports it now."""

    name: str
    state: str = Field(description="Compose's word: running, exited, created, ...")
    health: Health | None = Field(description="None when the service has no healthcheck")
    image: str


class Url(BaseModel):
    """One of the twin's published ports, as the host reaches it."""

    url: str
    port: int
    path: str
    label: str | None


class Universe(BaseModel):
    """One Compose project the tool launched, measured now."""

    id: str
    name: str
    description: str | None
    profile_path: Path
    twin_machine: str
    state: UniverseState
    services: list[Service]
    urls: list[Url]
    state_path: Path
    created_at: datetime


class ExecResult(BaseModel):
    """What one command in the twin produced. A non-zero exit is a result, not a failure."""

    exit_code: int
    stdout: str
    stderr: str


class Destroyed(BaseModel):
    """What `destroy` took down."""

    id: str
    removed: list[str] = Field(description="Names of the containers, networks, and volumes taken down")


# endregion
