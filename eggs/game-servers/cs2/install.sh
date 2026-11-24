#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Counter-Strike 2 (cs2)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Counter-Strike 2. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Counter-Strike 2."
    VNH_REINSTALL=0
fi

# Standard SteamCMD installer (AMD64 native Linux binaries)
ARCH="$(uname -m)"
if [[ "${ARCH}" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] SteamCMD and this game server require x86_64 (amd64); detected ${ARCH}." >&2
    exit 1
fi

STEAM_USER="${STEAM_USER:-anonymous}"
STEAM_PASS="${STEAM_PASS:-}"
STEAM_AUTH="${STEAM_AUTH:-}"

mkdir -p /mnt/server/steamcmd /mnt/server/steamapps /mnt/server/.steam/sdk32 /mnt/server/.steam/sdk64
if [[ ! -x /mnt/server/steamcmd/steamcmd.sh ]]; then
    curl -fsSL --connect-timeout 15 --max-time 120 \
        -o /tmp/steamcmd_linux.tar.gz \
        "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
    tar -xzf /tmp/steamcmd_linux.tar.gz -C /mnt/server/steamcmd
    rm -f /tmp/steamcmd_linux.tar.gz
fi

cd /mnt/server/steamcmd
./steamcmd.sh \
    +force_install_dir /mnt/server \
    +login "${STEAM_USER}" "${STEAM_PASS}" "${STEAM_AUTH}" \
    +app_update "${SRCDS_APPID}" ${SRCDS_BETAID:+-beta "${SRCDS_BETAID}"} ${SRCDS_BETAPASS:+-betapassword "${SRCDS_BETAPASS}"} validate \
    +quit

cp -f /mnt/server/steamcmd/linux32/steamclient.so /mnt/server/.steam/sdk32/steamclient.so 2>/dev/null || true
cp -f /mnt/server/steamcmd/linux64/steamclient.so /mnt/server/.steam/sdk64/steamclient.so 2>/dev/null || true
cd /mnt/server

{
    printf 'egg_id=%s\n' "cs2"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Counter-Strike 2."
