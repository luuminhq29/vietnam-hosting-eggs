"""Core domain models and constants for Vietnam Hosting Universal Eggs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

EGG_AUTHOR_EMAIL = "eggs@vietnam-hosting.net"
PROVIDER_NAME = "Vietnam Hosting"
PROVIDER_WEBSITE = "https://vietnam-hosting.net"
GHCR_NAMESPACE = "ghcr.io/luuminhq29/yolks"
EXPORTED_AT_DEFAULT = "2026-11-24T00:00:00+00:00"
LAST_UPDATED_DEFAULT = "2026-11-24"

VALID_CATEGORIES = (
    "languages",
    "operating-systems",
    "discord-bots",
    "web-hosting",
    "databases",
    "game-servers",
    "applications",
    "utilities",
)

VALID_STATUSES = ("Stable", "Beta", "Experimental", "Legacy", "Deprecated")
VALID_ARCHITECTURES = ("amd64", "arm64")
VALID_PTDL_FEATURES = frozenset(
    {"eula", "java_version", "pid_limit", "steam_disk_space", "gsl_token"}
)

# Built-in environment variables injected by Pterodactyl Panel & Wings.
PTERODACTYL_BUILTIN_VARS = frozenset(
    {
        "SERVER_MEMORY",
        "SERVER_PORT",
        "SERVER_IP",
        "P_SERVER_UUID",
        "P_SERVER_LOCATION",
        "P_SERVER_ALLOCATION_LIMIT",
        "STARTUP",
        "TZ",
        "USER",
        "HOME",
        "INTERNAL_IP",
        "SERVER_UUID",
        "UUID",
    }
)

DEFAULT_PANEL_VERSIONS = ["1.11.x", "1.12.x"]
DEFAULT_WINGS_VERSIONS = ["1.11.x", "1.12.x"]


@dataclass
class VariableSpec:
    name: str
    description: str
    env_variable: str
    default_value: str
    user_viewable: bool = True
    user_editable: bool = True
    rules: str = "nullable|string|max:255"
    field_type: str = "text"

    def to_ptdl_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "env_variable": self.env_variable,
            "default_value": self.default_value,
            "user_viewable": self.user_viewable,
            "user_editable": self.user_editable,
            "rules": self.rules,
            "field_type": self.field_type,
        }

    def to_ptdl_v1_dict(self) -> dict[str, Any]:
        """PTDL_v1 variable schema omits field_type for full legacy 1.0-1.6 compatibility."""
        return {
            "name": self.name,
            "description": self.description,
            "env_variable": self.env_variable,
            "default_value": self.default_value,
            "user_viewable": self.user_viewable,
            "user_editable": self.user_editable,
            "rules": self.rules,
        }


@dataclass
class EggSpec:
    id: str
    name: str
    category: str
    description: str
    icon: str
    supported_versions: list[str]
    supported_architectures: list[str]
    minimum_ram_mb: int
    recommended_ram_mb: int
    minimum_disk_mb: int
    docker_images: dict[str, str]
    startup: str
    stop: str
    startup_done: str
    install_body: str
    variables: list[VariableSpec] = field(default_factory=list)
    version: str = "1.0.0"
    status: str = "Stable"
    resource_basis: str = "recommended_estimate"
    image_source: str = "upstream_official_yolk"
    custom_docker_images: dict[str, str] = field(default_factory=dict)
    dockerfile_path: str | None = None
    install_container: str = "ghcr.io/parkervcp/installers:debian"
    install_entrypoint: str = "bash"
    features: list[str] | None = None
    file_denylist: list[str] = field(default_factory=list)
    config_files: dict[str, Any] = field(default_factory=dict)
    config_logs: dict[str, Any] = field(default_factory=dict)
    requires_inbound_port: bool = True
    privileged_requirements: dict[str, Any] = field(
        default_factory=lambda: {
            "requires_privileged": False,
            "requires_docker_socket": False,
            "requires_gpu": False,
            "requires_kernel_features": False,
            "notes": "Runs completely unprivileged inside standard Pterodactyl Wings isolation.",
        }
    )
    upstream_license: str = "See upstream repository"
    upstream_url: str = "https://vietnam-hosting.net"
    eula_required: bool = False
    steam_app_id: int | None = None
    notes: str = ""
    security_notes_vi: str = ""
    backup_notes_vi: str = ""
    example_files: dict[str, str] = field(default_factory=dict)
    extra_entrypoint: str | None = None
    healthcheck_mode: str = "process"
    healthcheck_target: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EggSpec":
        raw_vars = data.get("variables", [])
        parsed_vars = [
            v if isinstance(v, VariableSpec) else VariableSpec(**v) for v in raw_vars
        ]
        kwargs = dict(data)
        kwargs["variables"] = parsed_vars
        return cls(**kwargs)
