"""Phase 3: All 15 Linux Operating System Eggs with NAT Linux Container Hosting."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec

LINUX_NAT_SECURITY_VI = (
    "- **Phân biệt rõ Container và KVM VPS:** Đây là môi trường **Linux Container không đặc quyền** chạy trên kernel chia sẻ của máy chủ Node (Pterodactyl Wings), **không phải KVM VPS**.\n"
    "- **Không có quyền root thực sự trên host:** Không chạy `--privileged`, không cấp `CAP_SYS_ADMIN`, không mount Docker Socket, không dùng `host` network, không tắt AppArmor/Seccomp và không sử dụng `systemd`.\n"
    "- **Cài đặt phần mềm:** Các gói hệ thống đã được tích hợp khi build Docker Image. Trong container, người dùng cài công cụ trong thư mục `/home/container` qua user-space package managers (`pip --user`, `uv`, `npm`, `cargo`, `mise`, `nix`, static binaries). Không giả mạo quyền `apt install`/`dnf install` root.\n"
    "- **Nhu cầu toàn quyền root / systemd / kernel riêng:** Khách hàng cần sử dụng dịch vụ **KVM VPS riêng biệt** của Vietnam Hosting thay vì vượt giới hạn bảo mật Wings.\n"
    "- **Đăng nhập NAT SSH qua `readme.md`:** Tài khoản mặc định là `ubuntu` (`ssh -p <PORT> ubuntu@<NODE_IP>`) với mật khẩu mặc định `vietnam999` được lưu tại `/home/container/readme.md`. Khi người dùng chỉnh sửa dòng `PASSWORD:` trong `/home/container/readme.md`, mật khẩu SSH NAT tự động đồng bộ ngay lập tức (không cần restart server). Khuyến nghị đổi ngay mật khẩu mặc định `vietnam999` hoặc bật SSH Public Key (`~/.ssh/authorized_keys`) và đặt `ENABLE_SSH_PASSWORD=0`. Đăng nhập `root` qua SSH luôn bị vô hiệu hóa."
)

LINUX_NAT_INSTALL_BODY = r'''
mkdir -p /mnt/server/.ssh/host_keys /mnt/server/.local/bin /mnt/server/scripts /mnt/server/run
chmod 700 /mnt/server/.ssh /mnt/server/.ssh/host_keys

if [[ ! -f /mnt/server/readme.md ]]; then
    cat > /mnt/server/readme.md <<'EOF'
# Vietnam Hosting — NAT Linux Container SSH Access

Thông tin đăng nhập SSH NAT (kết nối: `ssh -p <PORT> ubuntu@<NODE_IP>`):

SSH_USER: ubuntu
PASSWORD: vietnam999

> Hướng dẫn đổi mật khẩu NAT SSH:
> - Sửa trực tiếp giá trị sau `PASSWORD:` ở trên rồi lưu file `readme.md`.
> - Hệ thống tự động đồng bộ mật khẩu SSH NAT mới trong vòng 2 giây (không cần restart server).
> - Khuyến nghị đổi ngay mật khẩu mặc định `vietnam999` hoặc thêm SSH Public Key vào `~/.ssh/authorized_keys`.
> - Đăng nhập `root` qua SSH luôn bị chặn vì lý do bảo mật container.
EOF
    chmod 600 /mnt/server/readme.md
fi

if [[ ! -f /mnt/server/startup.sh ]]; then
    cat > /mnt/server/startup.sh <<'EOF'
#!/usr/bin/env bash
# Vietnam Hosting NAT Linux Container — User Startup Script
# Add your long-running user-space services here (runs under restart-loop protection).
set -euo pipefail
echo "[USER] Startup script initialized inside /home/container."
EOF
    chmod 755 /mnt/server/startup.sh
fi

if [[ ! -f /mnt/server/crontab ]]; then
    cat > /mnt/server/crontab <<'EOF'
# Vietnam Hosting Container User-Space Scheduled Tasks
# Syntax: <interval_seconds> <command>
# Example (commented):
# 3600 /bin/bash /home/container/scripts/example-job.sh
EOF
fi

if [[ ! -f /mnt/server/.bashrc ]]; then
    cat > /mnt/server/.bashrc <<'EOF'
export PATH="$HOME/.local/bin:$PATH"
export PS1='[\u@vietnam-hosting \W]\$ '
EOF
fi
'''

LINUX_NAT_VARS = [
    VariableSpec(
        name="Enable Unprivileged SSH",
        description="Set to 1 to start user-space Dropbear/OpenSSH daemon on SSH_PORT (root login always disabled).",
        env_variable="ENABLE_SSH",
        default_value="1",
        rules="required|boolean",
    ),
    VariableSpec(
        name="Enable readme.md Password SSH",
        description="Set to 1 to allow NAT SSH password login synced live from /home/container/readme.md (default ubuntu / vietnam999). Set 0 for pubkey-only.",
        env_variable="ENABLE_SSH_PASSWORD",
        default_value="1",
        rules="required|boolean",
    ),
    VariableSpec(
        name="SSH Allocation Port",
        description="Dedicated Pterodactyl allocation port for SSH (leave blank to reuse SERVER_PORT).",
        env_variable="SSH_PORT",
        default_value="",
        rules="nullable|integer|between:1024,65535",
    ),
    VariableSpec(
        name="SSH Authorized Public Key",
        description="OpenSSH public key (ssh-ed25519 / ssh-rsa) added to ~/.ssh/authorized_keys.",
        env_variable="SSH_AUTHORIZED_KEYS",
        default_value="",
        rules="nullable|string|max:2048",
    ),
    VariableSpec(
        name="Enable User-Space Scheduler",
        description="Set to 1 to enable container-safe scheduled tasks from ~/crontab.",
        env_variable="ENABLE_CRON",
        default_value="1",
        rules="required|boolean",
    ),
    VariableSpec(
        name="User Startup Script",
        description="Relative path to user startup script managed with restart-loop protection.",
        env_variable="STARTUP_SCRIPT",
        default_value="startup.sh",
        rules="nullable|string|max:128",
    ),
    VariableSpec(
        name="Max Restart Attempts",
        description="Maximum restarts within 60 seconds before halting to prevent restart loops.",
        env_variable="VNH_MAX_RESTARTS",
        default_value="5",
        rules="required|integer|between:1,20",
    ),
]


def _make_linux_egg(
    egg_id: str,
    distro_name: str,
    versions: list[str],
    tag: str,
    dockerfile_rel: str,
    arches: list[str],
    upstream_url: str,
    upstream_license: str,
    status: str = "Stable",
    extra_note: str = "",
    official_fallback: dict[str, str] | None = None,
) -> EggSpec:
    images: dict[str, str] = {}
    if official_fallback:
        images.update(official_fallback)
        image_source = "hybrid_official_and_ghcr"
    else:
        image_source = "requires_ghcr_build"
    images[f"{distro_name} (Vietnam Hosting GHCR)"] = f"{GHCR_NAMESPACE}:{tag}"

    desc = (
        f"Unprivileged {distro_name} NAT Linux container compatible with Pterodactyl Console, "
        f"Wings SFTP, user-space SSH (pubkey-only), persistent storage, and container-safe task scheduling. "
        f"Not a KVM VPS (no root/systemd/privileged mode)."
    )
    if extra_note:
        desc += f" {extra_note}"

    return EggSpec(
        id=egg_id,
        name=f"Vietnam Hosting — {distro_name} (NAT Linux Container)",
        category="operating-systems",
        description=desc,
        icon=egg_id.split("-")[0],
        supported_versions=versions,
        supported_architectures=arches,
        minimum_ram_mb=256,
        recommended_ram_mb=512,
        minimum_disk_mb=1024,
        status=status,
        image_source=image_source,
        dockerfile_path=dockerfile_rel,
        docker_images=images,
        custom_docker_images={distro_name: f"{GHCR_NAMESPACE}:{tag}"},
        features=["pid_limit"],
        startup=(
            'if [[ -x /opt/vnh/nat-ssh.sh ]]; then exec /bin/bash /opt/vnh/nat-ssh.sh; '
            'else echo "VIETNAM HOSTING CONTAINER READY (Fallback Shell)"; exec /bin/bash; fi'
        ),
        stop="shutdown",
        startup_done="VIETNAM HOSTING CONTAINER READY",
        install_body=LINUX_NAT_INSTALL_BODY,
        variables=list(LINUX_NAT_VARS),
        requires_inbound_port=True,
        upstream_license=upstream_license,
        upstream_url=upstream_url,
        notes=extra_note or "Unprivileged NAT container with persistent SSH host keys and Wings SFTP.",
        security_notes_vi=LINUX_NAT_SECURITY_VI,
        backup_notes_vi=(
            "- Toàn bộ dữ liệu người dùng, khóa SSH (`/home/container/.ssh/host_keys`), script và ứng dụng user-space nằm trong `/home/container`.\n"
            "- Sao lưu trực tiếp qua Pterodactyl Panel Backup hoặc rsync/SFTP qua Wings."
        ),
    )


def get_specs() -> list[EggSpec]:
    return [
        _make_linux_egg(
            "ubuntu-20-04", "Ubuntu 20.04 Legacy", ["20.04 LTS (ESM Legacy)"], "ubuntu_20.04",
            "docker/linux/ubuntu-20.04/Dockerfile", ["amd64", "arm64"],
            "https://ubuntu.com", "GPL/Ubuntu-Main", status="Legacy",
            extra_note="Standard support ended May 2025 (ESM only). Migrate to Ubuntu 24.04 or 26.04 LTS for new workloads.",
        ),
        _make_linux_egg(
            "ubuntu-22-04", "Ubuntu 22.04 LTS", ["22.04 LTS (Jammy)"], "ubuntu_22.04",
            "docker/linux/ubuntu-22.04/Dockerfile", ["amd64", "arm64"],
            "https://ubuntu.com", "GPL/Ubuntu-Main",
        ),
        _make_linux_egg(
            "ubuntu-24-04", "Ubuntu 24.04 LTS", ["24.04 LTS (Noble)"], "ubuntu_24.04",
            "docker/linux/ubuntu-24.04/Dockerfile", ["amd64", "arm64"],
            "https://ubuntu.com", "GPL/Ubuntu-Main",
        ),
        _make_linux_egg(
            "ubuntu-26-04", "Ubuntu 26.04 LTS", ["26.04 LTS (Resolute)"], "ubuntu_26.04",
            "docker/linux/ubuntu-26.04/Dockerfile", ["amd64", "arm64"],
            "https://ubuntu.com", "GPL/Ubuntu-Main",
        ),
        _make_linux_egg(
            "debian-12", "Debian 12 (Bookworm)", ["12 (Bookworm)"], "debian_12",
            "docker/linux/debian-12/Dockerfile", ["amd64", "arm64"],
            "https://www.debian.org", "DFSG / GPL",
            official_fallback={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
        ),
        _make_linux_egg(
            "debian-13", "Debian 13 (Trixie)", ["13 (Trixie)"], "debian_13",
            "docker/linux/debian-13/Dockerfile", ["amd64", "arm64"],
            "https://www.debian.org", "DFSG / GPL",
        ),
        _make_linux_egg(
            "alpine", "Alpine Linux", ["3.23"], "alpine_3.23",
            "docker/linux/alpine/Dockerfile", ["amd64", "arm64"],
            "https://alpinelinux.org", "MIT / GPL-2.0",
            official_fallback={"Alpine Official Yolk": "ghcr.io/pterodactyl/yolks:alpine"},
        ),
        _make_linux_egg(
            "fedora", "Fedora Linux", ["44"], "fedora_44",
            "docker/linux/fedora/Dockerfile", ["amd64", "arm64"],
            "https://fedoraproject.org", "Fedora License",
        ),
        _make_linux_egg(
            "rocky-linux", "Rocky Linux", ["9"], "rocky_9",
            "docker/linux/rocky-linux/Dockerfile", ["amd64", "arm64"],
            "https://rockylinux.org", "BSD-3-Clause / GPL",
        ),
        _make_linux_egg(
            "almalinux", "AlmaLinux", ["9"], "almalinux_9",
            "docker/linux/almalinux/Dockerfile", ["amd64", "arm64"],
            "https://almalinux.org", "GPL / MIT",
        ),
        _make_linux_egg(
            "arch-linux", "Arch Linux", ["Rolling (Pinned Snapshot)"], "arch_base",
            "docker/linux/arch-linux/Dockerfile", ["amd64"],
            "https://archlinux.org", "GPL / Mixed",
            extra_note="Official Docker Hub archlinux:base image supports AMD64 only (ARM64 is not officially published by Arch Linux).",
        ),
        _make_linux_egg(
            "kali-linux", "Kali Linux Minimal", ["2026.3 Minimal"], "kali_minimal",
            "docker/linux/kali-linux/Dockerfile", ["amd64", "arm64"],
            "https://www.kali.org", "GPL / Mixed",
            extra_note="Minimal authorized security-testing container only. Raw packet capture / kernel modules are blocked by standard Wings isolation.",
        ),
        _make_linux_egg(
            "opensuse", "openSUSE Leap", ["15.6"], "opensuse_15.6",
            "docker/linux/opensuse/Dockerfile", ["amd64", "arm64"],
            "https://www.opensuse.org", "GPL / MIT",
        ),
        _make_linux_egg(
            "amazon-linux", "Amazon Linux", ["2023"], "amazonlinux_2023",
            "docker/linux/amazon-linux/Dockerfile", ["amd64", "arm64"],
            "https://aws.amazon.com/linux/amazon-linux-2023/", "MIT-0 / GPL",
        ),
        _make_linux_egg(
            "oracle-linux", "Oracle Linux", ["9"], "oraclelinux_9",
            "docker/linux/oracle-linux/Dockerfile", ["amd64", "arm64"],
            "https://www.oracle.com/linux/", "GPL-2.0 / Mixed",
        ),
    ]
