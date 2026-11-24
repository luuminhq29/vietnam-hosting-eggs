#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Minecraft NeoForge (minecraft-neoforge)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Minecraft NeoForge. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Minecraft NeoForge."
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
NF_VER="${NEOFORGE_VERSION:-latest}"
if [[ "${NF_VER}" == "latest" ]]; then
    NF_VER="$(curl -fsSL https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge | jq -r '.versions[-1]')"
fi
vnh_download "https://maven.neoforged.net/releases/net/neoforged/neoforge/${NF_VER}/neoforge-${NF_VER}-installer.jar" "/mnt/server/neoforge-installer.jar"
java -jar /mnt/server/neoforge-installer.jar --installServer /mnt/server
rm -f /mnt/server/neoforge-installer.jar
UNIX_ARGS="$(find /mnt/server/libraries/net/neoforged/neoforge -name unix_args.txt 2>/dev/null | head -n1 || true)"
if [[ -n "${UNIX_ARGS}" ]]; then
    ln -sf "${UNIX_ARGS}" /mnt/server/unix_args.txt
fi
mkdir -p /mnt/server/mods

{
    printf 'egg_id=%s\n' "minecraft-neoforge"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Minecraft NeoForge."
