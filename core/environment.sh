#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Universal Environment & Security Helper Library
# Website: https://vietnam-hosting.net
# License: MIT
#
# Provides safe logging with automatic secret redaction, cgroup resource
# detection, environment variable validation, JVM heap calculation, and
# build concurrency throttling. Designed for unprivileged Pterodactyl containers.
# ==============================================================================

set -euo pipefail

# Redact sensitive substrings (tokens, passwords, credentials in URLs) before logging.
vnh_redact() {
    local input="${1:-}"
    # Mask basic-auth credentials in URLs: https://user:token@host -> https://***@host
    input="$(printf '%s' "$input" | sed -E 's#(https?|ftp|postgres|postgresql|mysql|mongodb(\+srv)?|redis|amqp)://[^/@[:space:]]+@#\1://***@#g')"
    # Mask common key=value secret patterns
    input="$(printf '%s' "$input" | sed -E 's/((TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|ACCESS_KEY|PRIVATE_KEY|AUTH_TOKEN|BOT_TOKEN|CLIENT_SECRET)[[:space:]]*[:=][[:space:]]*)[^[:space:]"'"'"']+/\1[REDACTED]/gi')"
    printf '%s' "$input"
}

vnh_log_info() {
    local msg
    msg="$(vnh_redact "${1:-}")"
    printf '[VNH][INFO]  %s\n' "$msg"
}

vnh_log_warn() {
    local msg
    msg="$(vnh_redact "${1:-}")"
    printf '[VNH][WARN]  %s\n' "$msg" >&2
}

vnh_log_error() {
    local msg
    msg="$(vnh_redact "${1:-}")"
    printf '[VNH][ERROR] %s\n' "$msg" >&2
}

