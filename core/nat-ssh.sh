#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — NAT Linux Container Hosting Runtime Module
# Website: https://vietnam-hosting.net
# License: MIT
#
# Architecture:
#   Internet -> Public Node IP -> Pterodactyl Allocation -> Container -> Service
#
# Security & Container Boundaries:
#   - Unprivileged execution ONLY (container user; never root on host)
#   - No privileged mode, no CAP_SYS_ADMIN, no Docker socket, no host network
#   - No systemd required; uses lightweight signal-aware process supervision
#   - Never modifies host iptables/nftables/routing
#   - Generates persistent per-container SSH host keys under /home/container/.ssh
#   - Disables root SSH login and disables password SSH authentication by default
#   - Enforces SSH Public Key Authentication when SSH daemon is enabled
# ==============================================================================

set -euo pipefail

VNH_CORE_DIR="${VNH_CORE_DIR:-/opt/vnh}"
if [[ -r "${VNH_CORE_DIR}/environment.sh" ]]; then
    # shellcheck source=environment.sh
    source "${VNH_CORE_DIR}/environment.sh"
fi

HOME_DIR="${HOME:-/home/container}"
SSH_DIR="${HOME_DIR}/.ssh"
HOSTKEY_DIR="${SSH_DIR}/host_keys"
SSH_PORT="${SSH_PORT:-${SERVER_PORT:-}}"
ENABLE_SSH="${ENABLE_SSH:-1}"
ENABLE_CRON="${ENABLE_CRON:-1}"
SSH_AUTHORIZED_KEYS="${SSH_AUTHORIZED_KEYS:-}"
STARTUP_SCRIPT="${STARTUP_SCRIPT:-startup.sh}"

declare -a CHILD_PIDS=()

cleanup() {
    vnh_log_info "Stopping NAT Linux container services gracefully..."
    local pid
    for pid in "${CHILD_PIDS[@]:-}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    sleep 2
    for pid in "${CHILD_PIDS[@]:-}"; do
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    exit 0
}

trap cleanup TERM INT HUP

setup_nss_wrapper() {
    local cur_uid cur_gid lib_nss
    cur_uid="$(id -u)"
    cur_gid="$(id -g)"
    lib_nss="$(find /usr/lib /lib -name 'libnss_wrapper.so*' 2>/dev/null | head -n1 || true)"
    if [[ -n "$lib_nss" ]]; then
        mkdir -p "${HOME_DIR}/run"
        grep -v '^container:' /etc/passwd > "${HOME_DIR}/run/passwd" 2>/dev/null || true
        printf 'container:x:%s:%s:Vietnam Hosting Container:%s:/bin/bash\n' \
            "$cur_uid" "$cur_gid" "$HOME_DIR" >> "${HOME_DIR}/run/passwd"
        grep -v '^container:' /etc/group > "${HOME_DIR}/run/group" 2>/dev/null || true
        printf 'container:x:%s:\n' "$cur_gid" >> "${HOME_DIR}/run/group"
        export LD_PRELOAD="${lib_nss}${LD_PRELOAD:+:${LD_PRELOAD}}"
        export NSS_WRAPPER_PASSWD="${HOME_DIR}/run/passwd"
        export NSS_WRAPPER_GROUP="${HOME_DIR}/run/group"
    fi
}

print_linux_info() {
    local os_pretty kernel arch mem_mb cpus user_name
    os_pretty="$(vnh_detect_os)"
    kernel="$(uname -r)"
    arch="$(vnh_detect_arch)"
    mem_mb="$(vnh_detect_memory_mb)"
    cpus="$(vnh_detect_cpu_limit)"
    user_name="$(whoami 2>/dev/null || printf 'container')"

    printf '==============================================================\n'
    printf 'VIETNAM HOSTING — NAT LINUX CONTAINER ENVIRONMENT\n'
    printf '==============================================================\n'
    printf 'Distribution:      %s\n' "$os_pretty"
    printf 'Host Kernel:       %s (shared Linux kernel)\n' "$kernel"
    printf 'Architecture:      %s\n' "$arch"
    printf 'Memory Allocation: %s MiB\n' "$mem_mb"
    printf 'CPU Quota:         %s vCPU(s)\n' "$cpus"
    printf 'Primary Port:      %s\n' "${SERVER_PORT:-N/A}"
    printf 'SSH Port:          %s\n' "${SSH_PORT:-Disabled}"
    printf 'User Context:      %s (uid=%s, unprivileged container)\n' "$user_name" "$(id -u)"
    printf 'Notice:            Container runtime (not KVM VPS). Use user-space\n'
    printf '                   package managers (pip/npm/cargo/brew/nix/mise)\n'
    printf '                   under %s. System-wide root/systemd requires KVM.\n' "$HOME_DIR"
    printf '==============================================================\n'
}

