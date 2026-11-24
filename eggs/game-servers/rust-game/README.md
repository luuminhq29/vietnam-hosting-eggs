# Vietnam Hosting — Rust Game Server

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `rust-game` | **Danh mục:** `game-servers` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Official Facepunch Rust Linux dedicated server via SteamCMD (AppID 258550, AMD64 only).

- **Phiên bản hỗ trợ:** Latest SteamCMD (AppID 258550)
- **Kiến trúc CPU:** AMD64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Official Pterodactyl/Community Yolks (đã xác minh nguồn công khai)
- **Dự án upstream:** https://wiki.facepunch.com/rust/ (Giấy phép: `Facepunch Studios EULA`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **yêu cầu tài liệu chính thức từ nhà phát triển upstream**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 4096 MiB | 8192 MiB |
| Ổ cứng | 16384 MiB | ≥ 32768 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Rust Game Image (Official Pterodactyl) | `ghcr.io/pterodactyl/games:rust` |

> [!TIP]
> Egg sử dụng trực tiếp Official Pterodactyl / Community Yolks đã có sẵn. Có thể chuyển sang image nội bộ Vietnam Hosting bằng `vnh-egg generate --registry ghcr` sau khi publish GHCR.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `SRCDS_APPID` | Steam AppID | `258550` | Không | `required|integer` | Official Valve Steam Dedicated Server AppID (admin-locked). |
| `SRCDS_BETAID` | Steam Beta Branch | `(trống)` | Có | `nullable|string|max:64` | Optional Steam beta branch name. |
| `SRCDS_BETAPASS` | Steam Beta Password | `(trống)` | Có | `nullable|string|max:128` | Optional Steam beta branch password. |
| `STEAM_USER` | Steam Username | `(trống)` | Có | `nullable|string|max:128` | Steam account username (leave blank for anonymous login). |
| `STEAM_PASS` | Steam Password | `(trống)` | Có | `nullable|string|max:128` | Steam account password (leave blank for anonymous login; never logged). |
| `STEAM_AUTH` | Steam Guard Code | `(trống)` | Có | `nullable|string|max:32` | Optional Steam Guard auth code. |
| `HOSTNAME` | Server Hostname | `Vietnam Hosting Rust` | Có | `required|string|max:128` | Display name in Rust server browser. |
| `SERVER_IDENTITY` | Server Identity | `rust_vnh` | Có | `required|alpha_dash|max:64` | Directory identity under server/. |
| `MAX_PLAYERS` | Max Players | `50` | Có | `required|integer|between:1,500` | Player slot limit. |
| `WORLD_SIZE` | World Size | `3000` | Có | `required|integer|between:1000,6000` | Procedural map size (1000-6000). |
| `WORLD_SEED` | World Seed | `123456` | Có | `required|integer` | Procedural map seed. |
| `RCON_PORT` | RCON Port | `28016` | Có | `required|integer|between:1024,65535` | Dedicated allocation port for WebRCON. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `exec ./RustDedicated -batchmode +server.port {{SERVER_PORT}} +server.identity "${SERVER_IDENTITY}" +rcon.port "${RCON_PORT}" +rcon.web 1 +server.hostname "${HOSTNAME}" +server.maxplayers "${MAX_PLAYERS}" +server.worldsize "${WORLD_SIZE}" +server.seed "${WORLD_SEED}" -logfile 2>&1`
- **Stop Command:** `quit`
- **Startup Detection:** `Server startup complete`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- Chạy hoàn toàn trong không gian người dùng không đặc quyền (`container`).
- Mọi token/mật khẩu phải truyền qua biến môi trường, tuyệt đối không commit vào Git hoặc in ra log.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
