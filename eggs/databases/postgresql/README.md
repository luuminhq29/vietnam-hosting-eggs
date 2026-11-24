# Vietnam Hosting — PostgreSQL 17

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `postgresql` | **Danh mục:** `databases` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Unprivileged PostgreSQL 17 server with scram-sha-256 auth, PG_VERSION upgrade guard, and clean SIGINT/SIGTERM fast shutdown.

- **Phiên bản hỗ trợ:** 17
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://www.postgresql.org (Giấy phép: `PostgreSQL`)

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
| PostgreSQL 17 (Vietnam Hosting GHCR) | `ghcr.io/luuminhq29/yolks:postgresql_17` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/services/postgresql/Dockerfile`. Image đích trên GHCR: `ghcr.io/luuminhq29/yolks:*` (build & publish qua `.github/workflows/build-images.yml` hoặc `vnh-egg build`).

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `DB_USER` | Database Role | `app_user` | Có | `required|alpha_dash|max:32` | Primary PostgreSQL role. |
| `DB_PASSWORD` | Database Password | `(bí mật / để trống)` | Có | `nullable|string|min:12|max:128` | Strong SCRAM-SHA-256 password (auto-generated if empty). |
| `BIND_ADDRESS` | Bind Address | `127.0.0.1` | Không | `required|string|in:127.0.0.1,0.0.0.0` | Admin-controlled listen_addresses (default 127.0.0.1). |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `export PGDATA=/home/container/pgdata; mkdir -p /home/container/run /home/container/backups; if [[ -f "${PGDATA}/PG_VERSION" ]]; then   DATA_VER="$(cat "${PGDATA}/PG_VERSION")"; BIN_VER="$(postgres -V | awk '{print $3}' | cut -d. -f1)";   if [[ "${DATA_VER}" != "${BIN_VER}" ]]; then echo "[VNH][ERROR] PG_VERSION mismatch (data=${DATA_VER}, bin=${BIN_VER}). Run pg_dump upgrade before changing major image." >&2; exit 1; fi; else   PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}";   printf "%s" "${PW}" > /home/container/run/.pwfile; chmod 600 /home/container/run/.pwfile;   initdb -D "${PGDATA}" -U "${DB_USER}" --auth-local=scram-sha-256 --auth-host=scram-sha-256 --pwfile=/home/container/run/.pwfile --encoding=UTF8;   rm -f /home/container/run/.pwfile;   echo "host all all 0.0.0.0/0 scram-sha-256" >> "${PGDATA}/pg_hba.conf"; fi; exec postgres -D "${PGDATA}" -p {{SERVER_PORT}} -h "${BIND_ADDRESS}" -k /home/container/run`
- **Stop Command:** `^C`
- **Startup Detection:** `database system is ready to accept connections`

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

- Sử dụng `pg_dump -Fc -h /home/container/run -p {{SERVER_PORT}} -U ${DB_USER} > /home/container/backups/db.dump` để sao lưu nhất quán và hỗ trợ nâng cấp phiên bản major qua `pg_restore`.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
