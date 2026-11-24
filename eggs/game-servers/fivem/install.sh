#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — FiveM (Cfx.re FXServer) (fivem)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — FiveM (Cfx.re FXServer). Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — FiveM (Cfx.re FXServer)."
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
    echo "[VNH][INSTALL][ERROR] Cfx.re FXServer Linux artifacts support x86_64 (amd64) only." >&2
    exit 1
fi
ART_URL="${FIVEM_ARTIFACT_URL:-}"
if [[ -z "${ART_URL}" ]]; then
    CHANGELOG="$(curl -fsSL https://changelogs-live.fivem.net/api/changelog/versions/linux/server)"
    ART_URL="$(printf '%s' "${CHANGELOG}" | jq -r '.recommended_download')"
fi
vnh_download "${ART_URL}" "/tmp/fx.tar.xz"
tar -xf /tmp/fx.tar.xz -C /mnt/server
rm -f /tmp/fx.tar.xz
if [[ ! -f /mnt/server/server.cfg ]]; then
    cat > /mnt/server/server.cfg <<'EOF'
endpoint_add_tcp "0.0.0.0:{{SERVER_PORT}}"
endpoint_add_udp "0.0.0.0:{{SERVER_PORT}}"
sv_hostname "Vietnam Hosting FiveM Server"
sv_maxclients 32
EOF
fi

{
    printf 'egg_id=%s\n' "fivem"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — FiveM (Cfx.re FXServer)."