# Check whether an environment variable name is considered secret.
vnh_is_secret_var() {
    local name="${1:-}"
    case "$name" in
        *TOKEN*|*SECRET*|*PASSWORD*|*PASSWD*|*API_KEY*|*PRIVATE_KEY*|*AUTH*|*CREDENTIAL*|*ACCESS_KEY*|*DSN*|*COOKIE*|*SESSION_KEY*|*ENCRYPTION_KEY*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Validate that a relative path stays strictly inside /home/container (prevents path traversal).
vnh_validate_relpath() {
    local relpath="${1:-}"
    if [[ -z "$relpath" ]]; then
        vnh_log_error "Empty path is not allowed."
        return 1
    fi
    if [[ "$relpath" == /* ]] || [[ "$relpath" == *".."* ]] || [[ "$relpath" == *$'\n'* ]] || [[ "$relpath" == *$'\r'* ]]; then
        vnh_log_error "Unsafe path rejected: must be relative inside /home/container without '..'."
        return 1
    fi
    return 0
}

# Validate an integer within [min, max].
vnh_validate_int() {
    local val="${1:-}"
    local min="${2:-0}"
    local max="${3:-65535}"
    local label="${4:-value}"
    if ! [[ "$val" =~ ^[0-9]+$ ]]; then
        vnh_log_error "Invalid ${label}: expected integer, got '${val}'."
        return 1
    fi
    if (( val < min || val > max )); then
        vnh_log_error "Invalid ${label}: ${val} outside allowed range [${min}, ${max}]."
        return 1
    fi
    return 0
}

# Validate port number (1024-65535 for unprivileged containers, or 1-65535 if explicitly set).
vnh_validate_port() {
    local port="${1:-}"
    local label="${2:-SERVER_PORT}"
    vnh_validate_int "$port" 1 65535 "$label"
}

# Detect container memory limit in MiB using SERVER_MEMORY, cgroup v2, or cgroup v1.
vnh_detect_memory_mb() {
    if [[ -n "${SERVER_MEMORY:-}" ]] && [[ "${SERVER_MEMORY}" =~ ^[0-9]+$ ]] && (( SERVER_MEMORY > 0 )); then
        printf '%s' "${SERVER_MEMORY}"
        return 0
    fi

    # cgroup v2
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        local raw
        raw="$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true)"
        if [[ "$raw" =~ ^[0-9]+$ ]] && (( raw > 0 && raw < 9000000000000000000 )); then
            printf '%s' $(( raw / 1024 / 1024 ))
            return 0
        fi
    fi

    # cgroup v1
    if [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        local raw
        raw="$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || true)"
        if [[ "$raw" =~ ^[0-9]+$ ]] && (( raw > 0 && raw < 9000000000000000000 )); then
            printf '%s' $(( raw / 1024 / 1024 ))
            return 0
        fi
    fi

    printf 'Unknown'
    return 0
}

# Detect available CPU count respecting cgroup quotas to avoid starving shared nodes.
vnh_detect_cpu_limit() {
    local cpus=1
    if command -v nproc >/dev/null 2>&1; then
        cpus="$(nproc 2>/dev/null || printf '1')"
    fi

    # cgroup v2 cpu.max: "<quota> <period>"
    if [[ -r /sys/fs/cgroup/cpu.max ]]; then
        local quota period
        read -r quota period < /sys/fs/cgroup/cpu.max 2>/dev/null || true
        if [[ "${quota:-}" =~ ^[0-9]+$ ]] && [[ "${period:-}" =~ ^[0-9]+$ ]] && (( period > 0 )); then
            local cg_cpus=$(( (quota + period - 1) / period ))
            (( cg_cpus < 1 )) && cg_cpus=1
            if (( cg_cpus < cpus )); then
                cpus="$cg_cpus"
            fi
        fi
    elif [[ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ]] && [[ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]]; then
        local quota period
        quota="$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || printf '-1')"
        period="$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || printf '100000')"
        if [[ "$quota" =~ ^[0-9]+$ ]] && (( quota > 0 && period > 0 )); then
            local cg_cpus=$(( (quota + period - 1) / period ))
            (( cg_cpus < 1 )) && cg_cpus=1
            if (( cg_cpus < cpus )); then
                cpus="$cg_cpus"
            fi
        fi
    fi

    printf '%s' "$cpus"
}

# Compute safe compiler parallelism (CARGO_BUILD_JOBS / MAKEFLAGS / GOMAXPROCS) for shared hosting.
vnh_compute_build_jobs() {
    local requested="${VNH_BUILD_JOBS:-${BUILD_JOBS:-}}"
    local detected_cpus
    detected_cpus="$(vnh_detect_cpu_limit)"
    local mem_mb
    mem_mb="$(vnh_detect_memory_mb)"

    local max_jobs="$detected_cpus"
    # Cap jobs by available RAM (roughly 1 build job per 512 MiB to prevent OOM kills).
    if [[ "$mem_mb" =~ ^[0-9]+$ ]]; then
        local ram_jobs=$(( mem_mb / 512 ))
        (( ram_jobs < 1 )) && ram_jobs=1
        if (( ram_jobs < max_jobs )); then
            max_jobs="$ram_jobs"
        fi
    fi
    # Global shared-hosting safety cap unless explicitly overridden below detected_cpus.
    if (( max_jobs > 4 )); then
        max_jobs=4
    fi

    if [[ -n "$requested" ]] && [[ "$requested" =~ ^[0-9]+$ ]] && (( requested >= 1 )); then
        if (( requested < max_jobs )); then
            printf '%s' "$requested"
            return 0
        fi
    fi
    printf '%s' "$max_jobs"
}

# Compute JVM heap size in MiB leaving headroom for Metaspace, CodeCache, Direct Buffers, and OS overhead.
vnh_compute_jvm_heap_mb() {
    local mem_mb
    mem_mb="$(vnh_detect_memory_mb)"
    local overhead_mb="${JVM_OVERHEAD_MB:-256}"
    local heap_pct="${JVM_HEAP_PERCENT:-75}"

    if ! [[ "$mem_mb" =~ ^[0-9]+$ ]] || (( mem_mb <= 0 )); then
        printf '512'
        return 0
    fi
    if ! [[ "$overhead_mb" =~ ^[0-9]+$ ]]; then
        overhead_mb=256
    fi
    if ! [[ "$heap_pct" =~ ^[0-9]+$ ]] || (( heap_pct < 30 || heap_pct > 90 )); then
        heap_pct=75
    fi

    local by_pct=$(( mem_mb * heap_pct / 100 ))
    local by_overhead=$(( mem_mb - overhead_mb ))
    local heap_mb="$by_pct"
    if (( by_overhead < heap_mb )); then
        heap_mb="$by_overhead"
    fi
    if (( heap_mb < 128 )); then
        heap_mb=128
    fi
    printf '%s' "$heap_mb"
}

# Detect OS pretty name without requiring lsb_release.
vnh_detect_os() {
    if [[ -r /etc/os-release ]]; then
        local pretty_name
        pretty_name="$(grep -E '^PRETTY_NAME=' /etc/os-release | head -n1 | cut -d= -f2- | tr -d '"')"
        if [[ -n "$pretty_name" ]]; then
            printf '%s' "$pretty_name"
            return 0
        fi
    fi
    uname -sr
}

# Detect primary architecture label normalized to amd64 / arm64.
vnh_detect_arch() {
    local raw
    raw="$(uname -m 2>/dev/null || printf 'unknown')"
    case "$raw" in
        x86_64|amd64) printf 'amd64 (x86_64)' ;;
        aarch64|arm64) printf 'arm64 (aarch64)' ;;
        *) printf '%s' "$raw" ;;
    esac
}
