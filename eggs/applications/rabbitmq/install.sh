#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — RabbitMQ 4.0 (rabbitmq)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — RabbitMQ 4.0. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — RabbitMQ 4.0."
    VNH_REINSTALL=0
fi

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

{
    printf 'egg_id=%s\n' "rabbitmq"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — RabbitMQ 4.0."
