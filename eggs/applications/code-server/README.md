# Vietnam Hosting — Code Server (VS Code Web)

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `code-server` | **Danh mục:** `applications` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Browser-based VS Code (code-server) workspace running unprivileged in /home/container/workspace with mandatory password auth (no Docker Socket).

- **Phiên bản hỗ trợ:** 4.98+
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Official Pterodactyl/Community Yolks (đã xác minh nguồn công khai)
- **Dự án upstream:** https://coder.com (Giấy phép: `MIT`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 1024 MiB | 2048 MiB |
| Ổ cứng | 4096 MiB | ≥ 8192 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Debian Official Yolk | `ghcr.io/pterodactyl/yolks:debian` |

> [!TIP]
> Egg sử dụng trực tiếp Official Pterodactyl / Community Yolks đã có sẵn. Có thể chuyển sang image nội bộ Vietnam Hosting bằng `vnh-egg generate --registry ghcr` sau khi publish GHCR.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `CS_PASSWORD` | Web IDE Password | `(bí mật / để trống)` | Có | `nullable|string|min:12|max:128` | Strong login password (auto-generated into .cs_password if empty). |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `if [[ ! -f /home/container/.cs_password ]]; then   PW="${CS_PASSWORD:-$(openssl rand -base64 20 | tr -dc A-Za-z0-9 | head -c 20)}";   printf "%s" "${PW}" > /home/container/.cs_password; chmod 600 /home/container/.cs_password; fi; export PASSWORD="$(cat /home/container/.cs_password)"; exec ./code-server/bin/code-server --bind-addr "0.0.0.0:{{SERVER_PORT}}" --user-data-dir /home/container/.local/share/code-server --extensions-dir /home/container/.local/share/code-server/extensions /home/container/workspace`
- **Stop Command:** `^C`
- **Startup Detection:** `HTTP server listening on`

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
