#!/usr/bin/env bash
# ==============================================================================
# Vietnam Hosting — Complete Static Verification & Lint Runner
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[1/4] Validating all PTDL_v2 Eggs, metadata, scripts, and Dockerfiles..."
python3 -m generator validate --strict

echo "[2/4] Running Python unit test suite..."
python3 -m unittest discover -s tests -v

if command -v shellcheck >/dev/null 2>&1; then
    echo "[3/4] Running ShellCheck..."
    shellcheck -S warning core/*.sh scripts/*.sh
    find eggs -name "install.sh" -print0 | xargs -0 -r shellcheck -S error
else
    echo "[3/4] ShellCheck not installed locally (enforced in CI .github/workflows/validate.yml)."
fi

if command -v hadolint >/dev/null 2>&1; then
    echo "[4/4] Running Hadolint..."
    find docker -name "Dockerfile" -print0 | xargs -0 -n1 hadolint --failure-threshold error
else
    echo "[4/4] Hadolint not installed locally (enforced in CI .github/workflows/validate.yml)."
fi

echo "[OK] Verification complete."
