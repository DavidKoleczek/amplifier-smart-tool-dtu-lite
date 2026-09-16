"""Top level entry point for the DTU Lite library."""

from pathlib import Path

from dtu_lite.capabilities.check import check as check_module
from dtu_lite.core import manifest
from dtu_lite.core import skill as skill_module
from dtu_lite.schemas import HostReport, Manifest


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
