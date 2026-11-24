# Hướng dẫn Triển khai Production — Vietnam Hosting Universal Eggs

> **Hệ điều hành máy chủ Node:** Ubuntu 24.04 LTS  
> **Container Runtime:** Docker Engine (cgroup v2)  
> **Hệ thống quản trị:** Pterodactyl Panel 1.11.x / 1.12.x + Wings Multi-Node

## 1. Kiến trúc triển khai Multi-Node, Multi-Tenant

```text
Internet
  │
  ├──► Edge Reverse Proxy / Cloudflare Tunnel (Admin-Controlled TLS & Custom Domains)
  │         └──► Pterodactyl Wings Allocation Ports (Web / App Containers)
  │
  └──► Public IP Node (TCP/UDP Allocations + Wings SFTP :2022)
            └──► Pterodactyl Wings (cgroups v2, PID limit 512, enable_icc: false, AppArmor/Seccomp)
                      └──► Unprivileged Container (`USER container`, `/home/container`)
```

## 2. Bước 1 — Chuẩn bị Node Ubuntu 24.04 LTS & Hardening Wings

1. Cài đặt Docker Engine chính thức trên Ubuntu 24.04 LTS và kích hoạt `cgroup v2`.
2. Áp dụng cấu hình tham chiếu tại `security/wings-hardening.yml`:
   - Đặt `docker.network.enable_icc: false` để chặn lưu lượng ngang hàng giữa container của các khách hàng khác nhau.
   - Đặt `docker.container_pid_limit: 512` để chống fork-bomb.
   - Đặt `docker.log_config` với `max-size: "10m"`, `max-file: "3"` để tránh tràn ổ đĩa do log.
   - Giữ `allowed_mounts: []` — tuyệt đối không mount `/var/run/docker.sock` hay thư mục host vào container khách hàng.
3. Cấu hình tường lửa Host (`ufw` hoặc `nftables`) chỉ mở các cổng cần thiết: HTTPS (443 cho Panel/Proxy), Wings Daemon (8080), Wings SFTP (2022) và dải cổng Allocation đã quy hoạch.

## 3. Bước 2 — Build và Publish Docker Images lên GHCR

Các Egg dùng Official Yolks (`ghcr.io/pterodactyl/yolks:*`, `ghcr.io/parkervcp/games:*`) có thể dùng ngay. Đối với các runtime tùy chỉnh (PHP 8.2–8.5, Linux Distros, Databases, .NET 10/11, Bun, Deno, Rust, v.v.):

1. Push repository lên GitHub (`luuminhq29/vietnam-hosting-eggs`).
2. Vào **Actions → Build & Publish Multi-Arch Docker Images (GHCR) → Run workflow**.
3. Chỉ bật `publish_ghcr = true` sau khi workflow `validate.yml` và `security-scan.yml` đã vượt qua.
4. Sau khi toàn bộ image đã tồn tại trên `ghcr.io/luuminhq29/yolks:*`, chạy lệnh sau nếu muốn toàn bộ 147 Egg dùng thống nhất registry GHCR:
   ```bash
   python3 -m generator generate --registry ghcr
   python3 -m generator validate --strict
   python3 -m generator export --output dist/eggs
   ```

## 4. Bước 3 — Import Egg vào Pterodactyl Panel

1. Chạy `python3 -m generator export --output dist/eggs --format both` (hoặc giải nén `dist/vietnam-hosting-universal-eggs.zip`).
   - Dùng `dist/eggs/ptdl_v2/<category>/egg-vnh-<id>.json` cho **Pterodactyl Panel 1.7–1.12+** (`PTDL_v2`, khuyến nghị).
   - Dùng `dist/eggs/ptdl_v1/<category>/egg-vnh-<id>-v1.json` cho **Pterodactyl Panel 1.0–1.6** hoặc hệ thống yêu cầu định dạng `PTDL_v1`.
2. Trong Pterodactyl Admin Panel → **Nests** → tạo các Nest tương ứng:
   - `Vietnam Hosting — Programming Languages`
   - `Vietnam Hosting — Linux OS (NAT)`
   - `Vietnam Hosting — Discord & Automation Bots`
   - `Vietnam Hosting — Web Hosting`
   - `Vietnam Hosting — Databases`
   - `Vietnam Hosting — Game Servers`
   - `Vietnam Hosting — Applications & Utilities`
3. Nhấn **Import Egg**, tải lên file `egg-vnh-<id>.json` (chuẩn `PTDL_v2`).
4. Kiểm tra danh sách Docker Images hiển thị trong tab **Configuration** và kiểm thử tạo 1 server mẫu trên Node staging trước khi mở bán thương mại.

## 5. Bước 4 — Triển khai Reverse Proxy & Custom Domain / Cloudflare Tunnel

- Tất cả Web Hosting & Application Eggs đều bind vào `0.0.0.0:{{SERVER_PORT}}` và không hardcode IP Node.
- Quản trị viên cấu hình Nginx/Caddy/Traefik hoặc `cloudflared` **ở tầng hạ tầng nền tảng (bên ngoài container khách hàng)** trỏ tới `<Node_Private_or_Public_IP>:<Allocation_Port>`.
- Không cấp quyền chỉnh sửa firewall hay Docker Network từ trong Egg.

## 6. Quy trình Rollback Image khi sự cố

Nếu một bản build Docker image mới gặp lỗi trên staging/production:

```bash
# Xem trước (Dry-Run)
bash scripts/rollback-image.sh python_3.13 sha256:<verified_previous_digest>

# Thực thi rollback sau khi quản trị viên xác nhận
bash scripts/rollback-image.sh python_3.13 sha256:<verified_previous_digest> --confirm-rollback
```
Hoặc chạy trực tiếp trong GitHub Actions workflow `build-images.yml` với tham số `rollback_tag` và `rollback_digest`.
