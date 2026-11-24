#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — SearXNG Privacy Metasearch (searxng)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — SearXNG Privacy Metasearch. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — SearXNG Privacy Metasearch."
    VNH_REINSTALL=0
fi

if [[ ! -f /mnt/server/settings.yml ]]; then
    SEC="$(openssl rand -hex 32)"
    cat > /mnt/server/settings.yml <<EOF
use_default_settings: true
server:
  secret_key: "${SEC}"
  limiter: true
  image_proxy: true
EOF
    chmod 600 /mnt/server/settings.yml
fi

{
    printf 'egg_id=%s\n' "searxng"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — SearXNG Privacy Metasearch."
