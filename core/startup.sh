#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Universal Startup System
# Website: https://vietnam-hosting.net
# License: MIT
#
# Implements all 11 Universal Startup modules:
#   1. Runtime Detection
#   2. Dependency Detection
#   3. Environment Validation
#   4. Startup Validation
#   5. Git Deployment (optional auto-update on boot)
#   6. Process Management (with restart-loop protection)
#   7. Signal Handling (SIGTERM / SIGINT graceful shutdown)
#   8. Health Check integration
#   9. Error Reporting (secret-safe)
#  10. Resource Detection (RAM / CPU / Arch / OS)
#  11. First Boot Initialization (idempotent)
# ==============================================================================

set -euo pipefail

VNH_CORE_DIR="${VNH_CORE_DIR:-/opt/vnh}"
if [[ -r "${VNH_CORE_DIR}/environment.sh" ]]; then
    # shellcheck source=environment.sh
    source "${VNH_CORE_DIR}/environment.sh"
fi

# 1. Runtime Detection
vnh_detect_runtime() {
    if [[ -n "${VNH_RUNTIME_LABEL:-}" ]]; then
        printf '%s' "${VNH_RUNTIME_LABEL}"
        return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 --version 2>&1 | head -n1
    elif command -v node >/dev/null 2>&1; then
        printf 'Node.js %s' "$(node -v 2>/dev/null)"
    elif command -v bun >/dev/null 2>&1; then
        printf 'Bun %s' "$(bun --version 2>/dev/null)"
    elif command -v deno >/dev/null 2>&1; then
        deno --version 2>/dev/null | head -n1
    elif command -v java >/dev/null 2>&1; then
        java -version 2>&1 | head -n1
    elif command -v rustc >/dev/null 2>&1; then
        rustc --version 2>/dev/null | head -n1
    elif command -v go >/dev/null 2>&1; then
        go version 2>/dev/null | head -n1
    elif command -v dotnet >/dev/null 2>&1; then
        printf '.NET %s' "$(dotnet --version 2>/dev/null)"
    elif command -v php >/dev/null 2>&1; then
        php -v 2>/dev/null | head -n1
    elif command -v ruby >/dev/null 2>&1; then
        ruby -v 2>/dev/null | head -n1
    else
        printf 'Linux Container Runtime'
    fi
}

# Print the Vietnam Hosting Universal Runtime Console Banner (zero secrets).
vnh_print_banner() {
    local status="${1:-Starting}"
    local runtime_info os_info arch_info mem_mb port_val workdir
    runtime_info="$(vnh_detect_runtime)"
    os_info="$(vnh_detect_os)"
    arch_info="$(vnh_detect_arch)"
    mem_mb="$(vnh_detect_memory_mb)"
    port_val="${SERVER_PORT:-N/A}"
    workdir="${PWD:-/home/container}"

    local mem_display="Unknown"
    if [[ "$mem_mb" =~ ^[0-9]+$ ]]; then
        mem_display="${mem_mb} MiB"
    fi

    printf '==============================================================\n'
    printf 'VIETNAM HOSTING — UNIVERSAL RUNTIME\n'
    printf '==============================================================\n'
    printf 'Runtime:           %s\n' "$runtime_info"
    printf 'Operating System:  %s\n' "$os_info"
    printf 'Architecture:      %s\n' "$arch_info"
    printf 'Memory Limit:      %s\n' "$mem_display"
    printf 'Allocated Port:    %s\n' "$port_val"
    printf 'Working Directory: %s\n' "$workdir"
    printf 'Status:            %s\n' "$status"
    printf '==============================================================\n'
}

