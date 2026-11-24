#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Uptime Kuma (uptime-kuma)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Uptime Kuma. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Uptime Kuma."
    VNH_REINSTALL=0
fi

mkdir -p /mnt/server/data
if [[ ! -d /mnt/server/.git ]]; then
    git clone --depth 1 https://github.com/louislam/uptime-kuma.git /tmp/kuma
    cp -an /tmp/kuma/. /mnt/server/
    rm -rf /tmp/kuma
else
    git -C /mnt/server pull --ff-only || true
fi
cd /mnt/server
npm run setup || npm ci --omit=dev

{
    printf 'egg_id=%s\n' "uptime-kuma"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Uptime Kuma."
