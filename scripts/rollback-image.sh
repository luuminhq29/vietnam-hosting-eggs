#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Safe GHCR Docker Image Rollback Utility
# Usage:
#   scripts/rollback-image.sh <tag> <verified_sha256_digest> [--confirm-rollback]
#
# Dry-run by default. Requires explicit --confirm-rollback approval from admin.
# ==============================================================================

set -euo pipefail

TAG="${1:-}"
DIGEST="${2:-}"
CONFIRM="${3:-}"
REGISTRY_REPO="ghcr.io/luuminhq29/yolks"

if [[ -z "$TAG" ]] || [[ -z "$DIGEST" ]]; then
    echo "Usage: $0 <tag> <sha256:digest> [--confirm-rollback]" >&2
    exit 2
fi

if [[ ! "$DIGEST" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    echo "[ERROR] Invalid digest format. Expected sha256:<64-hex-chars>." >&2
    exit 2
fi

SRC_REF="${REGISTRY_REPO}@${DIGEST}"
DST_REF="${REGISTRY_REPO}:${TAG}"

if [[ "$CONFIRM" != "--confirm-rollback" ]]; then
    echo "[DRY-RUN] Would re-tag ${SRC_REF} -> ${DST_REF}"
    echo "[INFO] Pass --confirm-rollback to execute against GHCR."
    exit 0
fi

if command -v crane >/dev/null 2>&1; then
    crane copy "${SRC_REF}" "${DST_REF}"
elif command -v docker >/dev/null 2>&1; then
    docker buildx imagetools create -t "${DST_REF}" "${SRC_REF}"
else
    echo "[ERROR] Neither crane nor docker buildx is installed." >&2
    exit 1
fi

echo "[OK] Rolled back ${DST_REF} to verified digest ${DIGEST}."