setup_ssh_keys() {
    mkdir -p "$SSH_DIR" "$HOSTKEY_DIR" "${HOME_DIR}/run"
    chmod 700 "$SSH_DIR" "$HOSTKEY_DIR"

    # Provision authorized_keys from panel variable without wiping existing keys
    local auth_file="${SSH_DIR}/authorized_keys"
    touch "$auth_file"
    chmod 600 "$auth_file"

    if [[ -n "$SSH_AUTHORIZED_KEYS" ]]; then
        if ! grep -Fqx "$SSH_AUTHORIZED_KEYS" "$auth_file" 2>/dev/null; then
            printf '%s\n' "$SSH_AUTHORIZED_KEYS" >> "$auth_file"
            vnh_log_info "Registered SSH public key from SSH_AUTHORIZED_KEYS."
        fi
    fi

    # Generate persistent container-scoped host keys if missing
    if command -v dropbearkey >/dev/null 2>&1; then
        if [[ ! -f "${HOSTKEY_DIR}/dropbear_ed25519_host_key" ]]; then
            dropbearkey -t ed25519 -f "${HOSTKEY_DIR}/dropbear_ed25519_host_key" >/dev/null 2>&1
            chmod 600 "${HOSTKEY_DIR}/dropbear_ed25519_host_key"
            vnh_log_info "Generated persistent Dropbear Ed25519 SSH host key."
        fi
        if [[ ! -f "${HOSTKEY_DIR}/dropbear_ecdsa_host_key" ]]; then
            dropbearkey -t ecdsa -f "${HOSTKEY_DIR}/dropbear_ecdsa_host_key" >/dev/null 2>&1
            chmod 600 "${HOSTKEY_DIR}/dropbear_ecdsa_host_key"
        fi
    elif command -v ssh-keygen >/dev/null 2>&1; then
        if [[ ! -f "${HOSTKEY_DIR}/ssh_host_ed25519_key" ]]; then
            ssh-keygen -q -t ed25519 -N "" -f "${HOSTKEY_DIR}/ssh_host_ed25519_key"
            chmod 600 "${HOSTKEY_DIR}/ssh_host_ed25519_key"
            vnh_log_info "Generated persistent OpenSSH Ed25519 host key."
        fi
    fi
}

start_unprivileged_ssh() {
    if [[ "$ENABLE_SSH" != "1" ]] && [[ "$ENABLE_SSH" != "true" ]]; then
        vnh_log_info "Container SSH disabled (ENABLE_SSH=${ENABLE_SSH}). Use Pterodactyl Console & Wings SFTP."
        return 0
    fi

    if [[ -z "$SSH_PORT" ]] || ! vnh_validate_port "$SSH_PORT" "SSH_PORT"; then
        vnh_log_warn "No valid SSH_PORT allocation configured; skipping SSH daemon."
        return 0
    fi

    setup_ssh_keys

    if [[ ! -s "${SSH_DIR}/authorized_keys" ]]; then
        vnh_log_warn "No SSH public keys found in ${SSH_DIR}/authorized_keys. Password auth is disabled by policy."
        vnh_log_warn "Add your public key via SSH_AUTHORIZED_KEYS or ~/.ssh/authorized_keys to authenticate over SSH."
    fi

    # Prefer Dropbear for unprivileged multi-tenant containers (no privilege separation / root setuid requirement)
    if command -v dropbear >/dev/null 2>&1; then
        vnh_log_info "Starting unprivileged Dropbear SSH daemon on 0.0.0.0:${SSH_PORT} (pubkey-only, root login disabled)..."
        # -F foreground, -E log to stderr, -s disable password logins, -g disable root password, -w disallow root logins
        dropbear -F -E -s -g -w \
            -p "0.0.0.0:${SSH_PORT}" \
            -r "${HOSTKEY_DIR}/dropbear_ed25519_host_key" \
            -P "${HOME_DIR}/run/dropbear.pid" &
        CHILD_PIDS+=($!)
        return 0
    fi

    # Fallback: OpenSSH daemon running completely unprivileged (requires compatible sshd binary)
    if command -v sshd >/dev/null 2>&1 && [[ -f "${HOSTKEY_DIR}/ssh_host_ed25519_key" ]]; then
        local sshd_bin
        sshd_bin="$(command -v sshd)"
        local sshd_cfg="${SSH_DIR}/sshd_config"
        cat > "$sshd_cfg" <<EOF
Port ${SSH_PORT}
ListenAddress 0.0.0.0
HostKey ${HOSTKEY_DIR}/ssh_host_ed25519_key
PidFile ${HOME_DIR}/run/sshd.pid
AuthorizedKeysFile ${SSH_DIR}/authorized_keys
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
UsePAM no
PrintMotd no
Subsystem sftp internal-sftp
StrictModes no
EOF
        vnh_log_info "Starting unprivileged OpenSSH daemon on 0.0.0.0:${SSH_PORT} (pubkey-only, root login disabled)..."
        "$sshd_bin" -D -e -f "$sshd_cfg" &
        CHILD_PIDS+=($!)
        return 0
    fi

    vnh_log_warn "Neither dropbear nor sshd available in this image; use Pterodactyl Console and Wings SFTP."
    return 0
}

