#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Webhook Receiver (webhook-receiver)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Webhook Receiver. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Webhook Receiver."
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
if [[ ! -f /mnt/server/receiver.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/receiver.py <<'EOF'
import hashlib, hmac, os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("SERVER_PORT", "8080"))
SECRET = os.environ.get("WEBHOOK_SECRET", "").encode()

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")
            return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(min(length, 1048576))
        if SECRET:
            sig = self.headers.get("X-Hub-Signature-256", "")
            expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                self.send_response(401); self.end_headers(); self.wfile.write(b"invalid signature\n")
                return
        self.send_response(202); self.end_headers(); self.wfile.write(b"accepted\n")

if __name__ == "__main__":
    print(f"VIETNAM HOSTING Webhook Receiver Ready on 0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), WebhookHandler).serve_forever()
EOF
fi

{
    printf 'egg_id=%s\n' "webhook-receiver"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Webhook Receiver."
