"""Phase 4B: All 22 Web Hosting Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import GIT_DEPLOY_VARS, GIT_INSTALL_SNIPPET, SAFE_DOWNLOAD_HELPER

WEB_SECURITY_VI = (
    "- **Bind chuẩn container:** Ứng dụng luôn lắng nghe trên `0.0.0.0:{{SERVER_PORT}}` (không hardcode IP Node).\n"
    "- **Reverse Proxy & Custom Domain:** Tên miền tùy chỉnh, TLS/HTTPS và Cloudflare Tunnel được quản lý ở tầng **Reverse Proxy / Ingress của nền tảng** do quản trị viên kiểm soát — container không bao giờ chỉnh sửa firewall hoặc Docker Network của host.\n"
    "- **Health Check:** Cung cấp đường dẫn kiểm tra sức khỏe HTTP để reverse proxy giám sát trạng thái."
)

ROOTLESS_NGINX_INSTALL = r'''
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
'''


def _node_web_egg(
    egg_id: str,
    title: str,
    desc: str,
    default_build: str,
    default_start: str,
    upstream_url: str,
    upstream_license: str,
    static_dist: str | None = None,
) -> EggSpec:
    if static_dist:
        startup = (
            'export NODE_ENV=production PORT={{SERVER_PORT}} HOST=0.0.0.0; '
            'if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then '
            '  if [[ -f pnpm-lock.yaml ]]; then pnpm install --frozen-lockfile || pnpm install; '
            '  elif [[ -f yarn.lock ]]; then yarn install --frozen-lockfile || yarn install; '
            '  elif [[ -f package-lock.json ]]; then npm ci || npm install; else npm install; fi; '
            'fi; '
            'if [[ -n "${BUILD_SCRIPT}" ]] && [[ -f package.json ]]; then npm run "${BUILD_SCRIPT}"; fi; '
            'exec npx --yes serve -s "${DIST_DIR}" -l "tcp://0.0.0.0:{{SERVER_PORT}}"'
        )
        extra_vars = [
            VariableSpec("Build Script", "Package.json production build script.", "BUILD_SCRIPT", default_build, rules="nullable|string|max:64"),
            VariableSpec("Static Output Directory", "Built static directory (e.g. dist or build).", "DIST_DIR", static_dist, rules="required|string|max:128"),
        ]
    else:
        startup = (
            'export NODE_ENV=production PORT={{SERVER_PORT}} HOST=0.0.0.0 HOSTNAME=0.0.0.0 NITRO_HOST=0.0.0.0 NITRO_PORT={{SERVER_PORT}}; '
            'if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then '
            '  if [[ -f pnpm-lock.yaml ]]; then pnpm install --frozen-lockfile || pnpm install; '
            '  elif [[ -f yarn.lock ]]; then yarn install --frozen-lockfile || yarn install; '
            '  elif [[ -f package-lock.json ]]; then npm ci || npm install; else npm install; fi; '
            'fi; '
            'if [[ -n "${BUILD_SCRIPT}" ]] && [[ -f package.json ]]; then npm run "${BUILD_SCRIPT}"; fi; '
            'exec npm run "${START_SCRIPT}"'
        )
        extra_vars = [
            VariableSpec("Build Script", "Optional production build script in package.json.", "BUILD_SCRIPT", default_build, rules="nullable|string|max:64"),
            VariableSpec("Start Script", "Production start script in package.json (never dev/nodemon).", "START_SCRIPT", default_start, rules="required|string|max:64"),
        ]

    return EggSpec(
        id=egg_id,
        name=f"Vietnam Hosting — {title}",
        category="web-hosting",
        description=desc,
        icon=egg_id,
        supported_versions=["Node.js 22 LTS", "Node.js 24 LTS", "Node.js 26 LTS"],
        supported_architectures=["amd64", "arm64"],
        minimum_ram_mb=512,
        recommended_ram_mb=1024,
        minimum_disk_mb=1024,
        image_source="hybrid_official_and_ghcr",
        dockerfile_path="docker/languages/nodejs/24/Dockerfile",
        docker_images={
            "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            "Node.js 22 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_22",
            "Node.js 26 LTS (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:nodejs_26",
        },
        custom_docker_images={"Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24", "Node.js 26 LTS": f"{GHCR_NAMESPACE}:nodejs_26"},
        startup=startup,
        stop="^C",
        startup_done="Listening|Ready in|Accepting connections|http://0.0.0.0|VIETNAM HOSTING",
        install_body=GIT_INSTALL_SNIPPET + f'\necho "[VNH][INSTALL] {title} workspace initialized in /mnt/server."\n',
        variables=[
            *extra_vars,
            VariableSpec("Install Dependencies", "Auto install dependencies from lockfile.", "INSTALL_DEPS", "1", rules="required|boolean"),
            *GIT_DEPLOY_VARS,
        ],
        upstream_license=upstream_license,
        upstream_url=upstream_url,
        security_notes_vi=WEB_SECURITY_VI,
        healthcheck_mode="http",
        healthcheck_target="http://127.0.0.1:{{SERVER_PORT}}/",
    )


def get_specs() -> list[EggSpec]:
    return [
        # 1. Static HTML/CSS/JS
        EggSpec(
            id="static-web",
            name="Vietnam Hosting — Static HTML/CSS/JS Hosting",
            category="web-hosting",
            description="High-speed rootless Nginx static website hosting with SPA fallback option, gzip, /healthz endpoint, and Git deploy.",
            icon="html5",
            supported_versions=["Nginx 1.28"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/nginx/Dockerfile",
            docker_images={"Nginx 1.28 Rootless (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:nginx_1.28"},
            custom_docker_images={"Nginx 1.28": f"{GHCR_NAMESPACE}:nginx_1.28"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'FB="=404"; [[ "${SPA_MODE}" == "1" ]] && FB="/index.html"; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/${WEBROOT}|g; s|__FALLBACK__|${FB}|g" '
                '/home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'echo "VIETNAM HOSTING Static Web Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Static Web Ready",
            install_body=GIT_INSTALL_SNIPPET + "\n" + ROOTLESS_NGINX_INSTALL,
            variables=[
                VariableSpec("Document Root", "Folder served by Nginx relative to /home/container.", "WEBROOT", "public", rules="required|string|max:128"),
                VariableSpec("SPA Fallback Mode", "Set to 1 to rewrite unmatched routes to /index.html.", "SPA_MODE", "0", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-2-Clause",
            upstream_url="https://nginx.org",
            security_notes_vi=WEB_SECURITY_VI,
            healthcheck_mode="http",
            healthcheck_target="http://127.0.0.1:{{SERVER_PORT}}/healthz",
        ),
        # 2. Nginx
        EggSpec(
            id="nginx",
            name="Vietnam Hosting — Nginx Web Server",
            category="web-hosting",
            description="Customizable rootless Nginx 1.28 HTTP server and application reverse proxy bound to 0.0.0.0:{{SERVER_PORT}}.",
            icon="nginx",
            supported_versions=["1.28"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/nginx/Dockerfile",
            docker_images={"Nginx 1.28 Rootless (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:nginx_1.28"},
            custom_docker_images={"Nginx 1.28": f"{GHCR_NAMESPACE}:nginx_1.28"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/${WEBROOT}|g; s|__FALLBACK__|=404|g" '
                '/home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'nginx -t -c /home/container/tmp/nginx.conf; '
                'echo "VIETNAM HOSTING Nginx Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Nginx Ready",
            install_body=GIT_INSTALL_SNIPPET + "\n" + ROOTLESS_NGINX_INSTALL,
            variables=[
                VariableSpec("Document Root", "Web root relative to /home/container.", "WEBROOT", "public", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-2-Clause",
            upstream_url="https://nginx.org",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 3. Apache HTTP Server
        EggSpec(
            id="apache",
            name="Vietnam Hosting — Apache HTTP Server",
            category="web-hosting",
            description="Rootless Apache HTTP Server 2.4 with .htaccess support, mod_rewrite, and custom httpd.conf in /home/container.",
            icon="apache",
            supported_versions=["2.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/apache/Dockerfile",
            docker_images={"Apache HTTPD 2.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:apache_2.4"},
            custom_docker_images={"Apache HTTPD 2.4": f"{GHCR_NAMESPACE}:apache_2.4"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/${WEBROOT}|g" '
                '/home/container/apache/httpd.conf.tpl > /home/container/tmp/httpd.conf; '
                'echo "VIETNAM HOSTING Apache Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec httpd -f /home/container/tmp/httpd.conf -DFOREGROUND'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Apache Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/public /mnt/server/apache /mnt/server/tmp /mnt/server/logs
if [[ ! -f /mnt/server/apache/httpd.conf.tpl ]]; then
cat > /mnt/server/apache/httpd.conf.tpl <<'EOF'
ServerRoot "/usr/local/apache2"
Listen 0.0.0.0:__PORT__
LoadModule mpm_event_module modules/mod_mpm_event.so
LoadModule authz_core_module modules/mod_authz_core.so
LoadModule dir_module modules/mod_dir.so
LoadModule mime_module modules/mod_mime.so
LoadModule log_config_module modules/mod_log_config.so
LoadModule unixd_module modules/mod_unixd.so
LoadModule rewrite_module modules/mod_rewrite.so
ServerName localhost
PidFile /home/container/tmp/httpd.pid
ErrorLog /home/container/logs/error.log
CustomLog /home/container/logs/access.log common
DocumentRoot "__DOCROOT__"
<Directory "__DOCROOT__">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
DirectoryIndex index.html
EOF
fi
if [[ ! -f /mnt/server/public/index.html ]]; then
    printf '<h1>Vietnam Hosting Apache 2.4 Ready</h1>\n' > /mnt/server/public/index.html
fi
''',
            variables=[
                VariableSpec("Document Root", "Apache DocumentRoot relative to /home/container.", "WEBROOT", "public", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://httpd.apache.org",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 4. Caddy
        EggSpec(
            id="caddy",
            name="Vietnam Hosting — Caddy Web Server",
            category="web-hosting",
            description="Modern Caddy 2.9 rootless web server & reverse proxy configured via Caddyfile bound to :{{SERVER_PORT}}.",
            icon="caddy",
            supported_versions=["2.9"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/caddy/Dockerfile",
            docker_images={"Caddy 2.9 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:caddy_2.9"},
            custom_docker_images={"Caddy 2.9": f"{GHCR_NAMESPACE}:caddy_2.9"},
            startup='export PORT={{SERVER_PORT}}; echo "VIETNAM HOSTING Caddy Ready on 0.0.0.0:{{SERVER_PORT}}"; exec caddy run --config /home/container/Caddyfile --adapter caddyfile',
            stop="^C",
            startup_done="serving initial configuration|VIETNAM HOSTING Caddy Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/public
if [[ ! -f /mnt/server/Caddyfile ]]; then
cat > /mnt/server/Caddyfile <<'EOF'
{
    admin off
    auto_https off
}
:{$PORT:8080} {
    root * /home/container/public
    encode gzip
    respond /healthz 200
    file_server
}
EOF
fi
if [[ ! -f /mnt/server/public/index.html ]]; then
    printf '<h1>Vietnam Hosting Caddy 2.9 Ready</h1>\n' > /mnt/server/public/index.html
fi
''',
            variables=[*GIT_DEPLOY_VARS],
            upstream_license="Apache-2.0",
            upstream_url="https://caddyserver.com",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 5. PHP-FPM
        EggSpec(
            id="php-fpm",
            name="Vietnam Hosting — PHP-FPM Dedicated Pool",
            category="web-hosting",
            description="Dedicated rootless PHP-FPM + Nginx web hosting stack supporting PHP 8.2–8.5 and Composer.",
            icon="php",
            supported_versions=["8.2", "8.3", "8.4", "8.5"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/php/8.4/Dockerfile",
            docker_images={
                "PHP-FPM 8.5 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.5",
                "PHP-FPM 8.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.4",
                "PHP-FPM 8.3 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.3",
                "PHP-FPM 8.2 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.2",
            },
            custom_docker_images={"PHP-FPM 8.4": f"{GHCR_NAMESPACE}:php_8.4"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/${WEBROOT}|g" /home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'php-fpm --fpm-config /home/container/php/php-fpm.conf --daemonize; '
                'echo "VIETNAM HOSTING PHP-FPM Pool Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING PHP-FPM Pool Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
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
''',
            variables=[
                VariableSpec("Document Root", "PHP document root.", "WEBROOT", "public", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="PHP-3.01",
            upstream_url="https://www.php.net",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 6. WordPress
        EggSpec(
            id="wordpress",
            name="Vietnam Hosting — WordPress Hosting",
            category="web-hosting",
            description="Production WordPress hosting on rootless Nginx + PHP-FPM 8.3/8.4 with non-destructive reinstall preserving wp-content and wp-config.php.",
            icon="wordpress",
            supported_versions=["Latest Official Tarball (PHP 8.3/8.4)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/php/8.4/Dockerfile",
            docker_images={
                "PHP 8.4 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.4",
                "PHP 8.3 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.3",
            },
            custom_docker_images={"PHP 8.4": f"{GHCR_NAMESPACE}:php_8.4"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/wordpress|g" /home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'php-fpm --fpm-config /home/container/php/php-fpm.conf --daemonize; '
                'echo "VIETNAM HOSTING WordPress Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING WordPress Ready",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
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
''',
            variables=[],
            upstream_license="GPL-2.0-or-later",
            upstream_url="https://wordpress.org",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 7. Laravel
        EggSpec(
            id="laravel",
            name="Vietnam Hosting — Laravel Hosting",
            category="web-hosting",
            description="Production Laravel hosting on PHP 8.3–8.5 + Nginx + PHP-FPM with Composer, artisan cache optimization, and Git deploy.",
            icon="laravel",
            supported_versions=["Laravel 11/12 (PHP 8.3–8.5)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/php/8.4/Dockerfile",
            docker_images={
                "PHP 8.4 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.4",
                "PHP 8.5 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.5",
                "PHP 8.3 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.3",
            },
            custom_docker_images={"PHP 8.4": f"{GHCR_NAMESPACE}:php_8.4"},
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'if [[ -f composer.json ]] && [[ "${COMPOSER_INSTALL}" == "1" ]]; then composer install --no-dev --optimize-autoloader --no-interaction; fi; '
                'if [[ -f artisan ]] && [[ "${RUN_MIGRATIONS}" == "1" ]]; then php artisan migrate --force; fi; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/public|g" /home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'php-fpm --fpm-config /home/container/php/php-fpm.conf --daemonize; '
                'echo "VIETNAM HOSTING Laravel Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Laravel Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
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
        index index.php;
        location / { try_files $uri $uri/ /index.php?$query_string; }
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
''',
            variables=[
                VariableSpec("Auto Composer Install", "Install Composer production packages.", "COMPOSER_INSTALL", "1", rules="required|boolean"),
                VariableSpec("Run Artisan Migrate on Boot", "Set to 1 to run `php artisan migrate --force`.", "RUN_MIGRATIONS", "0", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://laravel.com",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 8. Django
        EggSpec(
            id="django",
            name="Vietnam Hosting — Django Hosting (Gunicorn)",
            category="web-hosting",
            description="Production Django web hosting running Gunicorn WSGI bound to 0.0.0.0:{{SERVER_PORT}} with collectstatic and migrate options.",
            icon="django",
            supported_versions=["Python 3.11–3.14"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Python 3.12 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.12",
            },
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup=(
                'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; '
                'if [[ "${INSTALL_DEPS}" == "1" ]] && [[ -f requirements.txt ]]; then pip install --no-cache-dir -r requirements.txt gunicorn; fi; '
                'if [[ "${RUN_COLLECTSTATIC}" == "1" ]] && [[ -f manage.py ]]; then python manage.py collectstatic --noinput; fi; '
                'if [[ "${RUN_MIGRATIONS}" == "1" ]] && [[ -f manage.py ]]; then python manage.py migrate --noinput; fi; '
                'exec gunicorn --bind "0.0.0.0:{{SERVER_PORT}}" --workers "${WORKERS}" "${WSGI_APP}"'
            ),
            stop="^C",
            startup_done="Listening at:|Booting worker",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Django production workspace ready. Set WSGI_APP (e.g. myproject.wsgi:application)."\n',
            variables=[
                VariableSpec("WSGI Application", "Django WSGI callable (e.g. config.wsgi:application).", "WSGI_APP", "config.wsgi:application", rules="required|string|max:128"),
                VariableSpec("Gunicorn Workers", "Number of Gunicorn worker processes.", "WORKERS", "2", rules="required|integer|between:1,8"),
                VariableSpec("Collect Static", "Run `manage.py collectstatic --noinput` on boot.", "RUN_COLLECTSTATIC", "1", rules="required|boolean"),
                VariableSpec("Run Migrations", "Run `manage.py migrate --noinput` on boot.", "RUN_MIGRATIONS", "0", rules="required|boolean"),
                VariableSpec("Install Dependencies", "Install requirements.txt + gunicorn.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://www.djangoproject.com",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 9. Flask
        EggSpec(
            id="flask",
            name="Vietnam Hosting — Flask Hosting (Gunicorn)",
            category="web-hosting",
            description="Production Flask hosting using Gunicorn WSGI (never Flask dev server) bound to 0.0.0.0:{{SERVER_PORT}}.",
            icon="flask",
            supported_versions=["Python 3.11–3.14"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={"Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13"},
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup=(
                'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; '
                'if [[ "${INSTALL_DEPS}" == "1" ]] && [[ -f requirements.txt ]]; then pip install --no-cache-dir -r requirements.txt gunicorn; fi; '
                'exec gunicorn --bind "0.0.0.0:{{SERVER_PORT}}" --workers "${WORKERS}" "${WSGI_APP}"'
            ),
            stop="^C",
            startup_done="Listening at:|Booting worker",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/app.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    printf 'flask>=3.0\ngunicorn>=23.0\n' > /mnt/server/requirements.txt
    cat > /mnt/server/app.py <<'EOF'
from flask import Flask
app = Flask(__name__)
@app.get("/")
def index(): return "Vietnam Hosting Flask Ready\n"
@app.get("/healthz")
def healthz(): return "ok\n", 200
EOF
fi
''',
            variables=[
                VariableSpec("WSGI Target", "Flask WSGI target (e.g. app:app).", "WSGI_APP", "app:app", rules="required|string|max:128"),
                VariableSpec("Gunicorn Workers", "Number of worker processes.", "WORKERS", "2", rules="required|integer|between:1,8"),
                VariableSpec("Install Dependencies", "Auto install requirements.txt + gunicorn.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://flask.palletsprojects.com",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 10. FastAPI
        EggSpec(
            id="fastapi",
            name="Vietnam Hosting — FastAPI Hosting (Uvicorn)",
            category="web-hosting",
            description="Production FastAPI ASGI hosting with Uvicorn bound to 0.0.0.0:{{SERVER_PORT}}, proxy headers enabled, and .venv isolation.",
            icon="fastapi",
            supported_versions=["Python 3.11–3.14"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={"Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13"},
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup=(
                'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; '
                'if [[ "${INSTALL_DEPS}" == "1" ]] && [[ -f requirements.txt ]]; then pip install --no-cache-dir -r requirements.txt uvicorn; fi; '
                'exec uvicorn "${ASGI_APP}" --host 0.0.0.0 --port {{SERVER_PORT}} --workers "${WORKERS}" --proxy-headers'
            ),
            stop="^C",
            startup_done="Application startup complete|Uvicorn running",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/main.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    printf 'fastapi>=0.115\nuvicorn[standard]>=0.32\n' > /mnt/server/requirements.txt
    cat > /mnt/server/main.py <<'EOF'
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
async def root(): return {"status": "ready", "provider": "Vietnam Hosting"}
@app.get("/healthz")
async def health(): return {"ok": True}
EOF
fi
''',
            variables=[
                VariableSpec("ASGI Application", "FastAPI ASGI target (e.g. main:app).", "ASGI_APP", "main:app", rules="required|string|max:128"),
                VariableSpec("Uvicorn Workers", "Number of ASGI worker processes.", "WORKERS", "2", rules="required|integer|between:1,8"),
                VariableSpec("Install Dependencies", "Install requirements.txt into .venv.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://fastapi.tiangolo.com",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 11-17. Node.js Web Frameworks
        _node_web_egg("express-js", "Express.js Hosting", "Production Express.js API & web hosting on Node.js LTS bound to 0.0.0.0:{{SERVER_PORT}} without nodemon.", "", "start", "https://expressjs.com", "MIT"),
        _node_web_egg("nextjs", "Next.js Production Hosting", "Next.js production SSR/standalone hosting with build step and 0.0.0.0:{{SERVER_PORT}} binding.", "build", "start", "https://nextjs.org", "MIT"),
        _node_web_egg("nuxtjs", "Nuxt.js Production Hosting", "Nuxt 3/4 Nitro SSR production hosting bound to 0.0.0.0:{{SERVER_PORT}}.", "build", "start", "https://nuxt.com", "MIT"),
        _node_web_egg("sveltekit", "SvelteKit Production Hosting", "SvelteKit adapter-node production hosting bound to 0.0.0.0:{{SERVER_PORT}}.", "build", "start", "https://kit.svelte.dev", "MIT"),
        _node_web_egg("astro", "Astro Production Hosting", "Astro SSR/static production hosting bound to 0.0.0.0:{{SERVER_PORT}}.", "build", "start", "https://astro.build", "MIT"),
        _node_web_egg("react-production", "React Production Hosting", "React SPA production build and static serving on 0.0.0.0:{{SERVER_PORT}} (no dev server).", "build", "start", "https://react.dev", "MIT", static_dist="dist"),
        _node_web_egg("vue-production", "Vue Production Hosting", "Vue 3 SPA production build and static serving on 0.0.0.0:{{SERVER_PORT}}.", "build", "start", "https://vuejs.org", "MIT", static_dist="dist"),
        # 18. Spring Boot
        EggSpec(
            id="spring-boot",
            name="Vietnam Hosting — Spring Boot Hosting",
            category="web-hosting",
            description="Production Spring Boot hosting on Eclipse Temurin JDK 17/21/25 with automatic JVM heap sizing and reverse-proxy header support.",
            icon="spring",
            supported_versions=["Java 17", "Java 21 LTS", "Java 25 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images={
                "Java 21 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_21",
                "Java 25 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_25",
                "Java 17 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_17",
            },
            custom_docker_images={"Java 21 LTS": f"{GHCR_NAMESPACE}:java_21"},
            startup=(
                'MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 256 )) && HEAP=256; '
                'exec java -Xms256M -Xmx"${HEAP}M" -XX:+UseG1GC '
                '-Dserver.address=0.0.0.0 -Dserver.port={{SERVER_PORT}} '
                '-Dserver.forward-headers-strategy=framework '
                '-Dspring.profiles.active="${SPRING_PROFILES_ACTIVE}" '
                '-jar "${APP_JAR}"'
            ),
            stop="^C",
            startup_done="Started .* in .* seconds|Tomcat started on port",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Upload your Spring Boot fat JAR (app.jar)."\n',
            variables=[
                VariableSpec("Spring Boot JAR", "Executable Spring Boot JAR path.", "APP_JAR", "app.jar", rules="required|string|max:191"),
                VariableSpec("Spring Profiles Active", "Active Spring Boot profile (e.g. prod).", "SPRING_PROFILES_ACTIVE", "prod", rules="required|string|max:64"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://spring.io/projects/spring-boot",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 19. ASP.NET Core
        EggSpec(
            id="aspnet-core",
            name="Vietnam Hosting — ASP.NET Core Hosting",
            category="web-hosting",
            description="Production ASP.NET Core Kestrel hosting on .NET 10 LTS / 11 STS bound to http://0.0.0.0:{{SERVER_PORT}}.",
            icon="dotnet",
            supported_versions=[".NET 8.0", ".NET 10.0 LTS", ".NET 11.0 STS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dotnet/10/Dockerfile",
            docker_images={
                ".NET 10.0 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_10",
                ".NET 11.0 STS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_11",
            },
            custom_docker_images={".NET 10.0 LTS": f"{GHCR_NAMESPACE}:dotnet_10"},
            startup=(
                'export ASPNETCORE_URLS="http://0.0.0.0:{{SERVER_PORT}}" ASPNETCORE_ENVIRONMENT="${ASPNETCORE_ENVIRONMENT}"; '
                'if [[ -n "${PROJECT_FILE}" ]] && [[ -f "${PROJECT_FILE}" ]]; then dotnet publish "${PROJECT_FILE}" -c Release -o ./out --nologo; fi; '
                'if [[ -f "./out/${APP_DLL}" ]]; then exec dotnet "./out/${APP_DLL}"; else exec dotnet "./${APP_DLL}"; fi'
            ),
            stop="^C",
            startup_done="Now listening on:|Application started",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/out\n',
            variables=[
                VariableSpec("Project File", "Optional .csproj path to publish.", "PROJECT_FILE", "", rules="nullable|string|max:191"),
                VariableSpec("Application DLL", "Compiled ASP.NET Core DLL.", "APP_DLL", "WebApp.dll", rules="required|string|max:191"),
                VariableSpec("Environment", "ASPNETCORE_ENVIRONMENT setting.", "ASPNETCORE_ENVIRONMENT", "Production", rules="required|string|in:Production,Staging,Development"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://dotnet.microsoft.com/apps/aspnet",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 20. Go Web Server
        EggSpec(
            id="go-web",
            name="Vietnam Hosting — Go Web Server",
            category="web-hosting",
            description="High-concurrency Go HTTP/Gin/Fiber/Echo web server compiled cleanly and bound to 0.0.0.0:{{SERVER_PORT}}.",
            icon="go",
            supported_versions=["Go 1.23", "Go 1.25"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/go/1.25/Dockerfile",
            docker_images={
                "Go 1.23 (Official Yolk)": "ghcr.io/pterodactyl/yolks:go_1.23",
                "Go 1.25 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:go_1.25",
            },
            custom_docker_images={"Go 1.25": f"{GHCR_NAMESPACE}:go_1.25"},
            startup='export PORT={{SERVER_PORT}} HOST=0.0.0.0; if [[ -f go.mod ]] && [[ "${AUTO_BUILD}" == "1" ]]; then go build -trimpath -ldflags="-s -w" -o "./${BIN_NAME}" "${BUILD_PKG}"; fi; exec "./${BIN_NAME}"',
            stop="^C",
            startup_done="Listening|Serving|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Go Web Server workspace ready."\n',
            variables=[
                VariableSpec("Binary Name", "Output HTTP server executable.", "BIN_NAME", "web", rules="required|string|max:128"),
                VariableSpec("Go Package", "Package path to build.", "BUILD_PKG", ".", rules="required|string|max:128"),
                VariableSpec("Auto Build", "Build binary on startup.", "AUTO_BUILD", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://go.dev",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 21. Rust Axum
        EggSpec(
            id="rust-axum",
            name="Vietnam Hosting — Rust Axum Web Hosting",
            category="web-hosting",
            description="Rust Axum async web server hosting with bounded CARGO_BUILD_JOBS release build and 0.0.0.0:{{SERVER_PORT}} binding.",
            icon="rust",
            supported_versions=["Rust Stable 1.86"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/rust/stable/Dockerfile",
            docker_images={"Rust Stable 1.86 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_stable"},
            custom_docker_images={"Rust Stable 1.86": f"{GHCR_NAMESPACE}:rust_stable"},
            startup='export PORT={{SERVER_PORT}} HOST=0.0.0.0 CARGO_BUILD_JOBS="${BUILD_JOBS}"; if [[ -f Cargo.toml ]] && [[ "${AUTO_BUILD}" == "1" ]]; then cargo build --release --jobs "${BUILD_JOBS}"; fi; exec "./target/release/${BIN_NAME}"',
            stop="^C",
            startup_done="Listening|Axum|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/target/release\n',
            variables=[
                VariableSpec("Binary Name", "Axum binary name under target/release/.", "BIN_NAME", "server", rules="required|string|max:128"),
                VariableSpec("Auto Build", "Build release binary on startup.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Cargo Build Jobs", "Max parallel rustc threads.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://github.com/tokio-rs/axum",
            security_notes_vi=WEB_SECURITY_VI,
        ),
        # 22. Rust Actix Web
        EggSpec(
            id="rust-actix-web",
            name="Vietnam Hosting — Rust Actix Web Hosting",
            category="web-hosting",
            description="Rust Actix Web high-throughput server hosting with release build throttling and 0.0.0.0:{{SERVER_PORT}} binding.",
            icon="rust",
            supported_versions=["Rust Stable 1.86"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/rust/stable/Dockerfile",
            docker_images={"Rust Stable 1.86 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_stable"},
            custom_docker_images={"Rust Stable 1.86": f"{GHCR_NAMESPACE}:rust_stable"},
            startup='export PORT={{SERVER_PORT}} HOST=0.0.0.0 CARGO_BUILD_JOBS="${BUILD_JOBS}"; if [[ -f Cargo.toml ]] && [[ "${AUTO_BUILD}" == "1" ]]; then cargo build --release --jobs "${BUILD_JOBS}"; fi; exec "./target/release/${BIN_NAME}"',
            stop="^C",
            startup_done="Starting|Listening|Actix|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/target/release\n',
            variables=[
                VariableSpec("Binary Name", "Actix Web binary name under target/release/.", "BIN_NAME", "server", rules="required|string|max:128"),
                VariableSpec("Auto Build", "Build release binary on startup.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Cargo Build Jobs", "Max parallel rustc threads.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT OR Apache-2.0",
            upstream_url="https://actix.rs",
            security_notes_vi=WEB_SECURITY_VI,
        ),
    ]
