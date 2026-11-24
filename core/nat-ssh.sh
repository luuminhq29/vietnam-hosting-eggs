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
#   - Unprivileged execution ONLY (non-root container UID; never root on host)
#   - No privileged mode, no CAP_SYS_ADMIN, no Docker socket, no host network
#   - No systemd required; uses lightweight signal-aware process supervision
#   - Never modifies host iptables/nftables/routing
#   - Generates persistent per-container SSH host keys under /home/container/.ssh
#   - Disables root SSH login permanently (-w -g / PermitRootLogin no)
#   - Supports BOTH SSH Public Key Auth AND live password sync from
#     /home/container/readme.md (default user: ubuntu, default pass: vietnam999)
#     via unprivileged libnss-wrapper without requiring /etc/shadow or root.
# ==============================================================================

set -euo pipefail

VNH_CORE_DIR="${VNH_CORE_DIR:-/opt/vnh}"
if [[ -r "${VNH_CORE_DIR}/environment.sh" ]]; then
    # shellcheck source=environment.sh
    source "${VNH_CORE_DIR}/environment.sh"
fi
if [[ -r "${VNH_CORE_DIR}/proc-limits.sh" ]]; then
    # shellcheck source=proc-limits.sh
    source "${VNH_CORE_DIR}/proc-limits.sh"
fi

HOME_DIR="${HOME:-/home/container}"
ROOTFS_DIR="${HOME_DIR}/rootfs"
SSH_DIR="${HOME_DIR}/.ssh"
HOSTKEY_DIR="${SSH_DIR}/host_keys"
README_CRED_FILE="${HOME_DIR}/readme.md"
SSH_PORT="${SSH_PORT:-${SERVER_PORT:-}}"
ENABLE_SSH="${ENABLE_SSH:-1}"
ENABLE_SSH_PASSWORD="${ENABLE_SSH_PASSWORD:-1}"
AUTO_RANDOM_SSH_PASSWORD="${AUTO_RANDOM_SSH_PASSWORD:-0}"
ENABLE_PROOT="${ENABLE_PROOT:-1}"
ENABLE_CRON="${ENABLE_CRON:-1}"
SSH_AUTHORIZED_KEYS="${SSH_AUTHORIZED_KEYS:-}"
STARTUP_SCRIPT="${STARTUP_SCRIPT:-startup.sh}"
CURRENT_SSH_USER="ubuntu"
VPS_SHELL="/opt/vnh/vps-shell.sh"

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

