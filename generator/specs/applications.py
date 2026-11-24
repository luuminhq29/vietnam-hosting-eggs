"""Phase 5B: All 19 Application Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import SAFE_DOWNLOAD_HELPER


def get_specs() -> list[EggSpec]:
    return [
        # 1. Lavalink
        EggSpec(
            id="lavalink",
            name="Vietnam Hosting — Lavalink Audio Server",
            category="applications",
            description="Standalone Lavalink v4 audio sending node for Discord music bots with auto-generated strong password and JVM heap cap.",
            icon="lavalink",
            supported_versions=["v4 (Java 17/21)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images={
                "Java 21 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_21",
                "Java 17 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_17",
            },
            custom_docker_images={"Java 21 LTS": f"{GHCR_NAMESPACE}:java_21"},
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 256 )) && HEAP=256; exec java -Xms128M -Xmx"${HEAP}M" -Dserver.port={{SERVER_PORT}} -Dserver.address=0.0.0.0 -jar Lavalink.jar',
            stop="^C",
            startup_done="Lavalink is ready to accept connections",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
JAR_URL="$(curl -fsSL https://api.github.com/repos/lavalink-devs/Lavalink/releases/latest | jq -r '.assets[] | select(.name == "Lavalink.jar") | .browser_download_url' | head -n1)"
vnh_download "${JAR_URL}" "/mnt/server/Lavalink.jar"
if [[ ! -f /mnt/server/application.yml ]]; then
    PW="${LAVALINK_PASSWORD:-$(openssl rand -hex 20)}"
    cat > /mnt/server/application.yml <<EOF
server:
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "${PW}"
    sources:
      youtube: false
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
EOF
    chmod 600 /mnt/server/application.yml
fi
''',
            variables=[
                VariableSpec("Lavalink Password", "Strong auth password written to application.yml on first install (auto-generated if blank).", "LAVALINK_PASSWORD", "", rules="nullable|string|min:12|max:128"),
            ],
            upstream_license="MIT",
            upstream_url="https://lavalink.dev",
        ),

        # 2. Uptime Kuma
        EggSpec(
            id="uptime-kuma",
            name="Vietnam Hosting — Uptime Kuma",
            category="applications",
            description="Self-hosted Uptime Kuma monitoring dashboard on Node.js LTS bound to 0.0.0.0:{{SERVER_PORT}} with persistent SQLite data.",
            icon="uptime-kuma",
            supported_versions=["1.23.x / 2.x"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/nodejs/22/Dockerfile",
            docker_images={"Node.js 22 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_22"},
            custom_docker_images={"Node.js 22 LTS": f"{GHCR_NAMESPACE}:nodejs_22"},
            startup='export UPTIME_KUMA_HOST=0.0.0.0 UPTIME_KUMA_PORT={{SERVER_PORT}} DATA_DIR=/home/container/data/; exec node server/server.js',
            stop="^C",
            startup_done="Listening on",
            install_body=r'''
mkdir -p /mnt/server/data
if [[ ! -d /mnt/server/.git ]]; then
    git clone --depth 1 https://github.com/louislam/uptime-kuma.git /tmp/kuma
    cp -an /tmp/kuma/. /mnt/server/
    rm -rf /tmp/kuma
else
    git -C /mnt/server pull --ff-only || true
fi
cd /mnt/server
npm run setup || npm ci --omit=dev
''',
            variables=[],
            upstream_license="MIT",
            upstream_url="https://uptime.kuma.pet",
        ),

        # 3. n8n
        EggSpec(
            id="n8n",
            name="Vietnam Hosting — n8n Workflow Automation",
            category="applications",
            description="Fair-code n8n workflow automation platform bound to 0.0.0.0:{{SERVER_PORT}} (Docker Socket execution disabled in shared Wings).",
            icon="n8n",
            supported_versions=["1.x (Node.js 22 LTS)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/nodejs/22/Dockerfile",
            docker_images={"Node.js 22 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_22"},
            custom_docker_images={"Node.js 22 LTS": f"{GHCR_NAMESPACE}:nodejs_22"},
            startup='export N8N_HOST=0.0.0.0 N8N_PORT={{SERVER_PORT}} N8N_USER_FOLDER=/home/container/data N8N_DIAGNOSTICS_ENABLED=false; exec ./node_modules/.bin/n8n start',
            stop="^C",
            startup_done="Editor is now accessible via:|n8n ready on",
            install_body='mkdir -p /mnt/server/data\ncd /mnt/server\nif [[ ! -f package.json ]]; then npm init -y >/dev/null; fi\nnpm install n8n --omit=dev\n',
            variables=[
                VariableSpec("Public Webhook URL", "External HTTPS URL configured on platform reverse proxy.", "WEBHOOK_URL", "", rules="nullable|string|max:256"),
                VariableSpec("Encryption Key", "Stable encryption key for n8n credentials (never logged).", "N8N_ENCRYPTION_KEY", "", rules="nullable|string|max:128"),
            ],
            upstream_license="Sustainable Use License",
            upstream_url="https://n8n.io",
            notes="Runs unprivileged; host Docker Socket / privileged nodes are unsupported by default.",
        ),

        # 4. Gitea
        EggSpec(
            id="gitea",
            name="Vietnam Hosting — Gitea Git Server",
            category="applications",
            description="Lightweight Go-based Gitea self-hosted Git service downloaded directly from official dl.gitea.com (AMD64 & ARM64).",
            icon="gitea",
            supported_versions=["1.23.x"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=2048,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='export GITEA_WORK_DIR=/home/container/data; exec ./gitea web -p {{SERVER_PORT}} -c /home/container/data/custom/conf/app.ini',
            stop="^C",
            startup_done="Listen: http://",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && GARCH="arm64" || GARCH="amd64"
VER="${GITEA_VERSION}"
vnh_download "https://dl.gitea.com/gitea/${VER}/gitea-${VER}-linux-${GARCH}" "/mnt/server/gitea"
chmod +x /mnt/server/gitea
mkdir -p /mnt/server/data/custom/conf
''',
            variables=[VariableSpec("Gitea Version", "Official Gitea release version.", "GITEA_VERSION", "1.23.4", rules="required|string|max:32")],
            upstream_license="MIT",
            upstream_url="https://about.gitea.com",
        ),

        # 5. Forgejo
        EggSpec(
            id="forgejo",
            name="Vietnam Hosting — Forgejo Git Forge",
            category="applications",
            description="Community-governed GPL Forgejo self-hosted Git forge downloaded from official codeberg.org/forgejo/forgejo releases.",
            icon="forgejo",
            supported_versions=["10.0 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=2048,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='export FORGEJO_WORK_DIR=/home/container/data; exec ./forgejo web -p {{SERVER_PORT}} -c /home/container/data/custom/conf/app.ini',
            stop="^C",
            startup_done="Listen: http://",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && FARCH="arm64" || FARCH="amd64"
VER="${FORGEJO_VERSION}"
vnh_download "https://codeberg.org/forgejo/forgejo/releases/download/v${VER}/forgejo-${VER}-linux-${FARCH}" "/mnt/server/forgejo"
chmod +x /mnt/server/forgejo
mkdir -p /mnt/server/data/custom/conf
''',
            variables=[VariableSpec("Forgejo Version", "Official Forgejo LTS release version.", "FORGEJO_VERSION", "10.0.1", rules="required|string|max:32")],
            upstream_license="GPL-3.0-or-later",
            upstream_url="https://forgejo.org",
        ),

        # 6. Vaultwarden
        EggSpec(
            id="vaultwarden",
            name="Vietnam Hosting — Vaultwarden Password Manager",
            category="applications",
            description="Lightweight Rust Bitwarden-compatible Vaultwarden server (must be fronted by HTTPS reverse proxy for WebCrypto).",
            icon="vaultwarden",
            supported_versions=["1.33"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/vaultwarden/Dockerfile",
            docker_images={"Vaultwarden 1.33 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:vaultwarden_1.33"},
            custom_docker_images={"Vaultwarden 1.33": f"{GHCR_NAMESPACE}:vaultwarden_1.33"},
            startup='export ROCKET_ADDRESS=0.0.0.0 ROCKET_PORT={{SERVER_PORT}} DATA_FOLDER=/home/container/data SIGNUPS_ALLOWED="${SIGNUPS_ALLOWED}"; exec /vaultwarden',
            stop="^C",
            startup_done="Rocket has launched from",
            install_body='mkdir -p /mnt/server/data\n',
            variables=[
                VariableSpec("Allow New Signups", "Set to false after creating initial accounts.", "SIGNUPS_ALLOWED", "false", rules="required|string|in:true,false"),
                VariableSpec("Domain URL", "Public HTTPS URL managed by platform reverse proxy.", "DOMAIN", "", rules="nullable|string|max:256"),
                VariableSpec("Admin Token (Argon2 PHC)", "Optional Argon2id hashed admin token (never plaintext).", "ADMIN_TOKEN", "", rules="nullable|string|max:512"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://github.com/dani-garcia/vaultwarden",
        ),

        # 7. File Browser
        EggSpec(
            id="filebrowser",
            name="Vietnam Hosting — File Browser",
            category="applications",
            description="Web-based File Browser scoped strictly to /home/container/files with auto-generated admin password.",
            icon="filebrowser",
            supported_versions=["2.32+"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=1024,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./filebrowser --address 0.0.0.0 --port {{SERVER_PORT}} --root /home/container/files --database /home/container/filebrowser.db',
            stop="^C",
            startup_done="Listening on",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && FARCH="arm64" || FARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/filebrowser/filebrowser/releases/latest | jq -r --arg a "linux-${FARCH}-filebrowser.tar.gz" '.assets[] | select(.name == $a) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/fb.tar.gz"
tar -xzf /tmp/fb.tar.gz -C /mnt/server filebrowser
chmod +x /mnt/server/filebrowser
rm -f /tmp/fb.tar.gz
mkdir -p /mnt/server/files
''',
            variables=[],
            upstream_license="Apache-2.0",
            upstream_url="https://filebrowser.org",
        ),

        # 8. Syncthing
        EggSpec(
            id="syncthing",
            name="Vietnam Hosting — Syncthing",
            category="applications",
            description="Continuous decentralized file synchronization with Syncthing web GUI on 0.0.0.0:{{SERVER_PORT}}.",
            icon="syncthing",
            supported_versions=["1.29+"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=2048,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./syncthing --home=/home/container/config --gui-address="0.0.0.0:{{SERVER_PORT}}" --no-browser --no-restart',
            stop="^C",
            startup_done="GUI and API listening on",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && SARCH="arm64" || SARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/syncthing/syncthing/releases/latest | jq -r --arg a "linux-${SARCH}-" '.assets[] | select(.name | contains($a) and endswith(".tar.gz")) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/syncthing.tar.gz"
tar -xzf /tmp/syncthing.tar.gz --strip-components=1 -C /mnt/server --wildcards "*/syncthing"
chmod +x /mnt/server/syncthing
rm -f /tmp/syncthing.tar.gz
mkdir -p /mnt/server/config /mnt/server/sync
''',
            variables=[],
            upstream_license="MPL-2.0",
            upstream_url="https://syncthing.net",
        ),

        # 9. MinIO
        EggSpec(
            id="minio",
            name="Vietnam Hosting — MinIO S3 Object Storage",
            category="applications",
            description="S3-compatible MinIO object storage server with mandatory strong root credentials and console allocation port.",
            icon="minio",
            supported_versions=["Official MinIO Release"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=4096,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup=(
                'if [[ ! -f /home/container/.minio_secret ]]; then '
                '  PW="${MINIO_ROOT_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  printf "%s" "${PW}" > /home/container/.minio_secret; chmod 600 /home/container/.minio_secret; '
                'fi; '
                'export MINIO_ROOT_USER="${MINIO_ROOT_USER}" MINIO_ROOT_PASSWORD="$(cat /home/container/.minio_secret)"; '
                'exec ./minio server /home/container/data --address ":{{SERVER_PORT}}" --console-address ":${CONSOLE_PORT}"'
            ),
            stop="^C",
            startup_done="S3-API:|MinIO Object Storage Server",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && MARCH="arm64" || MARCH="amd64"
vnh_download "https://dl.min.io/server/minio/release/linux-${MARCH}/minio" "/mnt/server/minio"
chmod +x /mnt/server/minio
mkdir -p /mnt/server/data
''',
            variables=[
                VariableSpec("MinIO Root User", "Root access key username.", "MINIO_ROOT_USER", "vnhminio", rules="required|alpha_dash|min:4|max:64"),
                VariableSpec("MinIO Root Password", "Strong root secret key (auto-generated if empty).", "MINIO_ROOT_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Console Port", "Additional allocation port for MinIO Web Console.", "CONSOLE_PORT", "9001", rules="required|integer|between:1024,65535"),
            ],
            upstream_license="AGPL-3.0",
            upstream_url="https://min.io",
        ),

        # 10. RabbitMQ
        EggSpec(
            id="rabbitmq",
            name="Vietnam Hosting — RabbitMQ 4.0",
            category="applications",
            description="Enterprise RabbitMQ 4.0 AMQP message broker with container-scoped mnesia data and management plugin.",
            icon="rabbitmq",
            supported_versions=["4.0"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/rabbitmq/Dockerfile",
            docker_images={"RabbitMQ 4.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rabbitmq_4.0"},
            custom_docker_images={"RabbitMQ 4.0": f"{GHCR_NAMESPACE}:rabbitmq_4.0"},
            startup='export RABBITMQ_MNESIA_BASE=/home/container/mnesia RABBITMQ_LOG_BASE=/home/container/logs RABBITMQ_NODE_PORT={{SERVER_PORT}} RABBITMQ_CONFIG_FILE=/home/container/rabbitmq.conf; exec rabbitmq-server',
            stop="^C",
            startup_done="Server startup complete",
            install_body=r'''
mkdir -p /mnt/server/mnesia /mnt/server/logs
if [[ ! -f /mnt/server/rabbitmq.conf ]]; then
    PW="${RABBITMQ_DEFAULT_PASS:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"
    cat > /mnt/server/rabbitmq.conf <<EOF
listeners.tcp.default = 0.0.0.0:{{SERVER_PORT}}
default_user = ${RABBITMQ_DEFAULT_USER:-vnhmq}
default_pass = ${PW}
loopback_users = none
EOF
    chmod 600 /mnt/server/rabbitmq.conf
fi
''',
            variables=[
                VariableSpec("Default User", "Initial RabbitMQ user.", "RABBITMQ_DEFAULT_USER", "vnhmq", rules="required|alpha_dash|max:32"),
                VariableSpec("Default Password", "Strong initial password (auto-generated if blank).", "RABBITMQ_DEFAULT_PASS", "", rules="nullable|string|min:12|max:128"),
            ],
            upstream_license="MPL-2.0",
            upstream_url="https://www.rabbitmq.com",
        ),

        # 11. Mosquitto MQTT
        EggSpec(
            id="mosquitto",
            name="Vietnam Hosting — Mosquitto MQTT Broker",
            category="applications",
            description="Lightweight Eclipse Mosquitto 2.0 MQTT broker enforcing authenticated connections (allow_anonymous false).",
            icon="mosquitto",
            supported_versions=["2.0.21"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/mosquitto/Dockerfile",
            docker_images={"Mosquitto 2.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:mosquitto_2.0"},
            custom_docker_images={"Mosquitto 2.0": f"{GHCR_NAMESPACE}:mosquitto_2.0"},
            startup='sed "s|__PORT__|{{SERVER_PORT}}|g" /home/container/mosquitto.conf.tpl > /home/container/mosquitto.conf; exec mosquitto -c /home/container/mosquitto.conf',
            stop="^C",
            startup_done="mosquitto version .* running",
            install_body=r'''
mkdir -p /mnt/server/data /mnt/server/logs
if [[ ! -f /mnt/server/mosquitto.conf.tpl ]]; then
cat > /mnt/server/mosquitto.conf.tpl <<'EOF'
listener __PORT__ 0.0.0.0
allow_anonymous false
password_file /home/container/passwd
persistence true
persistence_location /home/container/data/
EOF
fi
touch /mnt/server/passwd && chmod 600 /mnt/server/passwd
''',
            variables=[],
            upstream_license="EPL-2.0 / EDL-1.0",
            upstream_url="https://mosquitto.org",
        ),

        # 12. Prometheus
        EggSpec(
            id="prometheus",
            name="Vietnam Hosting — Prometheus Monitoring",
            category="applications",
            description="Prometheus TSDB metrics collector downloaded from official GitHub Releases (AMD64 & ARM64).",
            icon="prometheus",
            supported_versions=["3.2+"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=4096,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./prometheus --config.file=/home/container/prometheus.yml --storage.tsdb.path=/home/container/data --storage.tsdb.retention.time="${RETENTION_TIME}" --web.listen-address="0.0.0.0:{{SERVER_PORT}}"',
            stop="^C",
            startup_done="Server is ready to receive web requests",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && PARCH="arm64" || PARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/prometheus/prometheus/releases/latest | jq -r --arg a "linux-${PARCH}.tar.gz" '.assets[] | select(.name | endswith($a)) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/prom.tar.gz"
tar -xzf /tmp/prom.tar.gz --strip-components=1 -C /mnt/server
rm -f /tmp/prom.tar.gz
mkdir -p /mnt/server/data
if [[ ! -f /mnt/server/prometheus.yml ]]; then
    printf "global:\n  scrape_interval: 15s\nscrape_configs:\n  - job_name: 'prometheus'\n    static_configs:\n      - targets: ['127.0.0.1:{{SERVER_PORT}}']\n" > /mnt/server/prometheus.yml
fi
''',
            variables=[VariableSpec("TSDB Retention", "Data retention window (e.g. 15d, 30d).", "RETENTION_TIME", "15d", rules="required|string|max:16")],
            upstream_license="Apache-2.0",
            upstream_url="https://prometheus.io",
        ),

        # 13. Grafana
        EggSpec(
            id="grafana",
            name="Vietnam Hosting — Grafana Observability",
            category="applications",
            description="Grafana OSS 11.5 visualization dashboard running unprivileged with persistent data and plugins inside /home/container.",
            icon="grafana",
            supported_versions=["11.5"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/grafana/Dockerfile",
            docker_images={"Grafana 11.5 OSS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:grafana_11.5"},
            custom_docker_images={"Grafana 11.5 OSS": f"{GHCR_NAMESPACE}:grafana_11.5"},
            startup='export GF_SERVER_HTTP_ADDR=0.0.0.0 GF_SERVER_HTTP_PORT={{SERVER_PORT}} GF_PATHS_DATA=/home/container/data GF_PATHS_LOGS=/home/container/logs GF_PATHS_PLUGINS=/home/container/plugins; exec grafana server --homepath=/usr/share/grafana',
            stop="^C",
            startup_done="HTTP Server Listen",
            install_body='mkdir -p /mnt/server/data /mnt/server/logs /mnt/server/plugins\n',
            variables=[
                VariableSpec("Initial Admin User", "Grafana admin username.", "GF_SECURITY_ADMIN_USER", "vnhadmin", rules="required|alpha_dash|max:32"),
                VariableSpec("Initial Admin Password", "Strong initial Grafana password (never use weak defaults).", "GF_SECURITY_ADMIN_PASSWORD", "", rules="required|string|min:12|max:128"),
            ],
            upstream_license="AGPL-3.0",
            upstream_url="https://grafana.com",
        ),

        # 14. ntfy
        EggSpec(
            id="ntfy",
            name="Vietnam Hosting — ntfy Push Notification Server",
            category="applications",
            description="Self-hosted HTTP pub-sub push notification server (ntfy) downloaded from official GitHub Releases.",
            icon="ntfy",
            supported_versions=["2.11+"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=1024,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./ntfy serve --listen-http "0.0.0.0:{{SERVER_PORT}}" --cache-file /home/container/cache.db --auth-file /home/container/user.db --auth-default-access "${AUTH_DEFAULT_ACCESS}"',
            stop="^C",
            startup_done="Listening on",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && NARCH="arm64" || NARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/binwiederhier/ntfy/releases/latest | jq -r --arg a "linux_${NARCH}.tar.gz" '.assets[] | select(.name | endswith($a)) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/ntfy.tar.gz"
tar -xzf /tmp/ntfy.tar.gz --strip-components=1 -C /mnt/server --wildcards "*/ntfy"
chmod +x /mnt/server/ntfy
rm -f /tmp/ntfy.tar.gz
''',
            variables=[
                VariableSpec("Default Topic Access", "Default access control (`deny-all` recommended for private instances).", "AUTH_DEFAULT_ACCESS", "deny-all", rules="required|string|in:deny-all,read-only,write-only,read-write"),
            ],
            upstream_license="Apache-2.0 / GPL-2.0",
            upstream_url="https://ntfy.sh",
        ),

        # 15. SearXNG
        EggSpec(
            id="searxng",
            name="Vietnam Hosting — SearXNG Privacy Metasearch",
            category="applications",
            description="Privacy-respecting SearXNG metasearch engine with auto-generated secret key and persistent settings.yml.",
            icon="searxng",
            supported_versions=["2025/2026 Pinned"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/searxng/Dockerfile",
            docker_images={"SearXNG (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:searxng_2026"},
            custom_docker_images={"SearXNG": f"{GHCR_NAMESPACE}:searxng_2026"},
            startup='export SEARXNG_SETTINGS_PATH=/home/container/settings.yml SEARXNG_BIND_ADDRESS=0.0.0.0 SEARXNG_PORT={{SERVER_PORT}}; exec granian --interface wsgi --host 0.0.0.0 --port {{SERVER_PORT}} searx.webapp:app',
            stop="^C",
            startup_done="Listening at:|Serving on",
            install_body=r'''
if [[ ! -f /mnt/server/settings.yml ]]; then
    SEC="$(openssl rand -hex 32)"
    cat > /mnt/server/settings.yml <<EOF
use_default_settings: true
server:
  secret_key: "${SEC}"
  limiter: true
  image_proxy: true
EOF
    chmod 600 /mnt/server/settings.yml
fi
''',
            variables=[],
            upstream_license="AGPL-3.0",
            upstream_url="https://docs.searxng.org",
        ),

        # 16. JupyterLab
        EggSpec(
            id="jupyterlab",
            name="Vietnam Hosting — JupyterLab Workspace",
            category="applications",
            description="Interactive JupyterLab Python data-science notebook server bound to 0.0.0.0:{{SERVER_PORT}} with mandatory token authentication (no Docker Socket / no GPU by default).",
            icon="jupyter",
            supported_versions=["JupyterLab 4 (Python 3.12/3.13)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={"Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13"},
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup=(
                'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; '
                'if [[ ! -f /home/container/.jupyter_token ]]; then '
                '  TOK="${JUPYTER_TOKEN:-$(openssl rand -hex 24)}"; printf "%s" "${TOK}" > /home/container/.jupyter_token; chmod 600 /home/container/.jupyter_token; '
                'fi; '
                'exec jupyter lab --ip=0.0.0.0 --port={{SERVER_PORT}} --no-browser --notebook-dir=/home/container/notebooks '
                '--IdentityProvider.token="$(cat /home/container/.jupyter_token)"'
            ),
            stop="^C",
            startup_done="Jupyter Server .* is running at:",
            install_body='mkdir -p /mnt/server/notebooks\npython3 -m venv /mnt/server/.venv\n/mnt/server/.venv/bin/pip install --no-cache-dir --upgrade pip jupyterlab\n',
            variables=[
                VariableSpec("Jupyter Access Token", "Auth token (auto-generated into .jupyter_token if blank).", "JUPYTER_TOKEN", "", rules="nullable|string|min:16|max:128"),
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://jupyter.org",
            privileged_requirements={
                "requires_privileged": False,
                "requires_docker_socket": False,
                "requires_gpu": False,
                "requires_kernel_features": False,
                "notes": "CPU-only unprivileged notebook workspace. GPU passthrough and Docker Socket are NOT enabled by default and require explicit admin Node configuration.",
            },
        ),

        # 17. Code Server
        EggSpec(
            id="code-server",
            name="Vietnam Hosting — Code Server (VS Code Web)",
            category="applications",
            description="Browser-based VS Code (code-server) workspace running unprivileged in /home/container/workspace with mandatory password auth (no Docker Socket).",
            icon="vscode",
            supported_versions=["4.98+"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup=(
                'if [[ ! -f /home/container/.cs_password ]]; then '
                '  PW="${CS_PASSWORD:-$(openssl rand -base64 20 | tr -dc A-Za-z0-9 | head -c 20)}"; '
                '  printf "%s" "${PW}" > /home/container/.cs_password; chmod 600 /home/container/.cs_password; '
                'fi; '
                'export PASSWORD="$(cat /home/container/.cs_password)"; '
                'exec ./code-server/bin/code-server --bind-addr "0.0.0.0:{{SERVER_PORT}}" --user-data-dir /home/container/.local/share/code-server --extensions-dir /home/container/.local/share/code-server/extensions /home/container/workspace'
            ),
            stop="^C",
            startup_done="HTTP server listening on",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
ARCH="$(uname -m)"; [[ "${ARCH}" == "aarch64" ]] && CARCH="arm64" || CARCH="amd64"
URL="$(curl -fsSL https://api.github.com/repos/coder/code-server/releases/latest | jq -r --arg a "linux-${CARCH}.tar.gz" '.assets[] | select(.name | endswith($a)) | .browser_download_url' | head -n1)"
vnh_download "${URL}" "/tmp/cs.tar.gz"
mkdir -p /mnt/server/code-server /mnt/server/workspace
tar -xzf /tmp/cs.tar.gz --strip-components=1 -C /mnt/server/code-server
rm -f /tmp/cs.tar.gz
''',
            variables=[
                VariableSpec("Web IDE Password", "Strong login password (auto-generated into .cs_password if empty).", "CS_PASSWORD", "", rules="nullable|string|min:12|max:128"),
            ],
            upstream_license="MIT",
            upstream_url="https://coder.com",
            privileged_requirements={
                "requires_privileged": False,
                "requires_docker_socket": False,
                "requires_gpu": False,
                "requires_kernel_features": False,
                "notes": "Unprivileged workspace only. Docker-in-Docker and Docker Socket access are NOT supported by default.",
            },
        ),

        # 18. Open WebUI
        EggSpec(
            id="open-webui",
            name="Vietnam Hosting — Open WebUI (CPU / Remote LLM)",
            category="applications",
            description="Open WebUI chat interface connecting to Ollama CPU or OpenAI-compatible APIs (CPU-only by default; GPU requires admin Node setup).",
            icon="open-webui",
            supported_versions=["0.5.x"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/open-webui/Dockerfile",
            docker_images={"Open WebUI 0.5 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:open_webui_0.5"},
            custom_docker_images={"Open WebUI 0.5": f"{GHCR_NAMESPACE}:open_webui_0.5"},
            startup='export PORT={{SERVER_PORT}} HOST=0.0.0.0 DATA_DIR=/home/container/data OLLAMA_BASE_URL="${OLLAMA_BASE_URL}" WEBUI_AUTH=true; exec uvicorn open_webui.main:app --host 0.0.0.0 --port {{SERVER_PORT}}',
            stop="^C",
            startup_done="Application startup complete|Uvicorn running",
            install_body='mkdir -p /mnt/server/data\n',
            variables=[
                VariableSpec("Ollama Base URL", "Upstream Ollama API endpoint (e.g. http://127.0.0.1:11434).", "OLLAMA_BASE_URL", "", rules="nullable|string|max:256"),
            ],
            upstream_license="MIT (Open WebUI License)",
            upstream_url="https://openwebui.com",
            privileged_requirements={
                "requires_privileged": False,
                "requires_docker_socket": False,
                "requires_gpu": False,
                "requires_kernel_features": False,
                "notes": "Runs in CPU mode / remote API client mode. Local GPU inference requires dedicated GPU Node configuration by administrator.",
            },
        ),

        # 19. Ollama CPU
        EggSpec(
            id="ollama-cpu",
            name="Vietnam Hosting — Ollama CPU Inference Server",
            category="applications",
            description="CPU-only Ollama 0.6 local LLM inference server storing models in /home/container/.ollama/models (GPU acceleration is NOT enabled by default).",
            icon="ollama",
            supported_versions=["0.6.2 (CPU Only)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=4096,
            recommended_ram_mb=8192,
            minimum_disk_mb=16384,
            resource_basis="recommended_estimate",
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/ollama-cpu/Dockerfile",
            docker_images={"Ollama CPU 0.6 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:ollama_cpu_0.6"},
            custom_docker_images={"Ollama CPU 0.6": f"{GHCR_NAMESPACE}:ollama_cpu_0.6"},
            startup='export OLLAMA_HOST="${BIND_ADDRESS}:{{SERVER_PORT}}" OLLAMA_MODELS=/home/container/.ollama/models OLLAMA_NUM_PARALLEL=1; exec ollama serve',
            stop="^C",
            startup_done="Listening on",
            install_body='mkdir -p /mnt/server/.ollama/models\n',
            variables=[
                VariableSpec("Bind Address", "Default 127.0.0.1 (admin may enable 0.0.0.0 behind auth proxy — Ollama has no built-in auth!).", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="MIT",
            upstream_url="https://ollama.com",
            privileged_requirements={
                "requires_privileged": False,
                "requires_docker_socket": False,
                "requires_gpu": False,
                "requires_kernel_features": False,
                "notes": "CPU-ONLY default profile. GPU passthrough (NVIDIA Container Toolkit / ROCm) is NOT enabled in standard Wings shared containers and requires dedicated admin GPU node setup. Never expose Ollama directly to the public Internet without an authenticating reverse proxy.",
            },
            security_notes_vi="- **Cảnh báo bảo mật:** Ollama không có lớp xác thực tích hợp sẵn. Mặc định bind `127.0.0.1` — quản trị viên tuyệt đối không mở trực tiếp ra Internet nếu không có Reverse Proxy xác thực.\n- **Chế độ CPU:** Egg này chỉ chạy suy luận CPU. Tăng tốc GPU yêu cầu Node chuyên dụng được quản trị viên cấu hình NVIDIA/ROCm riêng.",
        ),
    ]