# 2. Dependency Detection (non-destructive inspection)
vnh_detect_dependencies() {
    local found=()
    [[ -f requirements.txt ]] && found+=("requirements.txt")
    [[ -f pyproject.toml ]] && found+=("pyproject.toml")
    [[ -f package.json ]] && found+=("package.json")
    [[ -f Cargo.toml ]] && found+=("Cargo.toml")
    [[ -f go.mod ]] && found+=("go.mod")
    [[ -f pom.xml ]] && found+=("pom.xml")
    [[ -f build.gradle || -f build.gradle.kts ]] && found+=("gradle")
    [[ -f composer.json ]] && found+=("composer.json")
    [[ -f Gemfile ]] && found+=("Gemfile")
    [[ -f CMakeLists.txt ]] && found+=("CMakeLists.txt")
    [[ -f Makefile ]] && found+=("Makefile")
    if (( ${#found[@]} > 0 )); then
        vnh_log_info "Detected project manifests: ${found[*]}"
    fi
}

# 3. Environment Validation
vnh_validate_environment() {
    if [[ -n "${SERVER_PORT:-}" ]]; then
        vnh_validate_port "${SERVER_PORT}" "SERVER_PORT" || return 1
    fi
    if [[ -n "${APP_FILE:-}" ]]; then
        vnh_validate_relpath "${APP_FILE}" || return 1
    fi
    if [[ -n "${PY_FILE:-}" ]]; then
        vnh_validate_relpath "${PY_FILE}" || return 1
    fi
    if [[ -n "${MAIN_FILE:-}" ]]; then
        vnh_validate_relpath "${MAIN_FILE}" || return 1
    fi
    # Export safe build parallelism limits for shared hosting
    local jobs
    jobs="$(vnh_compute_build_jobs)"
    export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-$jobs}"
    export MAKEFLAGS="${MAKEFLAGS:--j${jobs}}"
    export CMAKE_BUILD_PARALLEL_LEVEL="${CMAKE_BUILD_PARALLEL_LEVEL:-$jobs}"
    export VNH_COMPUTED_JOBS="$jobs"
    return 0
}

# 4. First Boot Initialization (idempotent)
vnh_first_boot_init() {
    local marker="${HOME:-/home/container}/.vnh_boot_initialized"
    if [[ ! -f "$marker" ]]; then
        vnh_log_info "Running first-boot initialization..."
        mkdir -p "${HOME:-/home/container}/.local/bin" "${HOME:-/home/container}/.cache" "${HOME:-/home/container}/tmp"
        date -u +%Y-%m-%dT%H:%M:%SZ > "$marker" 2>/dev/null || true
    fi
    export PATH="${HOME:-/home/container}/.local/bin:${PATH}"
    export TMPDIR="${HOME:-/home/container}/tmp"
}

# 5. Optional Boot-Time Git Deployment (only if AUTO_UPDATE=1 and GIT_ADDRESS set)
vnh_boot_git_update() {
    if [[ "${AUTO_UPDATE:-0}" != "1" ]] && [[ "${AUTO_UPDATE:-false}" != "true" ]]; then
        return 0
    fi
    if [[ -z "${GIT_ADDRESS:-}" ]]; then
        return 0
    fi
    if [[ ! -d .git ]]; then
        vnh_log_warn "AUTO_UPDATE enabled but no .git directory found; skipping boot pull."
        return 0
    fi
    if ! command -v git >/dev/null 2>&1; then
        vnh_log_warn "git is not installed in runtime image; skipping AUTO_UPDATE."
        return 0
    fi

    local askpass=""
    if [[ -n "${ACCESS_TOKEN:-}" ]]; then
        askpass="$(mktemp "${TMPDIR:-/tmp}/vnh-askpass.XXXXXX")"
        chmod 700 "$askpass"
        cat > "$askpass" <<'EOF'
#!/usr/bin/env sh
case "$1" in
    *Username*) printf '%s\n' "${USERNAME:-git}" ;;
    *Password*) printf '%s\n' "${ACCESS_TOKEN:-}" ;;
esac
EOF
        export GIT_ASKPASS="$askpass"
        export GIT_TERMINAL_PROMPT=0
    fi

    vnh_log_info "Updating Git repository before startup..."
    if ! git pull --ff-only; then
        vnh_log_warn "Git pull failed; continuing with existing files."
    fi

    if [[ -n "$askpass" ]]; then
        rm -f "$askpass"
        unset GIT_ASKPASS
    fi
}

# 6 & 7. Process Management with Restart-Loop Protection & Signal Forwarding
vnh_supervise_exec() {
    local max_restarts="${VNH_MAX_RESTARTS:-5}"
    local window_sec="${VNH_RESTART_WINDOW_SEC:-60}"
    local enable_supervise="${VNH_SUPERVISE:-0}"

    if [[ "$enable_supervise" != "1" ]]; then
        # Direct exec replaces shell so child receives PID 1/signals directly without overhead.
        exec "$@"
    fi

    local child_pid=""
    local stopping=0
    local restart_times=()

    _vnh_handle_signal() {
        stopping=1
        vnh_log_info "Received shutdown signal; forwarding SIGTERM to child process (${child_pid:-none})..."
        if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
            kill -TERM "$child_pid" 2>/dev/null || true
            local waited=0
            while kill -0 "$child_pid" 2>/dev/null && (( waited < 15 )); do
                sleep 1
                waited=$(( waited + 1 ))
            done
            if kill -0 "$child_pid" 2>/dev/null; then
                vnh_log_warn "Child process did not exit gracefully; sending SIGKILL."
                kill -KILL "$child_pid" 2>/dev/null || true
            fi
        fi
        exit 0
    }

    trap _vnh_handle_signal TERM INT HUP

    local backoff=2
    while true; do
        "$@" &
        child_pid=$!
        local exit_code=0
        wait "$child_pid" || exit_code=$?
        child_pid=""

        if (( stopping == 1 )); then
            exit 0
        fi
        if (( exit_code == 0 )); then
            vnh_log_info "Main process exited cleanly (code 0)."
            exit 0
        fi

        local now
        now="$(date +%s)"
        local pruned=()
        local ts
        for ts in "${restart_times[@]:-}"; do
            if [[ -n "$ts" ]] && (( now - ts <= window_sec )); then
                pruned+=("$ts")
            fi
        done
        pruned+=("$now")
        restart_times=("${pruned[@]}")

        if (( ${#restart_times[@]} > max_restarts )); then
            vnh_log_error "Restart loop detected (${#restart_times[@]} failures within ${window_sec}s). Halting container."
            vnh_print_banner "Failed"
            exit "$exit_code"
        fi

        vnh_log_warn "Main process exited with code ${exit_code}. Restarting in ${backoff}s (${#restart_times[@]}/${max_restarts})..."
        sleep "$backoff"
        backoff=$(( backoff * 2 ))
        (( backoff > 30 )) && backoff=30
    done
}
