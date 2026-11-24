#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — PHP-FPM Dedicated Pool (php-fpm)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — PHP-FPM Dedicated Pool. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — PHP-FPM Dedicated Pool."
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
mkdir -p /mnt/server/public /mnt/server/nginx /mnt/server/php /mnt/server/tmp /mnt/server/logs
cat > /mnt/server/nginx/nginx.conf.tpl <<'EOF'
worker_processes auto;
pid /home/container/tmp/nginx.pid;
error_log /home/container/logs/nginx-error.log warn;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /home/container/logs/nginx-access.log;
    client_body_temp_path /home/container/tmp/body;
    proxy_temp_path /home/container/tmp/proxy;
    fastcgi_temp_path /home/container/tmp/fastcgi;
    uwsgi_temp_path /home/container/tmp/uwsgi;
    scgi_temp_path /home/container/tmp/scgi;
    server {
        listen 0.0.0.0:__PORT__;
        root __DOCROOT__;
        index index.php index.html;
        location = /healthz { return 200 "ok\n"; }
        location / { try_files $uri $uri/ /index.php?$query_string; }
        location ~ \.php$ {
            include /etc/nginx/fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            fastcgi_pass unix:/home/container/tmp/php-fpm.sock;
        }
    }
}
EOF
cat > /mnt/server/php/php-fpm.conf <<'EOF'
[global]
pid = /home/container/tmp/php-fpm.pid
error_log = /home/container/logs/php-fpm.log
[www]
listen = /home/container/tmp/php-fpm.sock
pm = dynamic
pm.max_children = 12
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 4
clear_env = no
EOF
if [[ ! -f /mnt/server/public/index.php ]]; then
    printf '<?php echo "Vietnam Hosting PHP-FPM Ready (" . PHP_VERSION . ")\\n";\n' > /mnt/server/public/index.php
fi

{
    printf 'egg_id=%s\n' "php-fpm"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — PHP-FPM Dedicated Pool."