# Lightweight user-space scheduled task runner (compatible with non-root containers without crond/systemd).
start_userspace_scheduler() {
    if [[ "$ENABLE_CRON" != "1" ]] && [[ "$ENABLE_CRON" != "true" ]]; then
        return 0
    fi
    local cron_file="${HOME_DIR}/crontab"
    if [[ ! -f "$cron_file" ]]; then
        cat > "$cron_file" <<'EOF'
# Vietnam Hosting Container User-Space Schedule
# Format: <interval_seconds> <command>
# Example (disabled):
# 3600 /bin/bash /home/container/scripts/cleanup.sh
EOF
    fi

    if command -v supercronic >/dev/null 2>&1 && [[ -f "${HOME_DIR}/crontab.standard" ]]; then
        vnh_log_info "Starting supercronic user-space scheduler..."
        supercronic "${HOME_DIR}/crontab.standard" &
        CHILD_PIDS+=($!)
        return 0
    fi

    # Built-in lightweight interval task dispatcher for ~/crontab
    (
        declare -A last_run=()
        while true; do
            local now
            now="$(date +%s)"
            while IFS= read -r line || [[ -n "$line" ]]; do
                [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
                local interval cmd
                interval="$(printf '%s' "$line" | awk '{print $1}')"
                cmd="$(printf '%s' "$line" | cut -d' ' -f2-)"
                if [[ "$interval" =~ ^[0-9]+$ ]] && (( interval >= 10 )) && [[ -n "$cmd" ]]; then
                    local prev="${last_run[$cmd]:-0}"
                    if (( now - prev >= interval )); then
                        last_run["$cmd"]="$now"
                        /bin/bash -c "$cmd" >> "${HOME_DIR}/cron.log" 2>&1 &
                    fi
                fi
            done < "$cron_file"
            sleep 5
        done
    ) &
    CHILD_PIDS+=($!)
}

run_user_startup_script() {
    if [[ -n "$STARTUP_SCRIPT" ]] && vnh_validate_relpath "$STARTUP_SCRIPT" && [[ -f "${HOME_DIR}/${STARTUP_SCRIPT}" ]]; then
        vnh_log_info "Launching user startup script: ${HOME_DIR}/${STARTUP_SCRIPT}"
        local max_restarts="${VNH_MAX_RESTARTS:-5}"
        local restarts=0
        local backoff=2
        (
            while true; do
                /bin/bash "${HOME_DIR}/${STARTUP_SCRIPT}"
                local rc=$?
                if (( rc == 0 )); then
                    vnh_log_info "User startup script finished cleanly."
                    break
                fi
                restarts=$(( restarts + 1 ))
                if (( restarts > max_restarts )); then
                    vnh_log_error "User startup script hit restart limit (${max_restarts}). Stopping supervisor."
                    break
                fi
                vnh_log_warn "User startup script failed (exit ${rc}); restarting in ${backoff}s (${restarts}/${max_restarts})..."
                sleep "$backoff"
                backoff=$(( backoff * 2 ))
                (( backoff > 30 )) && backoff=30
            done
        ) &
        CHILD_PIDS+=($!)
    fi
}

# Interactive console loop for Pterodactyl Console stdin
run_interactive_console() {
    vnh_log_info "Vietnam Hosting Linux Container Ready. Type commands in Pterodactyl Console or connect via SSH/SFTP."
    printf 'VIETNAM HOSTING CONTAINER READY\n'
    while IFS= read -r cmd; do
        [[ -z "$cmd" ]] && continue
        case "$cmd" in
            exit|quit|shutdown)
                cleanup
                ;;
            *)
                /bin/bash -c "$cmd" || true
                ;;
        esac
    done
    # Keep container alive if stdin closes while services are running
    wait
}

setup_nss_wrapper
print_linux_info
start_unprivileged_ssh
start_userspace_scheduler
run_user_startup_script
run_interactive_console
