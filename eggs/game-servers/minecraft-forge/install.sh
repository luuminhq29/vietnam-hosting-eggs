#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Minecraft Forge (minecraft-forge)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Minecraft Forge. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Minecraft Forge."
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
apt-get update && apt-get install -y --no-install-recommends curl jq ca-certificates && rm -rf /var/lib/apt/lists/*
FORGE_FULL="${FORGE_VERSION}"
if [[ -z "${FORGE_FULL}" ]]; then
    PROMO="$(curl -fsSL https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json)"
    FVER="$(printf '%s' "${PROMO}" | jq -r --arg k "${MC_VERSION}-recommended" '.promos[$k] // empty')"
    [[ -z "${FVER}" ]] && FVER="$(printf '%s' "${PROMO}" | jq -r --arg k "${MC_VERSION}-latest" '.promos[$k] // empty')"
    FORGE_FULL="${MC_VERSION}-${FVER}"
fi
vnh_download "https://maven.minecraftforge.net/net/minecraftforge/forge/${FORGE_FULL}/forge-${FORGE_FULL}-installer.jar" "/mnt/server/forge-installer.jar"
java -jar /mnt/server/forge-installer.jar --installServer /mnt/server
rm -f /mnt/server/forge-installer.jar /mnt/server/forge-installer.jar.log
UNIX_ARGS="$(find /mnt/server/libraries/net/minecraftforge/forge -name unix_args.txt 2>/dev/null | head -n1 || true)"
if [[ -n "${UNIX_ARGS}" ]]; then
    ln -sf "${UNIX_ARGS}" /mnt/server/unix_args.txt
fi
mkdir -p /mnt/server/mods

{
    printf 'egg_id=%s\n' "minecraft-forge"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Minecraft Forge."
