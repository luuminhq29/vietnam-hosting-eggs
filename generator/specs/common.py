"""Reusable installation script builders and variable sets for Vietnam Hosting Eggs."""

from __future__ import annotations

from generator.models import VariableSpec

GIT_DEPLOY_VARS = [
    VariableSpec(
        name="Git Repository URL",
        description="Optional HTTPS Git repository URL to clone/pull on install or startup.",
        env_variable="GIT_ADDRESS",
        default_value="",
        rules="nullable|string|max:512",
    ),
    VariableSpec(
        name="Git Branch",
        description="Git branch or tag to checkout (leave blank for repository default).",
        env_variable="BRANCH",
        default_value="",
        rules="nullable|string|max:128",
    ),
    VariableSpec(
        name="Git Username",
        description="Optional username for private HTTPS Git repositories.",
        env_variable="USERNAME",
        default_value="",
        rules="nullable|string|max:128",
    ),
    VariableSpec(
        name="Git Access Token",
        description="Optional Personal Access Token for private repositories (never logged).",
        env_variable="ACCESS_TOKEN",
        default_value="",
        rules="nullable|string|max:256",
    ),
    VariableSpec(
        name="Auto Update Git on Boot",
        description="Set to 1 to run `git pull --ff-only` automatically before starting.",
        env_variable="AUTO_UPDATE",
        default_value="0",
        rules="required|boolean",
    ),
]

GIT_INSTALL_SNIPPET = r'''
# Safe HTTPS Git deployment without logging credentials or wiping existing user data
if [[ -n "${GIT_ADDRESS:-}" ]]; then
    if [[ ! "${GIT_ADDRESS}" =~ ^https:// ]]; then
        echo "[VNH][INSTALL][ERROR] GIT_ADDRESS must use https:// scheme." >&2
        exit 1
    fi
    ASKPASS_FILE=""
    if [[ -n "${ACCESS_TOKEN:-}" ]]; then
        ASKPASS_FILE="$(mktemp /tmp/vnh-git-askpass.XXXXXX)"
        chmod 700 "${ASKPASS_FILE}"
        cat > "${ASKPASS_FILE}" <<'VNH_EOF'
#!/usr/bin/env sh
case "$1" in
    *Username*) printf '%s\n' "${USERNAME:-git}" ;;
    *Password*) printf '%s\n' "${ACCESS_TOKEN:-}" ;;
esac
VNH_EOF
        export GIT_ASKPASS="${ASKPASS_FILE}"
        export GIT_TERMINAL_PROMPT=0
    fi

    if [[ -d /mnt/server/.git ]]; then
        echo "[VNH][INSTALL] Updating existing Git repository..."
        if [[ -n "${BRANCH:-}" ]]; then
            git -C /mnt/server fetch --depth 1 origin "${BRANCH}"
            git -C /mnt/server checkout -B "${BRANCH}" "origin/${BRANCH}"
        else
            git -C /mnt/server pull --ff-only
        fi
    else
        echo "[VNH][INSTALL] Cloning Git repository into /mnt/server..."
        CLONE_TMP="$(mktemp -d /tmp/vnh-clone.XXXXXX)"
        if [[ -n "${BRANCH:-}" ]]; then
            git clone --depth 1 --branch "${BRANCH}" --single-branch "${GIT_ADDRESS}" "${CLONE_TMP}"
        else
            git clone --depth 1 "${GIT_ADDRESS}" "${CLONE_TMP}"
        fi
        cp -an "${CLONE_TMP}/." /mnt/server/
        rm -rf "${CLONE_TMP}"
    fi

    if [[ -n "${ASKPASS_FILE}" ]]; then
        rm -f "${ASKPASS_FILE}"
        unset GIT_ASKPASS
    fi
fi
'''.strip()

SAFE_DOWNLOAD_HELPER = r'''
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
'''.strip()

STEAMCMD_INSTALL_SNIPPET = r'''
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
'''.strip()