# Seed persistent writable rootfs inside /home/container/rootfs once for unprivileged PRoot VPS mode.
ensure_proot_rootfs() {
    if [[ "${ENABLE_PROOT}" != "1" ]] && [[ "${ENABLE_PROOT}" != "true" ]]; then
        return 0
    fi
    if ! command -v proot >/dev/null 2>&1; then
        vnh_log_warn "proot binary not available in this image; running standard user-space shell."
        return 0
    fi

    if [[ ! -f "${ROOTFS_DIR}/.vnh_rootfs_ready" ]]; then
        vnh_log_info "Initializing persistent writable Linux rootfs at ${ROOTFS_DIR} (first boot only)..."
        mkdir -p "${ROOTFS_DIR}" "${HOME_DIR}/tmp"
        # Copy container OS files into persistent writable volume (ignores root-only files like /etc/shadow cleanly)
        tar --one-file-system \
            --exclude='./proc' \
            --exclude='./sys' \
            --exclude='./dev' \
            --exclude='./tmp' \
            --exclude='./run' \
            --exclude='./mnt' \
            --exclude='./media' \
            --exclude='./home/container' \
            --exclude='./opt/vnh' \
            --ignore-failed-read \
            --warning=no-file-ignored \
            -C / -cf - . 2>/dev/null | tar --no-same-owner -C "${ROOTFS_DIR}" -xf - 2>/dev/null || true

        mkdir -p \
            "${ROOTFS_DIR}/dev" \
            "${ROOTFS_DIR}/proc" \
            "${ROOTFS_DIR}/sys" \
            "${ROOTFS_DIR}/tmp" \
            "${ROOTFS_DIR}/run" \
            "${ROOTFS_DIR}/root" \
            "${ROOTFS_DIR}/mnt/container" \
            "${ROOTFS_DIR}/var/lib/apt/lists/partial" \
            "${ROOTFS_DIR}/var/cache/apt/archives/partial" \
            "${ROOTFS_DIR}/var/log/apt" \
            "${ROOTFS_DIR}/etc/apt/apt.conf.d"
        chmod 1777 "${ROOTFS_DIR}/tmp" 2>/dev/null || true

        # Ensure root user entries and clean apt configuration inside writable rootfs
        printf 'root:x:0:0:root:/root:/bin/bash\n' > "${ROOTFS_DIR}/etc/passwd.vnh"
        grep -v '^root:' "${ROOTFS_DIR}/etc/passwd" >> "${ROOTFS_DIR}/etc/passwd.vnh" 2>/dev/null || true
        mv -f "${ROOTFS_DIR}/etc/passwd.vnh" "${ROOTFS_DIR}/etc/passwd"
        chmod 644 "${ROOTFS_DIR}/etc/passwd"

        printf 'root:*:19000:0:99999:7:::\n' > "${ROOTFS_DIR}/etc/shadow"
        chmod 600 "${ROOTFS_DIR}/etc/shadow"

        # Prevent apt from attempting setgroups/_apt drop-privs errors inside PRoot
        cat > "${ROOTFS_DIR}/etc/apt/apt.conf.d/99vnh-proot" <<'EOF'
APT::Sandbox::User "root";
Acquire::AllowInsecureRepositories "false";
EOF

        # Clean interactive root prompt & helpful paths
        cat > "${ROOTFS_DIR}/root/.bashrc" <<'EOF'
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export LANG=C.UTF-8
export TERM="${TERM:-xterm-256color}"
export PS1='\[\033[01;32m\]root@vietnam-hosting\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]# '
alias ll='ls -alF --color=auto'
alias ls='ls --color=auto'
EOF
        cat > "${ROOTFS_DIR}/root/.profile" <<'EOF'
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
EOF
        # Provide lightweight sudo passthrough if real sudo is not installed (user is already virtual uid=0)
        if [[ ! -x "${ROOTFS_DIR}/usr/bin/sudo" ]] && [[ ! -x "${ROOTFS_DIR}/usr/local/bin/sudo" ]]; then
            mkdir -p "${ROOTFS_DIR}/usr/local/bin"
            printf '#!/bin/sh\nexec "$@"\n' > "${ROOTFS_DIR}/usr/local/bin/sudo"
            chmod 755 "${ROOTFS_DIR}/usr/local/bin/sudo"
        fi

        # Provide container-quota-accurate nproc wrapper reading virtualized /proc/cpuinfo
        mkdir -p "${ROOTFS_DIR}/usr/local/bin"
        cat > "${ROOTFS_DIR}/usr/local/bin/nproc" <<'EOF'
#!/bin/sh
grep -c '^processor[[:space:]]*:' /proc/cpuinfo 2>/dev/null || echo 1
EOF
        chmod 755 "${ROOTFS_DIR}/usr/local/bin/nproc"

        cp -f /etc/resolv.conf "${ROOTFS_DIR}/etc/resolv.conf" 2>/dev/null || true
        date -u +%Y-%m-%dT%H:%M:%SZ > "${ROOTFS_DIR}/.vnh_rootfs_ready"
        vnh_log_info "Persistent writable rootfs ready! Full 'apt update && apt install' is now available."
    fi

    # Ensure existing rootfs also receives quota-accurate nproc wrapper on image upgrade
    if [[ -d "${ROOTFS_DIR}/usr" ]] && [[ ! -x "${ROOTFS_DIR}/usr/local/bin/nproc" ]]; then
        mkdir -p "${ROOTFS_DIR}/usr/local/bin"
        cat > "${ROOTFS_DIR}/usr/local/bin/nproc" <<'EOF'
#!/bin/sh
grep -c '^processor[[:space:]]*:' /proc/cpuinfo 2>/dev/null || echo 1
EOF
        chmod 755 "${ROOTFS_DIR}/usr/local/bin/nproc"
    fi
}

