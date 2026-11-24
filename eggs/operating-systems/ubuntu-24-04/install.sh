#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Ubuntu 24.04 LTS (NAT Linux Container) (ubuntu-24-04)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Ubuntu 24.04 LTS (NAT Linux Container). Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Ubuntu 24.04 LTS (NAT Linux Container)."
    VNH_REINSTALL=0
fi

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

{
    printf 'egg_id=%s\n' "ubuntu-24-04"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Ubuntu 24.04 LTS (NAT Linux Container)."
