#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Universal Installation Helper Library
# Website: https://vietnam-hosting.net
# License: MIT
#
# Standardizes safe, idempotent installations inside /mnt/server:
#   - Network reachability check
#   - URL protocol validation (https only unless explicitly allowed)
#   - Bounded retries with timeouts
#   - SHA256 checksum verification when upstream provides digests
#   - First-install vs Reinstall detection without deleting user data
#   - Credential-safe Git deployment
# ==============================================================================

set -euo pipefail

VNH_SERVER_DIR="${VNH_SERVER_DIR:-/mnt/server}"
VNH_INSTALL_MARKER="${VNH_SERVER_DIR}/.vnh_installed"
VNH_DOWNLOAD_TIMEOUT="${VNH_DOWNLOAD_TIMEOUT:-120}"
VNH_CONNECT_TIMEOUT="${VNH_CONNECT_TIMEOUT:-15}"
VNH_MAX_RETRIES="${VNH_MAX_RETRIES:-3}"

vnh_inst_log() {
    printf '[VNH][INSTALL] %s\n' "$1"
}

vnh_inst_err() {
    printf '[VNH][INSTALL][ERROR] %s\n' "$1" >&2
}

vnh_inst_init() {
    mkdir -p "${VNH_SERVER_DIR}"
    cd "${VNH_SERVER_DIR}"

    if [[ -f "${VNH_INSTALL_MARKER}" ]]; then
        export VNH_IS_REINSTALL="1"
        vnh_inst_log "Detected existing installation (reinstall mode). Preserving user data and configs."
    else
        export VNH_IS_REINSTALL="0"
        vnh_inst_log "Detected first-time installation in ${VNH_SERVER_DIR}."
    fi
}

vnh_inst_mark_complete() {
    local egg_id="${1:-unknown}"
    local version="${2:-1.0.0}"
    {
        printf 'egg_id=%s\n' "$egg_id"
        printf 'version=%s\n' "$version"
        printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf 'unknown')"
    } > "${VNH_INSTALL_MARKER}"
    vnh_inst_log "Installation complete for ${egg_id} (v${version})."
}

