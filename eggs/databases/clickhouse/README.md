# Vietnam Hosting — ClickHouse 25 LTS

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `clickhouse` | **Danh mục:** `databases` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Columnar OLAP ClickHouse 25 LTS analytics server with container-scoped data directory and memory limits.

- **Phiên bản hỗ trợ:** 25.3 LTS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://clickhouse.com (Giấy phép: `Apache-2.0`)

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
| ClickHouse 25.3 LTS (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:clickhouse_25` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/services/clickhouse/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `CLICKHOUSE_PASSWORD` | Default User Password | `(bí mật / để trống)` | Có | `nullable|string|min:12|max:128` | Hashed to SHA256 in users.xml (auto-generated if blank). |
| `BIND_ADDRESS` | Bind Address | `127.0.0.1` | Không | `required|string|in:127.0.0.1,0.0.0.0` | Admin-controlled listen_host. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `mkdir -p /home/container/data /home/container/tmp /home/container/logs; sed "s|__PORT__|{{SERVER_PORT}}|g; s|__BIND__|${BIND_ADDRESS}|g" /home/container/config.xml.tpl > /home/container/config.xml; exec clickhouse-server --config-file=/home/container/config.xml`
- **Stop Command:** `^C`
- **Startup Detection:** `Ready for connections`

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

- Sử dụng câu lệnh `BACKUP DATABASE ... TO Disk(...)` hoặc `clickhouse-backup` trước khi sao lưu container.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
