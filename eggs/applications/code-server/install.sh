#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Code Server (VS Code Web) (code-server)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Code Server (VS Code Web). Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Code Server (VS Code Web)."
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
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && CARCH="arm64" || CARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/coder/code-server/releases/latest | jq -r --arg a "linux-${CARCH}.tar.gz" '.assets[] | select(.name | endswith($a)) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/cs.tar.gz"
mkdir -p /mnt/server/code-server /mnt/server/workspace
tar -xzf /tmp/cs.tar.gz --strip-components=1 -C /mnt/server/code-server
rm -f /tmp/cs.tar.gz

{
    printf 'egg_id=%s\n' "code-server"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Code Server (VS Code Web)."
