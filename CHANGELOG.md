# Lịch sử Thay đổi (Changelog) — Vietnam Hosting Universal Eggs

## [1.1.0] — 2026-11-24

### Hỗ trợ đồng thời cả `PTDL_v1` và `PTDL_v2`

- Bổ sung JSON Schema chuẩn `schemas/ptdl_v1.schema.json` và template `templates/egg_ptdl_v1.json.tmpl`.
- Sinh đồng thời `egg.json` (`PTDL_v2`) và `egg-ptdl-v1.json` (`PTDL_v1` sử dụng mảng `images[]`, không chứa `file_denylist`/`field_type` để tương thích tuyệt đối Panel 1.0–1.6+) cho toàn bộ **147 Egg** (tổng **294 file Egg JSON**).
- Nâng cấp `vnh-egg validate` để kiểm tra chéo đồng bộ giữa `PTDL_v1` và `PTDL_v2`, nâng cấp `vnh-egg export --format both|ptdl_v1|ptdl_v2`, bổ sung `egg_download_v1` vào `catalog.json` và `panel_1x_ptdl_v1` vào `compatibility.json`.

## [1.0.0] — 2026-11-24

### Khởi tạo hệ sinh thái hoàn chỉnh (Phases 1–7)

- **Core Runtime (`core/`):** Xây dựng hệ thống khởi động chung gồm `entrypoint.sh`, `startup.sh`, `installer.sh`, `healthcheck.sh`, `environment.sh` và `nat-ssh.sh` — không sử dụng `eval`, che bí mật tự động, tính toán JVM Heap động và giới hạn luồng biên dịch chia sẻ.
- **Universal CLI (`vnh-egg`):** Hỗ trợ đầy đủ 10 lệnh (`list`, `create`, `generate`, `validate`, `build`, `test`, `export`, `update`, `doctor`, `package`), chế độ `--dry-run` và cổng xác nhận quản trị viên (`--confirm-publish`).
- **147 Pterodactyl Eggs chuẩn `PTDL_v2`:**
  - `languages`: 26 ngôn ngữ lập trình (Python 3.10–3.14, Node.js 20–26, Bun, Deno, Java 8–25, Rust, Go, C/C++, .NET 8–11, PHP 8.2–8.5 + 16 ngôn ngữ bổ sung).
  - `operating-systems`: 15 bản phân phối Linux NAT Container (Ubuntu 20.04–26.04, Debian 12–13, Alpine 3.23, Fedora 44, Rocky 9, AlmaLinux 9, Arch Linux AMD64, Kali Minimal, openSUSE 15.6, Amazon Linux 2023, Oracle Linux 9).
  - `discord-bots`: 17 Egg cho Discord/Telegram Bot và Automation/Background/Scheduled Workers.
  - `web-hosting`: 22 Egg cho Static Web, Nginx, Apache, Caddy, PHP-FPM, WordPress, Laravel, Django, Flask, FastAPI, Express, Next.js, Nuxt.js, SvelteKit, Astro, React, Vue, Spring Boot, ASP.NET Core, Go Web, Rust Axum, Rust Actix Web.
  - `databases`: 14 Egg cho MySQL 8.4, MariaDB 11.4, PostgreSQL 17, MongoDB 8.0, Redis 7.4, Valkey 8.1, SQLite Workspace (file/CLI), CouchDB 3.4, ClickHouse 25, InfluxDB 2.7, TimescaleDB, Qdrant, Meilisearch, Typesense.
  - `game-servers`: 29 Egg (13 Minecraft + 16 game khác với Steam AppID và ma trận kiến trúc AMD64/ARM64 chính xác).
  - `applications` & `utilities`: 24 Egg (Lavalink, Uptime Kuma, n8n, Gitea, Forgejo, Vaultwarden, File Browser, Syncthing, MinIO, RabbitMQ, Mosquitto, Prometheus, Grafana, ntfy, SearXNG, JupyterLab, Code Server, Open WebUI, Ollama CPU, SFTP Storage, Backup Worker, Webhook Receiver, API Worker, Queue Worker).
- **90 Pinned Dockerfiles (`docker/`):** Multi-arch AMD64/ARM64 (trừ Arch Linux chỉ AMD64), không dùng `latest`, chạy unprivileged với `USER container`.
- **CI/CD & Security:** 6 GitHub Actions workflow (`validate.yml`, `build-images.yml`, `security-scan.yml`, `test-eggs.yml`, `release.yml`, `check-updates.yml`), Trivy config, Wings hardening profile và Catalog API tĩnh + CLI/HTTP server.
