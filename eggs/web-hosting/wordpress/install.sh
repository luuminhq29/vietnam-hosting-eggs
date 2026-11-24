#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — WordPress Hosting (wordpress)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — WordPress Hosting. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — WordPress Hosting."
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
mkdir -p /mnt/server/wordpress /mnt/server/nginx /mnt/server/php /mnt/server/tmp /mnt/server/logs
if [[ ! -f /mnt/server/wordpress/wp-login.php ]]; then
    vnh_download "https://wordpress.org/latest.tar.gz" "/tmp/wordpress.tar.gz"
    tar -xzf /tmp/wordpress.tar.gz -C /mnt/server
    rm -f /tmp/wordpress.tar.gz
else
    echo "[VNH][INSTALL] Existing WordPress files detected; preserving wp-config.php and wp-content."
fi
cat > /mnt/server/nginx/nginx.conf.tpl <<'EOF'
worker_processes auto;
pid /home/container/tmp/nginx.pid;
error_log /home/container/logs/nginx-error.log warn;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /home/container/logs/nginx-access.log;
    client_max_body_size 64M;
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
        location / { try_files $uri $uri/ /index.php?$args; }
        location ~ \.php$ {
            include /etc/nginx/fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            fastcgi_pass unix:/home/container/tmp/php-fpm.sock;
        }
        location ~ /\.(?!well-known).* { deny all; }
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
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 4
clear_env = no
EOF

{
    printf 'egg_id=%s\n' "wordpress"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — WordPress Hosting."
