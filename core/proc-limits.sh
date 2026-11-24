#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Container-Scoped /proc Resource Virtualization Library
# Website: https://vietnam-hosting.net
# License: MIT
#
# Generates live cgroup-accurate /proc/meminfo, /proc/cpuinfo, /proc/stat, and
# /proc/uptime files inside /home/container/run/proc/ so tools inside PRoot
# (neofetch, free, htop, top, uptime, nproc) display ONLY the exact RAM, vCPU
# cores, and uptime allocated to this Pterodactyl container — never leaking
# the physical Node's hardware totals.
# ==============================================================================

set -uo pipefail

VNH_PROC_HOME="${HOME:-/home/container}"
VNH_PROC_DIR="${VNH_PROC_HOME}/run/proc"
VNH_LIMITS_ENV="${VNH_PROC_HOME}/run/limits.env"

_vnh_detect_alloc_mem_kb() {
    # Prefer Pterodactyl's exact SERVER_MEMORY (MiB) so UI & container match 1:1
    if [[ -n "${SERVER_MEMORY:-}" ]] && [[ "${SERVER_MEMORY}" =~ ^[0-9]+$ ]] && (( SERVER_MEMORY > 0 )); then
        printf '%s' $(( SERVER_MEMORY * 1024 ))
        return 0
    fi
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        local raw
        raw="$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true)"
        if [[ "$raw" =~ ^[0-9]+$ ]] && (( raw > 0 && raw < 9000000000000000000 )); then
            printf '%s' $(( raw / 1024 ))
            return 0
        fi
    fi
    if [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        local raw
        raw="$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || true)"
        if [[ "$raw" =~ ^[0-9]+$ ]] && (( raw > 0 && raw < 9000000000000000000 )); then
            printf '%s' $(( raw / 1024 ))
            return 0
        fi
    fi
    awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || printf '524288'
}

_vnh_detect_alloc_swap_kb() {
    if [[ -r /sys/fs/cgroup/memory.swap.max ]]; then
        local raw
        raw="$(cat /sys/fs/cgroup/memory.swap.max 2>/dev/null || true)"
        if [[ "$raw" == "0" ]]; then
            printf '0'
            return 0
        elif [[ "$raw" =~ ^[0-9]+$ ]] && (( raw < 9000000000000000000 )); then
            printf '%s' $(( raw / 1024 ))
            return 0
        fi
    fi
    printf '0'
}

_vnh_detect_alloc_cpus() {
    local host_cpus=1
    host_cpus="$(grep -c '^processor[[:space:]]*:' /proc/cpuinfo 2>/dev/null || printf '1')"
    (( host_cpus < 1 )) && host_cpus=1

    # cgroup v2: cpu.max -> "<quota> <period>"
    if [[ -r /sys/fs/cgroup/cpu.max ]]; then
        local quota period
        read -r quota period < /sys/fs/cgroup/cpu.max 2>/dev/null || true
        if [[ "${quota:-}" =~ ^[0-9]+$ ]] && [[ "${period:-}" =~ ^[0-9]+$ ]] && (( period > 0 )); then
            local cg_cpus=$(( (quota + period - 1) / period ))
            (( cg_cpus < 1 )) && cg_cpus=1
            (( cg_cpus > host_cpus )) && cg_cpus="$host_cpus"
            printf '%s' "$cg_cpus"
            return 0
        fi
    elif [[ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]] && [[ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]]; then
        local quota period
        quota="$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || printf '-1')"
        period="$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || printf '100000')"
        if [[ "$quota" =~ ^[0-9]+$ ]] && (( quota > 0 && period > 0 )); then
            local cg_cpus=$(( (quota + period - 1) / period ))
            (( cg_cpus < 1 )) && cg_cpus=1
            (( cg_cpus > host_cpus )) && cg_cpus="$host_cpus"
            printf '%s' "$cg_cpus"
            return 0
        fi
    fi
    printf '%s' "$host_cpus"
}

vnh_init_proc_limits() {
    mkdir -p "${VNH_PROC_DIR}"
    local mem_kb swap_kb cpus boot_epoch
    mem_kb="$(_vnh_detect_alloc_mem_kb)"
    swap_kb="$(_vnh_detect_alloc_swap_kb)"
    cpus="$(_vnh_detect_alloc_cpus)"
    boot_epoch="$(date +%s)"

    cat > "${VNH_LIMITS_ENV}" <<EOF
VNH_MEM_LIMIT_KB=${mem_kb}
VNH_SWAP_LIMIT_KB=${swap_kb}
VNH_CPU_LIMIT=${cpus}
VNH_BOOT_EPOCH=${boot_epoch}
EOF
    chmod 644 "${VNH_LIMITS_ENV}"

    # Build container-scoped /proc/cpuinfo with exactly ${cpus} processor block(s)
    local tmp_cpu="${VNH_PROC_DIR}/cpuinfo.tmp.$$"
    awk -v limit="$cpus" '
        BEGIN { count = 0; keep = 1 }
        /^processor[[:space:]]*:/ {
            if (count >= limit) { keep = 0; next }
            keep = 1
            print "processor\t: " count
            count++
            next
        }
        keep == 1 {
            if ($0 ~ /^siblings[[:space:]]*:/) {
                print "siblings\t: " limit
            } else if ($0 ~ /^cpu cores[[:space:]]*:/) {
                print "cpu cores\t: " limit
            } else {
                print $0
            }
        }
    ' /proc/cpuinfo > "$tmp_cpu" 2>/dev/null || true
    if [[ -s "$tmp_cpu" ]]; then
        mv -f "$tmp_cpu" "${VNH_PROC_DIR}/cpuinfo"
    else
        rm -f "$tmp_cpu"
    fi

    # Build /sys/devices/system/cpu/online mask (e.g., "0" for 1 vCPU, "0-1" for 2 vCPUs)
    if (( cpus <= 1 )); then
        printf '0\n' > "${VNH_PROC_DIR}/cpu_online"
    else
        printf '0-%s\n' $(( cpus - 1 )) > "${VNH_PROC_DIR}/cpu_online"
    fi

    # Clean container product name (avoids leaking physical Node hypervisor model in neofetch)
    printf 'Vietnam Hosting NAT Container\n' > "${VNH_PROC_DIR}/product_name"
    printf '\n' > "${VNH_PROC_DIR}/product_version"

    vnh_refresh_proc_dynamic
}

vnh_refresh_proc_dynamic() {
    mkdir -p "${VNH_PROC_DIR}"
    if [[ -r "${VNH_LIMITS_ENV}" ]]; then
        # shellcheck source=/dev/null
        source "${VNH_LIMITS_ENV}"
    fi

    local mem_total_kb="${VNH_MEM_LIMIT_KB:-524288}"
    local swap_total_kb="${VNH_SWAP_LIMIT_KB:-0}"
    local cpus="${VNH_CPU_LIMIT:-1}"
    local boot_epoch="${VNH_BOOT_EPOCH:-$(date +%s)}"

    # Read live cgroup v2 (or v1) memory usage
    local current_bytes=0 file_bytes=0 anon_bytes=0 slab_bytes=0 swap_cur_bytes=0
    if [[ -r /sys/fs/cgroup/memory.current ]]; then
        current_bytes="$(cat /sys/fs/cgroup/memory.current 2>/dev/null || printf '0')"
        if [[ -r /sys/fs/cgroup/memory.stat ]]; then
            file_bytes="$(awk '$1 == "file" {print $2; exit}' /sys/fs/cgroup/memory.stat 2>/dev/null || printf '0')"
            anon_bytes="$(awk '$1 == "anon" {print $2; exit}' /sys/fs/cgroup/memory.stat 2>/dev/null || printf '0')"
            slab_bytes="$(awk '$1 == "slab" {print $2; exit}' /sys/fs/cgroup/memory.stat 2>/dev/null || printf '0')"
        fi
        if [[ -r /sys/fs/cgroup/memory.swap.current ]]; then
            swap_cur_bytes="$(cat /sys/fs/cgroup/memory.swap.current 2>/dev/null || printf '0')"
        fi
    elif [[ -r /sys/fs/cgroup/memory/memory.usage_in_bytes ]]; then
        current_bytes="$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || printf '0')"
    fi

    [[ "$current_bytes" =~ ^[0-9]+$ ]] || current_bytes=0
    [[ "$file_bytes" =~ ^[0-9]+$ ]] || file_bytes=0
    [[ "$anon_bytes" =~ ^[0-9]+$ ]] || anon_bytes=0
    [[ "$slab_bytes" =~ ^[0-9]+$ ]] || slab_bytes=0
    [[ "$swap_cur_bytes" =~ ^[0-9]+$ ]] || swap_cur_bytes=0

    local used_kb=$(( current_bytes / 1024 ))
    local cached_kb=$(( file_bytes / 1024 ))
    local slab_kb=$(( slab_bytes / 1024 ))
    local active_kb=$(( anon_bytes / 1024 ))
    local swap_used_kb=$(( swap_cur_bytes / 1024 ))

    (( used_kb > mem_total_kb )) && used_kb="$mem_total_kb"
    (( cached_kb > used_kb )) && cached_kb="$used_kb"
    (( swap_used_kb > swap_total_kb )) && swap_used_kb="$swap_total_kb"

    local mem_free_kb=$(( mem_total_kb - used_kb ))
    (( mem_free_kb < 0 )) && mem_free_kb=0
    local mem_avail_kb=$(( mem_free_kb + cached_kb ))
    (( mem_avail_kb > mem_total_kb )) && mem_avail_kb="$mem_total_kb"
    local swap_free_kb=$(( swap_total_kb - swap_used_kb ))
    (( swap_free_kb < 0 )) && swap_free_kb=0

    # Atomic /proc/meminfo
    local tmp_mem="${VNH_PROC_DIR}/meminfo.tmp.$$"
    cat > "$tmp_mem" <<EOF
MemTotal:       ${mem_total_kb} kB
MemFree:        ${mem_free_kb} kB
MemAvailable:   ${mem_avail_kb} kB
Buffers:               0 kB
Cached:         ${cached_kb} kB
SwapCached:            0 kB
Active:         ${active_kb} kB
Inactive:       ${cached_kb} kB
SwapTotal:      ${swap_total_kb} kB
SwapFree:       ${swap_free_kb} kB
Dirty:                 0 kB
Writeback:             0 kB
AnonPages:      ${active_kb} kB
Mapped:         ${cached_kb} kB
Shmem:                 0 kB
KReclaimable:   ${slab_kb} kB
Slab:           ${slab_kb} kB
SReclaimable:   ${slab_kb} kB
SUnreclaim:            0 kB
EOF
    mv -f "$tmp_mem" "${VNH_PROC_DIR}/meminfo"

    # Atomic /proc/stat trimmed to allocated cpu0..cpu{N-1}
    local tmp_stat="${VNH_PROC_DIR}/stat.tmp.$$"
    awk -v limit="$cpus" '
        /^cpu[0-9]+[[:space:]]/ {
            idx = substr($1, 4) + 0
            if (idx >= limit) next
        }
        { print }
    ' /proc/stat > "$tmp_stat" 2>/dev/null || true
    if [[ -s "$tmp_stat" ]]; then
        mv -f "$tmp_stat" "${VNH_PROC_DIR}/stat"
    else
        rm -f "$tmp_stat"
    fi

    # Atomic container-scoped /proc/uptime
    local now up_sec idle_sec tmp_up
    now="$(date +%s)"
    up_sec=$(( now - boot_epoch ))
    (( up_sec < 1 )) && up_sec=1
    idle_sec=$(( up_sec * cpus ))
    tmp_up="${VNH_PROC_DIR}/uptime.tmp.$$"
    printf '%s.00 %s.00\n' "$up_sec" "$idle_sec" > "$tmp_up"
    mv -f "$tmp_up" "${VNH_PROC_DIR}/uptime"
}
