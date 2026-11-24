# Vietnam Hosting — MariaDB 11.4 LTS

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `mariadb` | **Danh mục:** `databases` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Unprivileged MariaDB 11.4 LTS container with idempotent initialization, least-privilege app grants, and graceful shutdown.

- **Phiên bản hỗ trợ:** 11.4 LTS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://mariadb.org (Giấy phép: `GPL-2.0`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 512 MiB | 1024 MiB |
| Ổ cứng | 2048 MiB | ≥ 4096 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| MariaDB 11.4 LTS (Vietnam Hosting GHCR) | `ghcr.io/luuminhq29/yolks:mariadb_11.4` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/services/mariadb/Dockerfile`. Image đích trên GHCR: `ghcr.io/luuminhq29/yolks:*` (build & publish qua `.github/workflows/build-images.yml` hoặc `vnh-egg build`).

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `DB_NAME` | Database Name | `app_db` | Có | `required|alpha_dash|max:64` | Initial application database. |
| `DB_USER` | Application User | `app_user` | Có | `required|alpha_dash|max:32` | Least-privilege database user. |
| `DB_PASSWORD` | Application Password | `(bí mật / để trống)` | Có | `nullable|string|min:12|max:128` | Strong password (auto-generated if empty). |
| `BIND_ADDRESS` | Bind Address | `127.0.0.1` | Không | `required|string|in:127.0.0.1,0.0.0.0` | Admin-controlled network bind address. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `mkdir -p /home/container/data /home/container/run /home/container/logs; if [[ ! -d /home/container/data/mysql ]]; then   mariadb-install-db --datadir=/home/container/data --auth-root-authentication-method=normal;   PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}";   printf 'CREATE DATABASE IF NOT EXISTS `%s`; CREATE USER IF NOT EXISTS "%s"@"%%" IDENTIFIED BY "%s"; GRANT ALL PRIVILEGES ON `%s`.* TO "%s"@"%%"; FLUSH PRIVILEGES;\n'     "${DB_NAME}" "${DB_USER}" "${PW}" "${DB_NAME}" "${DB_USER}" > /home/container/run/init.sql;   chmod 600 /home/container/run/init.sql;   exec mariadbd --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mariadb.sock --init-file=/home/container/run/init.sql; fi; rm -f /home/container/run/init.sql; exec mariadbd --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mariadb.sock`
- **Stop Command:** `^C`
- **Startup Detection:** `ready for connections`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Không dùng mật khẩu yếu:** Nếu biến mật khẩu để trống khi cài đặt lần đầu, hệ thống tự động sinh mật khẩu ngẫu nhiên mạnh (`openssl rand`) lưu vào file cấu hình phân quyền `600` (tuyệt đối không in ra console).
- **Nguyên tắc quyền tối thiểu:** Tự động khởi tạo database ứng dụng và tài khoản chỉ có quyền trên database đó.
- **Bảo vệ mạng mặc định:** `BIND_ADDRESS` mặc định `127.0.0.1` — chỉ chuyển sang `0.0.0.0` khi quản trị viên chủ động cho phép mở truy cập ngoài và cấu hình firewall/TLS tầng Node.
- **An toàn dữ liệu:** Không bao giờ ghi đè thư mục dữ liệu khi restart/reinstall; kiểm tra tương thích phiên bản dữ liệu trước khi nâng cấp major version.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng `mariadb-dump --single-transaction -S /home/container/run/mariadb.sock` hoặc `mariadb-backup` để đảm bảo tính nhất quán dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
