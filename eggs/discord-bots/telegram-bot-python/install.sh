#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Telegram Bot (Python) (telegram-bot-python)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Telegram Bot (Python). Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Telegram Bot (Python)."
    VNH_REINSTALL=0
fi

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
if [[ ! -f /mnt/server/requirements.txt ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    printf 'python-telegram-bot>=21.0\npython-dotenv\n' > /mnt/server/requirements.txt
fi
if [[ ! -f /mnt/server/bot.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/bot.py <<'EOF'
import os, sys
token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not token:
    print("VIETNAM HOSTING Bot Ready — configure TELEGRAM_BOT_TOKEN in Startup variables (never commit tokens).", flush=True)
    sys.exit(0)
print("VIETNAM HOSTING Telegram Bot (Python) bootstrap ready. Replace bot.py with your bot code.", flush=True)
EOF
fi

{
    printf 'egg_id=%s\n' "telegram-bot-python"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Telegram Bot (Python)."
