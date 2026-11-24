# Vietnam Hosting — Universal Pterodactyl Egg System

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Tiêu chuẩn Schema:** `PTDL_v1` (`egg-ptdl-v1.json`) & `PTDL_v2` (`egg.json`) — tương thích Pterodactyl Panel 1.0–1.12+ & Wings  
> **Hệ điều hành Node mục tiêu:** Ubuntu 24.04 LTS + Docker Engine + Pterodactyl Wings  
> **Kiến trúc CPU:** AMD64 (`x86_64`) & ARM64 (`aarch64` — ghi rõ từng Egg theo hỗ trợ thực tế của upstream)  
> **Registry mục tiêu:** GitHub Container Registry (`ghcr.io/luuminhq29/yolks:*` — build & publish tự động qua GitHub Actions `build-images.yml`)

---

## 1. Tổng quan hệ sinh thái

**Vietnam Hosting Universal Eggs** là bộ thư viện **147 Pterodactyl Eggs chuẩn `PTDL_v2`**, **90 Dockerfile có tag cố định**, **Universal Startup & Entrypoint System (`core/`)**, công cụ quản trị CLI **`vnh-egg`**, **Catalog API**, **bộ kiểm thử tự động**, **chính sách bảo mật đa khách hàng (Multi-Tenant)** và **6 GitHub Actions CI/CD Workflows**.

| Danh mục (`eggs/`) | Số lượng Egg | Kiến trúc hỗ trợ | Tiêu biểu |
| :--- | :---: | :---: | :--- |
| `languages` | **26** | AMD64 + ARM64 | Python 3.10–3.14, Node.js 20–26, Bun, Deno, Java 8–25, Rust, Go, C/C++, .NET 8–11, PHP 8.2–8.5, Ruby, Lua, LuaJIT, Perl, Kotlin, Scala, Dart, Elixir, Erlang, Haskell, Swift, Zig, Julia, R, Bash, PowerShell |
| `operating-systems` | **15** | 14 Multi-arch, 1 AMD64-only (`arch-linux`) | Ubuntu 20.04–26.04, Debian 12–13, Alpine 3.23, Fedora 44, Rocky 9, AlmaLinux 9, Arch Linux, Kali Minimal, openSUSE 15.6, Amazon Linux 2023, Oracle Linux 9 |
| `discord-bots` | **17** | AMD64 + ARM64 | Discord.py, Pycord, Nextcord, Discord.js, Eris, JDA, Discord.NET, DSharpPlus, Serenity, Twilight, DiscordGo, Telegram Python/Node, Generic Bot, Automation/Background/Scheduled Workers |
| `web-hosting` | **22** | AMD64 + ARM64 | Static Web, Nginx, Apache, Caddy, PHP-FPM, WordPress, Laravel, Django, Flask, FastAPI, Express, Next.js, Nuxt.js, SvelteKit, Astro, React/Vue Prod, Spring Boot, ASP.NET Core, Go Web, Rust Axum/Actix |
| `databases` | **14** | AMD64 + ARM64 | MySQL 8.4, MariaDB 11.4, PostgreSQL 17, MongoDB 8.0, Redis 7.4, Valkey 8.1, SQLite Workspace (file/CLI), CouchDB 3.4, ClickHouse 25, InfluxDB 2.7, TimescaleDB, Qdrant, Meilisearch, Typesense |
| `game-servers` | **29** | 14 Multi-arch, 15 AMD64-only | 13 Minecraft (Vanilla, Paper, Purpur, Spigot BuildTools, Fabric, Forge, NeoForge, Velocity, BungeeCord, Waterfall Legacy, Bedrock, PocketMine-MP, Nukkit) + 16 game (Terraria, TShock, Factorio, Valheim, Palworld, Rust, ARK, CS2, Project Zomboid, DST, TF2, FiveM, MTA:SA, Unturned, Mindustry, OpenTTD) |
| `applications` | **19** | AMD64 + ARM64 | Lavalink, Uptime Kuma, n8n, Gitea, Forgejo, Vaultwarden, File Browser, Syncthing, MinIO, RabbitMQ, Mosquitto, Prometheus, Grafana, ntfy, SearXNG, JupyterLab, Code Server, Open WebUI, Ollama CPU |
| `utilities` | **5** | AMD64 + ARM64 | SFTP Storage (Wings Native), Backup Worker, Webhook Receiver, API Worker, Queue Worker |
| **Tổng cộng** | **147** | **147 AMD64 / 131 ARM64** | **100% chuẩn PTDL_v2, không `eval`, không `privileged`** |

---

## 2. Cấu trúc thư mục dự án

