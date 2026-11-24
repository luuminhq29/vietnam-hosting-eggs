#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — n8n Workflow Automation (n8n)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — n8n Workflow Automation. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — n8n Workflow Automation."
    VNH_REINSTALL=0
fi

mkdir -p /mnt/server/data
cd /mnt/server
if [[ ! -f package.json ]]; then npm init -y >/dev/null; fi
npm install n8n --omit=dev

{
    printf 'egg_id=%s\n' "n8n"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — n8n Workflow Automation."
