#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Unprivileged PRoot Writable RootFS Login Shell
# Website: https://vietnam-hosting.net
# License: MIT
#
# Provides a full writable Linux rootfs (`uid=0(root)` virtual environment for
# apt/dpkg/dnf/apk package installation inside /home/container/rootfs) while
# keeping the container 100% unprivileged under Pterodactyl Wings on the host.
# ==============================================================================

set -uo pipefail

HOME_DIR="/home/container"
ROOTFS_DIR="${HOME_DIR}/rootfs"

export TERM="${TERM:-xterm-256color}"
export LANG="C.UTF-8"
export LC_ALL="C.UTF-8"

if [[ "${ENABLE_PROOT:-1}" == "1" ]] && command -v proot >/dev/null 2>&1 && [[ -d "${ROOTFS_DIR}/bin" || -L "${ROOTFS_DIR}/bin" ]]; then
    mkdir -p "${HOME_DIR}/tmp"
    cp -f /etc/resolv.conf "${ROOTFS_DIR}/etc/resolv.conf" 2>/dev/null || true

    # Refresh live cgroup-scoped /proc metrics before spawning interactive shell
    if [[ -r /opt/vnh/proc-limits.sh ]]; then
        # shellcheck source=proc-limits.sh
        source /opt/vnh/proc-limits.sh
        vnh_refresh_proc_dynamic 2>/dev/null || true
    fi

    # Preserve container /etc/hosts entries if missing
    if [[ ! -s "${ROOTFS_DIR}/etc/hosts" ]]; then
        printf '127.0.0.1 localhost vietnam-hosting\n::1 localhost ip6-localhost ip6-loopback\n' > "${ROOTFS_DIR}/etc/hosts" 2>/dev/null || true
    fi

    export TMPDIR="${HOME_DIR}/tmp"
    export PROOT_NO_SECCOMP=1
    export HOME="/root"
    export USER="root"
    export SHELL="/bin/bash"
    export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    BIND_ARGS=(-b /dev -b /proc -b /sys)
    PROC_DIR="${HOME_DIR}/run/proc"
    [[ -r "${PROC_DIR}/meminfo" ]] && BIND_ARGS+=(-b "${PROC_DIR}/meminfo:/proc/meminfo")
    [[ -r "${PROC_DIR}/cpuinfo" ]] && BIND_ARGS+=(-b "${PROC_DIR}/cpuinfo:/proc/cpuinfo")
    [[ -r "${PROC_DIR}/stat" ]] && BIND_ARGS+=(-b "${PROC_DIR}/stat:/proc/stat")
    [[ -r "${PROC_DIR}/uptime" ]] && BIND_ARGS+=(-b "${PROC_DIR}/uptime:/proc/uptime")
    [[ -r "${PROC_DIR}/cpu_online" && -r /sys/devices/system/cpu/online ]] && BIND_ARGS+=(-b "${PROC_DIR}/cpu_online:/sys/devices/system/cpu/online")
    [[ -r "${PROC_DIR}/product_name" && -r /sys/devices/virtual/dmi/id/product_name ]] && BIND_ARGS+=(-b "${PROC_DIR}/product_name:/sys/devices/virtual/dmi/id/product_name")
    [[ -r "${PROC_DIR}/product_version" && -r /sys/devices/virtual/dmi/id/product_version ]] && BIND_ARGS+=(-b "${PROC_DIR}/product_version:/sys/devices/virtual/dmi/id/product_version")
    [[ -f "${HOME_DIR}/readme.md" ]] && BIND_ARGS+=(-b "${HOME_DIR}/readme.md:/root/readme.md")
    [[ -f "${HOME_DIR}/startup.sh" ]] && BIND_ARGS+=(-b "${HOME_DIR}/startup.sh:/root/startup.sh")
    [[ -f "${HOME_DIR}/crontab" ]] && BIND_ARGS+=(-b "${HOME_DIR}/crontab:/root/crontab")
    [[ -d "${HOME_DIR}/scripts" ]] && BIND_ARGS+=(-b "${HOME_DIR}/scripts:/root/scripts")
    BIND_ARGS+=(-b "${HOME_DIR}:/mnt/container")

    if (( $# > 0 )); then
        exec proot -0 -r "${ROOTFS_DIR}" "${BIND_ARGS[@]}" -w /root /bin/bash "$@"
    else
        exec proot -0 -r "${ROOTFS_DIR}" "${BIND_ARGS[@]}" -w /root /bin/bash -l
    fi
fi

# Graceful fallback when PRoot is disabled or unavailable on the distro
export HOME="${HOME_DIR}"
cd "${HOME_DIR}" || true
if (( $# > 0 )); then
    exec /bin/bash "$@"
else
    exec /bin/bash -l
fi