vnh_inst_require_cmds() {
    local missing=()
    local cmd
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done
    if (( ${#missing[@]} > 0 )); then
        vnh_inst_err "Missing required installation tools: ${missing[*]}"
        return 1
    fi
    return 0
}

vnh_inst_check_network() {
    local probe_url="${1:-https://cloudflare.com/cdn-cgi/trace}"
    if command -v curl >/dev/null 2>&1; then
        if curl -fsSL --connect-timeout "${VNH_CONNECT_TIMEOUT}" --max-time 20 -o /dev/null "$probe_url" 2>/dev/null; then
            return 0
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q --timeout="${VNH_CONNECT_TIMEOUT}" --tries=1 --spider "$probe_url" 2>/dev/null; then
            return 0
        fi
    fi
    vnh_inst_err "Outbound network connectivity check failed (${probe_url})."
    return 1
}

# Download a verified URL with timeout, bounded retry, and optional SHA256 verification.
vnh_inst_download() {
    local url="${1:-}"
    local dest="${2:-}"
    local expected_sha256="${3:-}"

    if [[ -z "$url" ]] || [[ -z "$dest" ]]; then
        vnh_inst_err "vnh_inst_download requires <url> <dest> [sha256]."
        return 1
    fi

    if [[ ! "$url" =~ ^https:// ]]; then
        vnh_inst_err "Rejected non-HTTPS download URL: ${url}"
        return 1
    fi

    local attempt=1
    local tmp_dest="${dest}.vnh.tmp"
    while (( attempt <= VNH_MAX_RETRIES )); do
        vnh_inst_log "Downloading (${attempt}/${VNH_MAX_RETRIES}): ${url}"
        if command -v curl >/dev/null 2>&1; then
            if curl -fsSL \
                --connect-timeout "${VNH_CONNECT_TIMEOUT}" \
                --max-time "${VNH_DOWNLOAD_TIMEOUT}" \
                --retry 0 \
                -A "VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)" \
                -o "$tmp_dest" "$url"; then
                break
            fi
        elif command -v wget >/dev/null 2>&1; then
            if wget -q \
                --timeout="${VNH_CONNECT_TIMEOUT}" \
                --tries=1 \
                --user-agent="VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)" \
                -O "$tmp_dest" "$url"; then
                break
            fi
        else
            vnh_inst_err "Neither curl nor wget is installed in the installation container."
            return 1
        fi

        rm -f "$tmp_dest"
        if (( attempt == VNH_MAX_RETRIES )); then
            vnh_inst_err "Failed to download ${url} after ${VNH_MAX_RETRIES} attempts."
            return 1
        fi
        sleep $(( attempt * 2 ))
        attempt=$(( attempt + 1 ))
    done

    if [[ -n "$expected_sha256" ]]; then
        if command -v sha256sum >/dev/null 2>&1; then
            local actual_sha256
            actual_sha256="$(sha256sum "$tmp_dest" | awk '{print $1}')"
            if [[ "${actual_sha256,,}" != "${expected_sha256,,}" ]]; then
                rm -f "$tmp_dest"
                vnh_inst_err "SHA256 checksum mismatch for ${dest}! Expected ${expected_sha256}, got ${actual_sha256}."
                return 1
            fi
            vnh_inst_log "SHA256 verified for ${dest}."
        else
            vnh_inst_err "sha256sum not available to verify required checksum."
            rm -f "$tmp_dest"
            return 1
        fi
    fi

    mv -f "$tmp_dest" "$dest"
    return 0
}

# Safe Git clone or pull without printing credentials and without wiping user files.
vnh_inst_git_sync() {
    local repo="${1:-}"
    local branch="${2:-}"
    local username="${3:-}"
    local token="${4:-}"

    if [[ -z "$repo" ]]; then
        return 0
    fi

    if [[ ! "$repo" =~ ^https:// ]]; then
        vnh_inst_err "Only HTTPS Git repository URLs are permitted (got invalid scheme)."
        return 1
    fi

    vnh_inst_require_cmds git || return 1

    # Configure git credential helper in memory without echoing token to logs.
    local askpass_script=""
    if [[ -n "$token" ]]; then
        askpass_script="$(mktemp /tmp/vnh-git-askpass.XXXXXX)"
        chmod 700 "$askpass_script"
        cat > "$askpass_script" <<'EOF'
#!/usr/bin/env sh
case "$1" in
    *Username*) printf '%s\n' "${VNH_GIT_USER:-git}" ;;
    *Password*) printf '%s\n' "${VNH_GIT_TOKEN:-}" ;;
esac
EOF
        export GIT_ASKPASS="$askpass_script"
        export GIT_TERMINAL_PROMPT=0
        export VNH_GIT_USER="${username:-git}"
        export VNH_GIT_TOKEN="$token"
    fi

    local rc=0
    if [[ -d "${VNH_SERVER_DIR}/.git" ]]; then
        vnh_inst_log "Updating existing Git repository..."
        if [[ -n "$branch" ]]; then
            git -C "${VNH_SERVER_DIR}" fetch --depth 1 origin "$branch" || rc=$?
            if (( rc == 0 )); then
                git -C "${VNH_SERVER_DIR}" checkout -B "$branch" "origin/${branch}" || rc=$?
            fi
        else
            git -C "${VNH_SERVER_DIR}" pull --ff-only || rc=$?
        fi
    else
        # Clone into temporary staging dir if server dir has non-git marker files, then merge safely.
        local staging_dir
        staging_dir="$(mktemp -d /tmp/vnh-git-clone.XXXXXX)"
        vnh_inst_log "Cloning Git repository into ${VNH_SERVER_DIR}..."
        local clone_args=(clone --depth 1)
        if [[ -n "$branch" ]]; then
            clone_args+=(--branch "$branch" --single-branch)
        fi
        if git "${clone_args[@]}" "$repo" "$staging_dir"; then
            cp -an "${staging_dir}/." "${VNH_SERVER_DIR}/"
        else
            rc=$?
        fi
        rm -rf "$staging_dir"
    fi

    if [[ -n "$askpass_script" ]]; then
        rm -f "$askpass_script"
        unset GIT_ASKPASS VNH_GIT_USER VNH_GIT_TOKEN
    fi

    if (( rc != 0 )); then
        vnh_inst_err "Git synchronization failed with exit code ${rc}."
        return "$rc"
    fi
    vnh_inst_log "Git synchronization completed."
    return 0
}