ensure_readme_credentials() {
    if [[ ! -f "${README_CRED_FILE}" ]]; then
        local init_pass="vietnam999"
        if [[ "${AUTO_RANDOM_SSH_PASSWORD}" == "1" ]] || [[ "${AUTO_RANDOM_SSH_PASSWORD}" == "true" ]]; then
            if command -v openssl >/dev/null 2>&1; then
                init_pass="Vnh$(openssl rand -hex 7)"
            else
                init_pass="Vnh$(od -An -tx1 -N7 /dev/urandom | tr -d ' \n')"
            fi
        fi
        cat > "${README_CRED_FILE}" <<EOF
# Vietnam Hosting — NAT Linux Container SSH Access

Thông tin đăng nhập SSH NAT (kết nối: \`ssh -p <PORT> ubuntu@<NODE_IP>\`):

SSH_USER: ubuntu
PASSWORD: ${init_pass}

> Hướng dẫn đổi mật khẩu NAT SSH:
> - Sửa trực tiếp giá trị sau \`PASSWORD:\` ở trên rồi lưu file \`readme.md\`.
> - Hệ thống tự động đồng bộ mật khẩu SSH NAT mới trong vòng 2 giây (không cần restart server).
> - Khuyến nghị đổi ngay mật khẩu mặc định hoặc thêm SSH Public Key vào \`~/.ssh/authorized_keys\`.
> - Đăng nhập \`root\` qua SSH luôn bị chặn vì lý do bảo mật container.
EOF
        chmod 600 "${README_CRED_FILE}" 2>/dev/null || true
        vnh_log_info "Initialized NAT SSH credentials file at ${README_CRED_FILE}."
    fi
}

# Parse SSH_USER and PASSWORD from /home/container/readme.md without logging secrets.
parse_readme_field() {
    local field_regex="$1"
    local default_val="$2"
    local val=""
    if [[ -r "${README_CRED_FILE}" ]]; then
        val="$(grep -iE "^[[:space:]]*(${field_regex})[[:space:]]*[:=]" "${README_CRED_FILE}" 2>/dev/null | head -n1 | sed -E 's/^[^:=]+[:=][[:space:]]*//; s/\r$//; s/[[:space:]]+$//' || true)"
    fi
    if [[ -z "$val" ]]; then
        printf '%s' "$default_val"
    else
        printf '%s' "$val"
    fi
}

hash_ssh_password() {
    local raw_pass="$1"
    if command -v openssl >/dev/null 2>&1; then
        openssl passwd -6 -stdin <<< "$raw_pass" 2>/dev/null && return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        VNH_RAW_PW="$raw_pass" python3 -c 'import crypt, os; print(crypt.crypt(os.environ["VNH_RAW_PW"], crypt.mksalt(crypt.METHOD_SHA512)))' 2>/dev/null && return 0
    fi
    printf '*'
}

# Build unprivileged nss_wrapper passwd/group files synced from readme.md.
sync_nss_passwd_from_readme() {
    local cur_uid cur_gid lib_nss ssh_user ssh_pass pass_hash tmp_pw tmp_gr
    cur_uid="$(id -u)"
    cur_gid="$(id -g)"

    ssh_user="$(parse_readme_field 'SSH_USER|USER|USERNAME' 'ubuntu')"
    # Strip trailing '@' if user wrote 'ubuntu@'
    ssh_user="${ssh_user%@}"
    # Validate safe POSIX username and strictly forbid root
    if [[ ! "$ssh_user" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]] || [[ "$ssh_user" == "root" ]]; then
        vnh_log_warn "Invalid or forbidden SSH_USER in readme.md; falling back to 'ubuntu'."
        ssh_user="ubuntu"
    fi
    CURRENT_SSH_USER="$ssh_user"

    if [[ "${ENABLE_SSH_PASSWORD}" == "1" ]] || [[ "${ENABLE_SSH_PASSWORD}" == "true" ]]; then
        ssh_pass="$(parse_readme_field 'PASSWORD|PASS|SSH_PASSWORD|SSH_PASS' 'vietnam999')"
        pass_hash="$(hash_ssh_password "$ssh_pass")"
    else
        pass_hash="*"
    fi

    mkdir -p "${HOME_DIR}/run"
    tmp_pw="${HOME_DIR}/run/passwd.tmp.$$"
    tmp_gr="${HOME_DIR}/run/group.tmp.$$"

    local login_shell="/bin/bash"
    if [[ "${ENABLE_PROOT}" == "1" || "${ENABLE_PROOT}" == "true" ]] \
        && [[ -x "${VPS_SHELL}" ]] \
        && grep -Fqx "${VPS_SHELL}" /etc/shells 2>/dev/null; then
        login_shell="${VPS_SHELL}"
    fi

    # Put the active NAT SSH user first so getpwuid() and getpwnam() resolve cleanly
    printf '%s:%s:%s:%s:Vietnam Hosting NAT User:%s:%s\n' \
        "$ssh_user" "$pass_hash" "$cur_uid" "$cur_gid" "$HOME_DIR" "$login_shell" > "$tmp_pw"
    if [[ "$ssh_user" != "container" ]]; then
        printf 'container:*:%s:%s:Vietnam Hosting Container:%s:%s\n' \
            "$cur_uid" "$cur_gid" "$HOME_DIR" "$login_shell" >> "$tmp_pw"
    fi
    grep -vE "^(${ssh_user}|container):" /etc/passwd >> "$tmp_pw" 2>/dev/null || true
    chmod 600 "$tmp_pw"
    mv -f "$tmp_pw" "${HOME_DIR}/run/passwd"

    printf '%s:x:%s:\n' "$ssh_user" "$cur_gid" > "$tmp_gr"
    if [[ "$ssh_user" != "container" ]]; then
        printf 'container:x:%s:\n' "$cur_gid" >> "$tmp_gr"
    fi
    grep -vE "^(${ssh_user}|container):" /etc/group >> "$tmp_gr" 2>/dev/null || true
    chmod 644 "$tmp_gr"
    mv -f "$tmp_gr" "${HOME_DIR}/run/group"

    lib_nss="$(find /usr/lib /lib -name 'libnss_wrapper.so*' 2>/dev/null | head -n1 || true)"
    if [[ -n "$lib_nss" ]]; then
        export LD_PRELOAD="${lib_nss}"
        export NSS_WRAPPER_PASSWD="${HOME_DIR}/run/passwd"
        export NSS_WRAPPER_GROUP="${HOME_DIR}/run/group"
    fi
}

# Watch /home/container/readme.md for edits and live-update NAT SSH password hash immediately.
start_readme_password_watcher() {
    if [[ "$ENABLE_SSH" != "1" ]] && [[ "$ENABLE_SSH" != "true" ]]; then
        return 0
    fi
    (
        local last_hash=""
        if [[ -r "${README_CRED_FILE}" ]]; then
            last_hash="$(sha256sum "${README_CRED_FILE}" 2>/dev/null | awk '{print $1}' || true)"
        fi
        while true; do
            sleep 2
            if declare -F vnh_refresh_proc_dynamic >/dev/null 2>&1; then
                vnh_refresh_proc_dynamic
            fi
            if [[ -r "${README_CRED_FILE}" ]]; then
                local cur_hash
                cur_hash="$(sha256sum "${README_CRED_FILE}" 2>/dev/null | awk '{print $1}' || true)"
                if [[ -n "$cur_hash" ]] && [[ "$cur_hash" != "$last_hash" ]]; then
                    last_hash="$cur_hash"
                    sync_nss_passwd_from_readme
                    vnh_log_info "Detected change in readme.md — updated NAT SSH password for user '${CURRENT_SSH_USER}' (no restart required)."
                fi
            fi
        done
    ) &
    CHILD_PIDS+=($!)
}

print_linux_info() {
    local os_pretty kernel arch mem_mb cpus user_name
    os_pretty="$(vnh_detect_os)"
    kernel="$(uname -r)"
    arch="$(vnh_detect_arch)"
    mem_mb="$(vnh_detect_memory_mb)"
    cpus="$(vnh_detect_cpu_limit)"
    user_name="$(whoami 2>/dev/null || printf '%s' "${CURRENT_SSH_USER}")"

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
    printf 'SSH Login User:    %s@<NODE_IP> (credentials managed in /home/container/readme.md)\n' "${CURRENT_SSH_USER}"
    printf 'User Context:      %s (uid=%s, unprivileged container)\n' "$user_name" "$(id -u)"
    printf 'Notice:            Container runtime (not KVM VPS). Use user-space\n'
    printf '                   package managers (pip/npm/cargo/brew/nix/mise)\n'
    printf '                   under %s. System-wide root/systemd requires KVM.\n' "$HOME_DIR"
    printf '==============================================================\n'
}

setup_ssh_keys() {
    mkdir -p "$SSH_DIR" "$HOSTKEY_DIR" "${HOME_DIR}/run"
    chmod 700 "$SSH_DIR" "$HOSTKEY_DIR"

    local auth_file="${SSH_DIR}/authorized_keys"
    touch "$auth_file"
    chmod 600 "$auth_file"

    if [[ -n "$SSH_AUTHORIZED_KEYS" ]]; then
        if ! grep -Fqx "$SSH_AUTHORIZED_KEYS" "$auth_file" 2>/dev/null; then
            printf '%s\n' "$SSH_AUTHORIZED_KEYS" >> "$auth_file"
            vnh_log_info "Registered SSH public key from SSH_AUTHORIZED_KEYS."
        fi
    fi

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

    if command -v dropbear >/dev/null 2>&1; then
        local db_flags=(-F -E -g -w)
        if [[ "${ENABLE_SSH_PASSWORD}" != "1" ]] && [[ "${ENABLE_SSH_PASSWORD}" != "true" ]]; then
            db_flags+=(-s)
            vnh_log_info "Starting unprivileged Dropbear SSH daemon on 0.0.0.0:${SSH_PORT} (pubkey-only, root login disabled)..."
        else
            vnh_log_info "Starting unprivileged Dropbear SSH daemon on 0.0.0.0:${SSH_PORT} (user '${CURRENT_SSH_USER}', readme.md password + pubkey, root disabled)..."
        fi
        dropbear "${db_flags[@]}" \
            -p "0.0.0.0:${SSH_PORT}" \
            -r "${HOSTKEY_DIR}/dropbear_ed25519_host_key" \
            -P "${HOME_DIR}/run/dropbear.pid" &
        CHILD_PIDS+=($!)
        return 0
    fi

    if command -v sshd >/dev/null 2>&1 && [[ -f "${HOSTKEY_DIR}/ssh_host_ed25519_key" ]]; then
        local sshd_bin sshd_cfg pw_auth
        sshd_bin="$(command -v sshd)"
        sshd_cfg="${SSH_DIR}/sshd_config"
        pw_auth="no"
        if [[ "${ENABLE_SSH_PASSWORD}" == "1" ]] || [[ "${ENABLE_SSH_PASSWORD}" == "true" ]]; then
            pw_auth="yes"
        fi
        cat > "$sshd_cfg" <<EOF
Port ${SSH_PORT}
ListenAddress 0.0.0.0
HostKey ${HOSTKEY_DIR}/ssh_host_ed25519_key
PidFile ${HOME_DIR}/run/sshd.pid
AuthorizedKeysFile ${SSH_DIR}/authorized_keys
PermitRootLogin no
PasswordAuthentication ${pw_auth}
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
UsePAM no
PrintMotd no
Subsystem sftp internal-sftp
StrictModes no
EOF
        vnh_log_info "Starting unprivileged OpenSSH daemon on 0.0.0.0:${SSH_PORT} (root login disabled)..."
        "$sshd_bin" -D -e -f "$sshd_cfg" &
        CHILD_PIDS+=($!)
        return 0
    fi

    vnh_log_warn "Neither dropbear nor sshd available in this image; use Pterodactyl Console and Wings SFTP."
    return 0
}

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
                if [[ -x "${VPS_SHELL}" ]]; then
                    "${VPS_SHELL}" -c "$cmd" || true
                else
                    /bin/bash -c "$cmd" || true
                fi
                ;;
        esac
    done
    wait
}

if declare -F vnh_init_proc_limits >/dev/null 2>&1; then
    vnh_init_proc_limits
fi
ensure_proot_rootfs
ensure_readme_credentials
sync_nss_passwd_from_readme
print_linux_info
start_unprivileged_ssh
start_readme_password_watcher
start_userspace_scheduler
run_user_startup_script
run_interactive_console
