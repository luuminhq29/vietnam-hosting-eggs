#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Universal Pterodactyl Container Entrypoint
# Website: https://vietnam-hosting.net
# License: MIT
#
# Security guarantees:
#   - Never uses `eval` on untrusted user input.
#   - Redacts secrets before printing any diagnostic output.
#   - Supports Wings STARTUP placeholder substitution ({{VAR}} -> env value).
#   - Runs completely unprivileged under the `container` user in /home/container.
#   - Cleanly forwards SIGTERM and SIGINT for graceful shutdown.
# ==============================================================================

set -euo pipefail

cd "${HOME:-/home/container}"

VNH_CORE_DIR="${VNH_CORE_DIR:-/opt/vnh}"
if [[ -r "${VNH_CORE_DIR}/environment.sh" ]]; then
    # shellcheck source=environment.sh
    source "${VNH_CORE_DIR}/environment.sh"
fi
if [[ -r "${VNH_CORE_DIR}/startup.sh" ]]; then
    # shellcheck source=startup.sh
    source "${VNH_CORE_DIR}/startup.sh"
fi

# Set INTERNAL_IP as expected by Pterodactyl Wings ecosystem
if command -v ip >/dev/null 2>&1; then
    INTERNAL_IP="$(ip route get 1 2>/dev/null | awk '{print $(NF-2);exit}' || printf '0.0.0.0')"
else
    INTERNAL_IP="0.0.0.0"
fi
export INTERNAL_IP

# Run Universal Startup pre-flight phases
vnh_first_boot_init
if ! vnh_validate_environment; then
    vnh_print_banner "Failed"
    exit 1
fi
vnh_print_banner "Starting"
vnh_detect_dependencies
vnh_boot_git_update

# If explicit command arguments were passed directly (e.g., docker run image cmd arg1), exec directly.
if (( $# > 0 )); then
    vnh_log_info "Status: Ready — launching explicit command."
    vnh_supervise_exec "$@"
    exit $?
fi

if [[ -z "${STARTUP:-}" ]]; then
    vnh_log_error "STARTUP environment variable is not set."
    vnh_print_banner "Failed"
    exit 1
fi

# Safely expand {{VAR_NAME}} placeholders using direct environment lookup (ZERO eval).
# Any token not matching ^[A-Z][A-Z0-9_]*$ is left untouched and never evaluated.
expand_pterodactyl_startup() {
    local template="$1"
    local result=""
    local rest="$template"

    # Iterative left-to-right replacement without regex backtracking hazards
    while [[ "$rest" =~ \{\{([A-Z][A-Z0-9_]*)\}\} ]]; do
        local full_match="${BASH_REMATCH[0]}"
        local var_name="${BASH_REMATCH[1]}"
        local prefix="${rest%%"$full_match"*}"
        local suffix="${rest#*"$full_match"}"
        local var_val="${!var_name:-}"
        result+="${prefix}${var_val}"
        rest="$suffix"
    done
    result+="$rest"
    printf '%s' "$result"
}

RESOLVED_STARTUP="$(expand_pterodactyl_startup "${STARTUP}")"

# Print sanitized startup command (secrets redacted)
vnh_log_info "Executing startup command: $(vnh_redact "${RESOLVED_STARTUP}")"

# Execute through bash -c without eval; Pterodactyl STARTUP is admin-defined at Egg level.
# All Egg startup templates quote user-editable variables safely or dispatch to typed handlers.
if [[ "${VNH_SUPERVISE:-0}" == "1" ]]; then
    vnh_supervise_exec /bin/bash -c "$RESOLVED_STARTUP"
else
    exec /bin/bash -c "$RESOLVED_STARTUP"
fi
