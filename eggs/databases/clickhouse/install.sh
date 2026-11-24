#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — ClickHouse 25 LTS (clickhouse)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — ClickHouse 25 LTS. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — ClickHouse 25 LTS."
    VNH_REINSTALL=0
fi

mkdir -p /mnt/server/data /mnt/server/tmp /mnt/server/logs /mnt/server/backups
if [[ ! -f /mnt/server/config.xml.tpl ]]; then
cat > /mnt/server/config.xml.tpl <<'EOF'
<clickhouse>
    <logger><level>information</level><console>1</console></logger>
    <http_port>__PORT__</http_port>
    <listen_host>__BIND__</listen_host>
    <path>/home/container/data/</path>
    <tmp_path>/home/container/tmp/</tmp_path>
    <user_files_path>/home/container/data/user_files/</user_files_path>
    <format_schema_path>/home/container/data/format_schemas/</format_schema_path>
    <users_config>users.xml</users_config>
</clickhouse>
EOF
fi
if [[ ! -f /mnt/server/users.xml ]]; then
    PW="${CLICKHOUSE_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"
    SHA="$(printf '%s' "${PW}" | sha256sum | awk '{print $1}')"
    cat > /mnt/server/users.xml <<EOF
<clickhouse>
    <profiles><default/></profiles>
    <quotas><default/></quotas>
    <users>
        <default>
            <password_sha256_hex>${SHA}</password_sha256_hex>
            <networks><ip>::/0</ip></networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>
</clickhouse>
EOF
    chmod 600 /mnt/server/users.xml
fi

{
    printf 'egg_id=%s\n' "clickhouse"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — ClickHouse 25 LTS."
