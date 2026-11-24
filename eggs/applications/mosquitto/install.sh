#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Egg Installation Script Template
# Egg: Vietnam Hosting — Mosquitto MQTT Broker (mosquitto)
# Website: https://vietnam-hosting.net
# ==============================================================================
set -euo pipefail

SERVER_DIR="/mnt/server"
INSTALL_MARKER="${SERVER_DIR}/.vnh_installed"
mkdir -p "${SERVER_DIR}"
cd "${SERVER_DIR}"

if [[ -f "${INSTALL_MARKER}" ]]; then
    echo "[VNH][INSTALL] Reinstall detected for Vietnam Hosting — Mosquitto MQTT Broker. Preserving user data."
    VNH_REINSTALL=1
else
    echo "[VNH][INSTALL] First-time installation for Vietnam Hosting — Mosquitto MQTT Broker."
    VNH_REINSTALL=0
fi

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

{
    printf 'egg_id=%s\n' "mosquitto"
    printf 'version=%s\n' "1.0.0"
    printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
} > "${INSTALL_MARKER}"

echo "[VNH][INSTALL] Completed installation for Vietnam Hosting — Mosquitto MQTT Broker."
