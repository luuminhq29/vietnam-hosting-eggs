#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Nginx Web Server (nginx)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Nginx Web Server. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Nginx Web Server."
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

mkdir -p /mnt/server/public /mnt/server/nginx /mnt/server/tmp /mnt/server/logs
if [[ ! -f /mnt/server/nginx/nginx.conf.tpl ]]; then
cat > /mnt/server/nginx/nginx.conf.tpl <<'EOF'
worker_processes auto;
pid /home/container/tmp/nginx.pid;
error_log /home/container/logs/error.log warn;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /home/container/logs/access.log;
    client_body_temp_path /home/container/tmp/body;
    proxy_temp_path /home/container/tmp/proxy;
    fastcgi_temp_path /home/container/tmp/fastcgi;
    uwsgi_temp_path /home/container/tmp/uwsgi;
    scgi_temp_path /home/container/tmp/scgi;
    sendfile on;
    gzip on;
    server {
        listen 0.0.0.0:__PORT__;
        root __DOCROOT__;
        index index.html index.htm;
        location = /healthz { return 200 "ok\n"; add_header Content-Type text/plain; }
        location / { try_files $uri $uri/ __FALLBACK__; }
    }
}
EOF
fi
if [[ ! -f /mnt/server/public/index.html ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    printf '<!doctype html><html><head><meta charset="utf-8"><title>Vietnam Hosting</title></head><body><h1>Vietnam Hosting Web Ready</h1></body></html>\n' > /mnt/server/public/index.html
fi

{
    printf 'egg_id=%s\n' "nginx"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Nginx Web Server."