```text
vietnam-hosting-eggs/
├── eggs/                  # 147 thư mục Egg độc lập (egg.json, install.sh, metadata.json, README.md, test.config.json, image-ref.json, example/)
├── docker/                # 90 Dockerfile phân loại theo base/, installers/, languages/, linux/, services/
├── core/                  # Universal Runtime (entrypoint.sh, startup.sh, installer.sh, healthcheck.sh, environment.sh, nat-ssh.sh)
├── generator/             # Source code CLI `vnh-egg` và các spec mô-đun (hỗ trợ custom/*.json)
├── templates/             # Template PTDL_v2, install.sh, README.md
├── schemas/               # JSON Schema chuẩn (ptdl_v2.schema.json, metadata.schema.json, catalog.schema.json)
├── scripts/               # Catalog Search/API server, GHCR rollback script, verify-all script
├── security/              # Trivy config, Wings hardening reference, Multi-tenant Security Policy
├── tests/                 # Bộ kiểm thử tự động unittest
├── docs/                  # Tài liệu tiếng Việt + Static Catalog API (docs/catalog-api/)
├── dist/                  # Gói phát hành vietnam-hosting-universal-eggs.zip + SHA256 + egg export
├── .github/workflows/     # 6 CI/CD workflows (validate, build-images, security-scan, test-eggs, release, check-updates)
├── catalog.json           # Danh mục Egg chuẩn tích hợp Admin Dashboard
├── versions.json          # Quản lý phiên bản base image & vòng đời EOL
└── compatibility.json     # Ma trận tương thích kiến trúc, Panel, Wings, EULA, SteamCMD
```

---

## 3. Sử dụng nhanh công cụ CLI `vnh-egg`

Không yêu cầu cài thư viện Python bên thứ ba (chạy trực tiếp trên Python 3.10+):

```bash
# Kiểm tra sức khỏe toàn bộ repository và công cụ cục bộ
python3 -m generator doctor

# Liệt kê danh sách Egg theo danh mục / kiến trúc / trạng thái
python3 -m generator list --category languages
python3 -m generator list --arch arm64 --format json

# Thêm một runtime tùy chỉnh mới (không cần sửa mã nguồn generator)
python3 -m generator create custom-service --category applications --image ghcr.io/pterodactyl/yolks:debian

# Sinh toàn bộ Egg JSON, install.sh, Dockerfile, README, catalog.json, compatibility.json
python3 -m generator generate
python3 -m generator generate --registry ghcr --dry-run   # Xem trước khi chuyển sang GHCR riêng

# Kiểm tra nghiêm ngặt Schema PTDL_v2, trùng biến, biến chưa khai báo, bảo mật script & Dockerfile
python3 -m generator validate --strict

# Xem trước lệnh Docker Buildx đa kiến trúc (push yêu cầu --confirm-publish)
python3 -m generator build --dry-run

# Chạy kiểm thử và xuất báo cáo
python3 -m generator test --report dist/test-report.json

# Xuất cả 2 định dạng PTDL_v1 & PTDL_v2 sẵn sàng import vào Pterodactyl Panel
python3 -m generator export --output dist/eggs --format both
python3 -m generator export --output dist/eggs --format ptdl_v1   # Chỉ PTDL_v1
python3 -m generator export --output dist/eggs --format ptdl_v2   # Chỉ PTDL_v2

# Đóng gói phát hành ZIP kèm mã kiểm tra SHA256
python3 -m generator package --output dist/vietnam-hosting-universal-eggs.zip
```

---

## 4. Lưu ý quan trọng về Docker Images & Trạng thái Kiểm thử

> [!IMPORTANT]
> 1. **Trạng thái GHCR Registry:** Các image mang nhãn `ghcr.io/luuminhq29/yolks:*` được build từ 90 Dockerfile trong `docker/` và publish lên GitHub Container Registry bằng `.github/workflows/build-images.yml` (`publish_ghcr: true`) hoặc `vnh-egg build --push --confirm-publish`.
> 2. **Ưu tiên Official Yolks:** Những Egg có Official Pterodactyl/Community Yolks đã xác minh (`ghcr.io/pterodactyl/yolks:*`, `ghcr.io/parkervcp/games:*`, `ghcr.io/parkervcp/installers:*`) được cấu hình mặc định sử dụng Official Yolks để có thể import và vận hành ngay.
> 3. **Trạng thái kiểm thử thực tế:** Toàn bộ 147 Egg và 90 Dockerfile đã vượt qua **kiểm tra tĩnh & schema (`PASS`)**. Các bài kiểm tra tích hợp yêu cầu Docker Engine và Pterodactyl Panel/Wings trực tiếp được ghi rõ là **`UNVERIFIED`** (xem chi tiết tại [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)).

---

## 5. Tài liệu chi tiết (Tiếng Việt)

- [Hướng dẫn Triển khai Production (Ubuntu 24.04 + Multi-Node Wings + GHCR + Reverse Proxy)](docs/DEPLOYMENT_GUIDE_VI.md)
- [Kiến trúc NAT Linux Container Hosting & Ranh giới với KVM VPS](docs/NAT_LINUX_HOSTING_VI.md)
- [Tài liệu Tích hợp Egg Catalog API cho Admin Dashboard](docs/CATALOG_API_VI.md)
- [Ma trận Tương thích (AMD64/ARM64, Panel 1.x/2.x, SteamCMD, EULA)](docs/COMPATIBILITY_MATRIX_VI.md)
- [Chính sách Bảo mật & Chống Lạm dụng Đa Khách hàng](security/policy.md)
- [Báo cáo Kiểm thử 17 Tiêu chí Bắt buộc](docs/TEST_REPORT.md)
