#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Universal Container Health Check Tool
# Website: https://vietnam-hosting.net
# License: MIT
#
# Usage:
#   healthcheck.sh tcp <host> <port> [timeout_sec]
#   healthcheck.sh http <url> [timeout_sec]
#   healthcheck.sh process <pattern>
# ==============================================================================

set -euo pipefail

MODE="${1:-tcp}"
TARGET="${2:-127.0.0.1}"
ARG3="${3:-${SERVER_PORT:-8080}}"
TIMEOUT="${4:-5}"

case "$MODE" in
    tcp)
        HOST="$TARGET"
        PORT="$ARG3"
        if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
            printf '[VNH][HEALTH] Invalid TCP port: %s\n' "$PORT" >&2
            exit 2
        fi
        if command -v timeout >/dev/null 2>&1; then
            if timeout "$TIMEOUT" bash -c "exec 3<>/dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
                exit 0
            fi
        else
            if bash -c "exec 3<>/dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
                exit 0
            fi
        fi
        printf '[VNH][HEALTH] TCP check failed for %s:%s\n' "$HOST" "$PORT" >&2
        exit 1
        ;;
    http)
        URL="$TARGET"
        HTTP_TIMEOUT="${ARG3:-5}"
        if command -v curl >/dev/null 2>&1; then
            curl --fail --silent --show-error --max-time "$HTTP_TIMEOUT" --output /dev/null "$URL"
            exit $?
        elif command -v wget >/dev/null 2>&1; then
            wget --quiet --tries=1 --timeout="$HTTP_TIMEOUT" --spider "$URL"
            exit $?
        else
            printf '[VNH][HEALTH] Neither curl nor wget available for HTTP health check.\n' >&2
            exit 2
        fi
        ;;
    process)
        PATTERN="$TARGET"
        if command -v pgrep >/dev/null 2>&1; then
            pgrep -f -- "$PATTERN" >/dev/null 2>&1
            exit $?
        fi
        ps aux 2>/dev/null | grep -v grep | grep -q -- "$PATTERN"
        exit $?
        ;;
    *)
        printf '[VNH][HEALTH] Unknown mode: %s (expected tcp|http|process)\n' "$MODE" >&2
        exit 2
        ;;
esac
