#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Minecraft Bedrock Dedicated Server (minecraft-bedrock)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Minecraft Bedrock Dedicated Server. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Minecraft Bedrock Dedicated Server."
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
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] Minecraft Bedrock Dedicated Server officially supports Linux x86_64 (amd64) only." >&2
    exit 1
fi
DL_URL="${BEDROCK_DOWNLOAD_URL:-}"
if [[ -z "${DL_URL}" ]]; then
    DL_URL="$(curl -fsSL -A "Mozilla/5.0" "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links" | jq -r '.result.links[] | select(.downloadType == "serverBedrockLinux") | .downloadUrl' | head -n1)"
fi
if [[ -z "${DL_URL}" || "${DL_URL}" == "null" ]]; then
    echo "[VNH][INSTALL][ERROR] Could not resolve official Mojang Bedrock download URL. Supply BEDROCK_DOWNLOAD_URL explicitly." >&2
    exit 1
fi
vnh_download "${DL_URL}" "/tmp/bedrock-server.zip"
# Preserve existing server.properties, permissions.json, allowlist.json on reinstall
unzip -n -q /tmp/bedrock-server.zip -d /mnt/server
unzip -o -q /tmp/bedrock-server.zip bedrock_server -d /mnt/server
chmod +x /mnt/server/bedrock_server
rm -f /tmp/bedrock-server.zip

{
    printf 'egg_id=%s\n' "minecraft-bedrock"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Minecraft Bedrock Dedicated Server."
