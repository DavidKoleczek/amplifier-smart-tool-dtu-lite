from typing import Literal, NamedTuple

from pydantic import BaseModel, Field

DEFAULT_INTELLIGENCE_MODEL = "gpt-6-astra"
ReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class DtuLiteError(Exception):
    """Raised for any failure the library can name and explain how to fix."""


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
