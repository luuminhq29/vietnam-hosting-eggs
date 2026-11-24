#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — OpenTTD Dedicated Server (openttd)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — OpenTTD Dedicated Server. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — OpenTTD Dedicated Server."
    VNH_REINSTALL=0
fi

mkdir -p /mnt/server/.openttd /mnt/server/save
if [[ ! -f /mnt/server/openttd.cfg ]]; then printf "[network]\nserver_name = Vietnam Hosting OpenTTD\n" > /mnt/server/openttd.cfg; fi

{
    printf 'egg_id=%s\n' "openttd"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — OpenTTD Dedicated Server."
