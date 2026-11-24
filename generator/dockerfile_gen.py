"""Dockerfile Generator for Vietnam Hosting Universal Docker Image System."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from generator.models import GHCR_NAMESPACE, REPO_ROOT


def _render_debian_dockerfile(
    base_image: str,
    title: str,
    extra_apt: list[str],
    extra_run: list[str],
    env_vars: dict[str, str],
    cmd_entrypoint: str = '["/usr/bin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]',
) -> str:
    apt_pkgs = " ".join(sorted(set(extra_apt)))
    lines = [
        f"# Vietnam Hosting Universal Docker Image — {title}",
        f"# Target Registry (publish required): {GHCR_NAMESPACE}",
        "# Unprivileged runtime compatible with Pterodactyl Wings (/home/container)",
        f"FROM {base_image}",
        "",
        'LABEL org.opencontainers.image.vendor="Vietnam Hosting" \\',
        '      org.opencontainers.image.url="https://vietnam-hosting.net" \\',
        f'      org.opencontainers.image.title="Vietnam Hosting — {title}" \\',
        '      org.opencontainers.image.licenses="MIT"',
        "",
        "ENV DEBIAN_FRONTEND=noninteractive \\",
        "    LANG=C.UTF-8 \\",
        "    LC_ALL=C.UTF-8",
        "",
        "RUN apt-get update \\",
        "    && apt-get install -y --no-install-recommends \\",
        f"        ca-certificates curl wget git tini procps iproute2 dnsutils unzip zip tar nano vim {apt_pkgs} \\",
        "    && rm -rf /var/lib/apt/lists/*",
    ]
    for run_cmd in extra_run:
        lines.extend(["", f"RUN {run_cmd}"])
    lines.extend(
        [
            "",
            "RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \\",
            "    && mkdir -p /opt/vnh /home/container \\",
            "    && chown -R container:container /home/container",
            "",
            "COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh core/proc-limits.sh /opt/vnh/",
            "RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells",
            "",
        ]
    )
    if env_vars:
        env_pairs = " \\\n    ".join(f'{k}="{v}"' for k, v in env_vars.items())
        lines.append(f"ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \\\n    {env_pairs}")
    else:
        lines.append("ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh")

    lines.extend(
        [
            "",
            "USER container",
            "WORKDIR /home/container",
            "STOPSIGNAL SIGTERM",
            f"ENTRYPOINT {cmd_entrypoint}",
            "",
        ]
    )
    return "\n".join(lines)


def _render_alpine_dockerfile(
    base_image: str,
    title: str,
    extra_apk: list[str],
    extra_run: list[str],
    env_vars: dict[str, str],
) -> str:
    apk_pkgs = " ".join(sorted(set(extra_apk)))
    lines = [
        f"# Vietnam Hosting Universal Docker Image — {title}",
        f"# Target Registry (publish required): {GHCR_NAMESPACE}",
        f"FROM {base_image}",
        "",
        'LABEL org.opencontainers.image.vendor="Vietnam Hosting" \\',
        '      org.opencontainers.image.url="https://vietnam-hosting.net" \\',
        f'      org.opencontainers.image.title="Vietnam Hosting — {title}" \\',
        '      org.opencontainers.image.licenses="MIT"',
        "",
        "RUN apk add --no-cache \\",
        f"        bash ca-certificates curl wget git tini procps iproute2 bind-tools unzip zip tar nano vim tzdata {apk_pkgs}",
    ]
    for run_cmd in extra_run:
        lines.extend(["", f"RUN {run_cmd}"])
    lines.extend(
        [
            "",
            "RUN (id -u container >/dev/null 2>&1 || adduser -D -h /home/container -s /bin/bash container) \\",
            "    && mkdir -p /opt/vnh /home/container \\",
            "    && chown -R container:container /home/container",
            "",
            "COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh core/proc-limits.sh /opt/vnh/",
            "RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells",
            "",
        ]
    )
    if env_vars:
        env_pairs = " \\\n    ".join(f'{k}="{v}"' for k, v in env_vars.items())
        lines.append(f"ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \\\n    {env_pairs}")
    else:
        lines.append("ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh")
    lines.extend(
        [
            "",
            "USER container",
            "WORKDIR /home/container",
            "STOPSIGNAL SIGTERM",
            'ENTRYPOINT ["/sbin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]',
            "",
        ]
    )
    return "\n".join(lines)


def _render_rpm_dockerfile(
    base_image: str,
    title: str,
    pkg_mgr: str,
    extra_pkgs: list[str],
    extra_run: list[str],
    env_vars: dict[str, str],
) -> str:
    pkgs = " ".join(sorted(set(extra_pkgs)))
    if pkg_mgr == "zypper":
        install_block = (
            "RUN zypper --non-interactive refresh \\\n"
            f"    && zypper --non-interactive install --no-recommends bash ca-certificates curl wget git procps iproute2 bind-utils unzip zip tar nano vim shadow {pkgs} \\\n"
            "    && zypper clean --all"
        )
    elif pkg_mgr == "pacman":
        install_block = (
            "RUN pacman -Syu --noconfirm \\\n"
            f"    && pacman -S --noconfirm --needed bash ca-certificates curl wget git procps-ng iproute2 bind unzip zip tar nano vim shadow {pkgs} \\\n"
            "    && pacman -Scc --noconfirm"
        )
    else:
        install_block = (
            f"RUN {pkg_mgr} install -y --setopt=install_weak_deps=False --allowerasing \\\n"
            f"        bash ca-certificates curl wget git procps-ng iproute bind-utils unzip zip tar nano vim shadow-utils {pkgs} \\\n"
            f"    && {pkg_mgr} clean all"
        )
    lines = [
        f"# Vietnam Hosting Universal Docker Image — {title}",
        f"# Target Registry (publish required): {GHCR_NAMESPACE}",
        f"FROM {base_image}",
        "",
        'LABEL org.opencontainers.image.vendor="Vietnam Hosting" \\',
        '      org.opencontainers.image.url="https://vietnam-hosting.net" \\',
        f'      org.opencontainers.image.title="Vietnam Hosting — {title}" \\',
        '      org.opencontainers.image.licenses="MIT"',
        "",
        install_block,
    ]
    for run_cmd in extra_run:
        lines.extend(["", f"RUN {run_cmd}"])
    lines.extend(
        [
            "",
            "RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \\",
            "    && mkdir -p /opt/vnh /home/container \\",
            "    && chown -R container:container /home/container",
            "",
            "COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh core/proc-limits.sh /opt/vnh/",
            "RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells",
            "",
        ]
    )
    if env_vars:
        env_pairs = " \\\n    ".join(f'{k}="{v}"' for k, v in env_vars.items())
        lines.append(f"ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \\\n    {env_pairs}")
    else:
        lines.append("ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh")
    lines.extend(
        [
            "",
            "USER container",
            "WORKDIR /home/container",
            "STOPSIGNAL SIGTERM",
            'ENTRYPOINT ["/bin/bash", "/opt/vnh/entrypoint.sh"]',
            "",
        ]
    )
    return "\n".join(lines)


def _render_installer_dockerfile(base_image: str, title: str, family: str) -> str:
    if family == "alpine":
        install_cmd = "RUN apk add --no-cache bash ca-certificates curl wget git jq unzip zip tar gzip xz zstd openssl"
    else:
        install_cmd = (
            "ENV DEBIAN_FRONTEND=noninteractive\n"
            "RUN apt-get update \\\n"
            "    && apt-get install -y --no-install-recommends ca-certificates curl wget git jq unzip zip tar xz-utils bzip2 openssl file \\\n"
            "    && rm -rf /var/lib/apt/lists/*"
        )
    return "\n".join(
        [
            f"# Vietnam Hosting Universal Installer Image — {title}",
            f"FROM {base_image}",
            "",
            'LABEL org.opencontainers.image.vendor="Vietnam Hosting" \\',
            '      org.opencontainers.image.url="https://vietnam-hosting.net" \\',
            f'      org.opencontainers.image.title="Vietnam Hosting Installer — {title}"',
            "",
            install_cmd,
            "COPY core/installer.sh /opt/vnh/installer.sh",
            "RUN chmod 755 /opt/vnh/installer.sh",
            "WORKDIR /mnt/server",
            'CMD ["/bin/bash"]',
            "",
        ]
    )


def generate_all_dockerfiles(dry_run: bool = False) -> list[dict[str, Any]]:
    versions_path = REPO_ROOT / "versions.json"
    if not versions_path.exists():
        return []
    versions = json.loads(versions_path.read_text(encoding="utf-8"))
    generated: list[dict[str, Any]] = []

    for img in versions.get("docker_images", []):
        rel_path = img["dockerfile"]
        family = img.get("family", "debian")
        if family == "installer-debian":
            content = _render_installer_dockerfile(img["base_image"], img["title"], "debian")
        elif family == "installer-alpine":
            content = _render_installer_dockerfile(img["base_image"], img["title"], "alpine")
        elif family == "alpine":
            content = _render_alpine_dockerfile(
                img["base_image"],
                img["title"],
                img.get("extra_packages", []),
                img.get("extra_run", []),
                img.get("env", {}),
            )
        elif family in ("dnf", "zypper", "pacman"):
            content = _render_rpm_dockerfile(
                img["base_image"],
                img["title"],
                family,
                img.get("extra_packages", []),
                img.get("extra_run", []),
                img.get("env", {}),
            )
        elif family == "custom_dockerfile":
            content = img["raw_dockerfile"]
        else:
            content = _render_debian_dockerfile(
                img["base_image"],
                img["title"],
                img.get("extra_packages", []),
                img.get("extra_run", []),
                img.get("env", {}),
            )

        if not dry_run:
            target = REPO_ROOT / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
        generated.append(img)

    return generated
