"""Phase 5C: All 5 Utility Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import GIT_DEPLOY_VARS, GIT_INSTALL_SNIPPET


def get_specs() -> list[EggSpec]:
    return [
        # 1. SFTP Storage
        EggSpec(
            id="sftp-storage",
            name="Vietnam Hosting — SFTP Storage Vault",
            category="utilities",
            description=(
                "Dedicated persistent SFTP storage box powered natively by Pterodactyl Wings SFTP daemon "
                "(no root SSH daemon required). Reports disk usage and integrity status in Console."
            ),
            icon="storage",
            supported_versions=["Debian 13 / Wings Native SFTP"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=5120,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/base/debian-13/Dockerfile",
            docker_images={
                "Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian",
                "Base Debian 13 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:base_debian13",
            },
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup=(
                'mkdir -p /home/container/storage; '
                'echo "VIETNAM HOSTING SFTP Storage Vault Ready — connect via Pterodactyl Wings SFTP credentials."; '
                'du -sh /home/container/storage 2>/dev/null || true; '
                'trap "exit 0" TERM INT; while true; do sleep 3600; done'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING SFTP Storage Vault Ready",
            install_body='mkdir -p /mnt/server/storage\necho "[VNH][INSTALL] SFTP Storage Vault initialized under /mnt/server/storage (managed via Wings SFTP)."\n',
            variables=[],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
            security_notes_vi="- Truy cập SFTP được xác thực và cô lập hoàn toàn bởi **Pterodactyl Wings SFTP Server** — không chạy `sshd` đặc quyền bên trong container.\n- Giới hạn dung lượng đĩa được Wings/Host Disk Quota cưỡng chế.",
        ),

        # 2. Backup Worker
        EggSpec(
            id="backup-worker",
            name="Vietnam Hosting — Backup Worker",
            category="utilities",
            description="Scheduled outbound backup worker running encrypted archive/sync jobs from /home/container/jobs without host privileges.",
            icon="backup",
            supported_versions=["Debian 13 / Bash + Python"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/base/debian-13/Dockerfile",
            docker_images={
                "Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian",
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
            },
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup=(
                'echo "VIETNAM HOSTING Backup Worker Ready (interval=${BACKUP_INTERVAL_SEC}s)"; '
                'trap "exit 0" TERM INT; '
                'while true; do /bin/bash "${BACKUP_SCRIPT}" || echo "[VNH][WARN] Backup run failed"; sleep "${BACKUP_INTERVAL_SEC}"; done'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Backup Worker Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/staging /mnt/server/logs
if [[ ! -f /mnt/server/backup.sh ]]; then
    cat > /mnt/server/backup.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "[VNH][BACKUP] $(date -u +%Y-%m-%dT%H:%M:%SZ) — Customize backup.sh with your rclone/restic/S3 sync commands."
EOF
    chmod 755 /mnt/server/backup.sh
fi
''',
            variables=[
                VariableSpec("Backup Script", "Relative path to backup shell script.", "BACKUP_SCRIPT", "backup.sh", rules="required|string|max:128"),
                VariableSpec("Backup Interval (Seconds)", "Interval between scheduled backup runs (min 300s).", "BACKUP_INTERVAL_SEC", "21600", rules="required|integer|between:300,604800"),
                VariableSpec("Backup Encryption Passphrase", "Secret passphrase exported as BACKUP_PASSPHRASE (never printed).", "BACKUP_PASSPHRASE", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
        ),

        # 3. Webhook Receiver
        EggSpec(
            id="webhook-receiver",
            name="Vietnam Hosting — Webhook Receiver",
            category="utilities",
            description="Production HTTP webhook ingestion service on Python 3.13 bound to 0.0.0.0:{{SERVER_PORT}} with HMAC-SHA256 signature verification.",
            icon="webhook",
            supported_versions=["Python 3.13"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={"Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13"},
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup='exec python3 "${WEBHOOK_APP}"',
            stop="^C",
            startup_done="VIETNAM HOSTING Webhook Receiver Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/receiver.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/receiver.py <<'EOF'
import hashlib, hmac, os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("SERVER_PORT", "8080"))
SECRET = os.environ.get("WEBHOOK_SECRET", "").encode()

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")
            return
        self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(min(length, 1048576))
        if SECRET:
            sig = self.headers.get("X-Hub-Signature-256", "")
            expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected):
                self.send_response(401); self.end_headers(); self.wfile.write(b"invalid signature\n")
                return
        self.send_response(202); self.end_headers(); self.wfile.write(b"accepted\n")

if __name__ == "__main__":
    print(f"VIETNAM HOSTING Webhook Receiver Ready on 0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), WebhookHandler).serve_forever()
EOF
fi
''',
            variables=[
                VariableSpec("Webhook App File", "Python script handling incoming webhooks.", "WEBHOOK_APP", "receiver.py", rules="required|string|max:128"),
                VariableSpec("HMAC Webhook Secret", "Optional shared secret for X-Hub-Signature-256 verification (never logged).", "WEBHOOK_SECRET", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
        ),

        # 4. API Worker
        EggSpec(
            id="api-worker",
            name="Vietnam Hosting — API Worker",
            category="utilities",
            description="Lightweight microservice API worker supporting Python or Node.js bound to 0.0.0.0:{{SERVER_PORT}} behind reverse proxy.",
            icon="api",
            supported_versions=["Python 3.13", "Node.js 24 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            },
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13", "Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24"},
            startup='export PORT={{SERVER_PORT}} HOST=0.0.0.0; exec /bin/bash "${START_SCRIPT}"',
            stop="^C",
            startup_done="Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/start.sh ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\necho "VIETNAM HOSTING API Worker Ready on 0.0.0.0:${SERVER_PORT:-8080}"\\nexec sleep infinity\\n\' > /mnt/server/start.sh; chmod +x /mnt/server/start.sh; fi\n',
            variables=[
                VariableSpec("Start Script", "Startup script executing your API worker.", "START_SCRIPT", "start.sh", rules="required|string|max:128"),
                VariableSpec("API Secret Key", "Optional service secret key (never logged).", "API_SECRET", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
        ),

        # 5. Queue Worker
        EggSpec(
            id="queue-worker",
            name="Vietnam Hosting — Queue Worker",
            category="utilities",
            description="Outbound asynchronous queue consumer worker (Redis/Valkey/RabbitMQ) with exponential backoff and graceful SIGTERM drain.",
            icon="queue",
            supported_versions=["Python 3.13", "Node.js 24 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            },
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13", "Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24"},
            startup='export VNH_SUPERVISE=1 CONCURRENCY="${CONCURRENCY}"; exec /bin/bash "${WORKER_SCRIPT}"',
            stop="^C",
            startup_done="Queue Worker Ready|Connected|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/worker.sh ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\necho "VIETNAM HOSTING Queue Worker Ready (concurrency=${CONCURRENCY:-2})"\\nexec sleep infinity\\n\' > /mnt/server/worker.sh; chmod +x /mnt/server/worker.sh; fi\n',
            variables=[
                VariableSpec("Worker Script", "Queue consumer launch script.", "WORKER_SCRIPT", "worker.sh", rules="required|string|max:128"),
                VariableSpec("Queue URL", "Broker connection string (never logged).", "QUEUE_URL", "", rules="nullable|string|max:512"),
                VariableSpec("Worker Concurrency", "Concurrent consumer threads/processes.", "CONCURRENCY", "2", rules="required|integer|between:1,16"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
        ),
    ]
