#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Minecraft Velocity Proxy (minecraft-velocity)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Minecraft Velocity Proxy. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Minecraft Velocity Proxy."
    VNH_REINSTALL=0
fi

vnh_download() {
    local url="$1"
    local dest="$2"
    local sha="${3:-}"
    if [[ ! "$url" =~ ^https:// ]]; then
        echo "[VNH][INSTALL][ERROR] Only https:// URLs are permitted: $url" >&2
        return 1
    fi
    local tmp="${dest}.vnh.tmp"
    local attempt=1
    while (( attempt <= 3 )); do
        echo "[VNH][INSTALL] Downloading (${attempt}/3): ${url}"
        if curl -fsSL --connect-timeout 15 --max-time 180 \
            -A "VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)" \
            -o "$tmp" "$url"; then
            break
        fi
        rm -f "$tmp"
        if (( attempt == 3 )); then
            echo "[VNH][INSTALL][ERROR] Failed to download ${url}" >&2
            return 1
        fi
        sleep $(( attempt * 2 ))
        attempt=$(( attempt + 1 ))
    done
    if [[ -n "$sha" ]]; then
        local got
        got="$(sha256sum "$tmp" | awk '{print $1}')"
        if [[ "${got,,}" != "${sha,,}" ]]; then
            rm -f "$tmp"
            echo "[VNH][INSTALL][ERROR] SHA256 mismatch for ${dest}: expected ${sha}, got ${got}" >&2
            return 1
        fi
        echo "[VNH][INSTALL] Verified SHA256 for ${dest}."
    fi
    mv -f "$tmp" "$dest"
}
UA="VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)"
V_VER="${VELOCITY_VERSION:-latest}"
if [[ "${V_VER}" == "latest" ]]; then
    V_VER="$(curl -fsSL -A "${UA}" https://api.papermc.io/v2/projects/velocity | jq -r '.versions[-1]')"
fi
B_NUM="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}" | jq -r '.builds[-1]')"
META="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}/builds/${B_NUM}")"
JAR_NAME="$(printf '%s' "${META}" | jq -r '.downloads.application.name')"
JAR_SHA256="$(printf '%s' "${META}" | jq -r '.downloads.application.sha256')"
vnh_download "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}/builds/${B_NUM}/downloads/${JAR_NAME}" "/mnt/server/${SERVER_JARFILE}" "${JAR_SHA256}"

{
    printf 'egg_id=%s\n' "minecraft-velocity"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Minecraft Velocity Proxy."
