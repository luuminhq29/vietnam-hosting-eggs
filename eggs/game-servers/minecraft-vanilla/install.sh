#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Minecraft Vanilla (minecraft-vanilla)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Minecraft Vanilla. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Minecraft Vanilla."
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
MANIFEST_JSON="$(curl -fsSL --connect-timeout 15 --max-time 30 https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)"
REQ_VER="${VANILLA_VERSION:-latest}"
if [[ "${REQ_VER}" == "latest" ]]; then
    REQ_VER="$(printf '%s' "${MANIFEST_JSON}" | jq -r '.latest.release')"
fi
VER_URL="$(printf '%s' "${MANIFEST_JSON}" | jq -r --arg v "${REQ_VER}" '.versions[] | select(.id == $v) | .url' | head -n1)"
if [[ -z "${VER_URL}" || "${VER_URL}" == "null" ]]; then
    echo "[VNH][INSTALL][ERROR] Minecraft Vanilla version '${REQ_VER}' not found in Mojang manifest." >&2
    exit 1
fi
VER_JSON="$(curl -fsSL --connect-timeout 15 --max-time 30 "${VER_URL}")"
JAR_URL="$(printf '%s' "${VER_JSON}" | jq -r '.downloads.server.url')"
JAR_SHA1="$(printf '%s' "${VER_JSON}" | jq -r '.downloads.server.sha1')"
vnh_download "${JAR_URL}" "/mnt/server/${SERVER_JARFILE}"
if command -v sha1sum >/dev/null 2>&1 && [[ -n "${JAR_SHA1}" && "${JAR_SHA1}" != "null" ]]; then
    GOT_SHA1="$(sha1sum "/mnt/server/${SERVER_JARFILE}" | awk '{print $1}')"
    if [[ "${GOT_SHA1,,}" != "${JAR_SHA1,,}" ]]; then
        echo "[VNH][INSTALL][ERROR] Mojang server JAR SHA1 mismatch!" >&2
        exit 1
    fi
fi

{
    printf 'egg_id=%s\n' "minecraft-vanilla"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Minecraft Vanilla."
