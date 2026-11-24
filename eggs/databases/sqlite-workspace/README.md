# Vietnam Hosting — SQLite Workspace (File & CLI)

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `sqlite-workspace` | **Danh mục:** `databases` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Embedded SQLite 3 file & CLI management workspace for local .db files, schema migrations, WAL integrity checks, and `.backup` snapshots. NOTE: SQLite is an embedded file database, NOT a standalone networked database server.

- **Phiên bản hỗ trợ:** SQLite 3 (Debian 13)
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Không bắt buộc (ứng dụng kết nối outbound)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://www.sqlite.org (Giấy phép: `Public Domain`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 128 MiB | 256 MiB |
| Ổ cứng | 512 MiB | ≥ 1024 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| SQLite 3 Workspace (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:sqlite_workspace` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/services/sqlite-workspace/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `DB_FILE` | Database Filename | `workspace.db` | Có | `required|string|max:128` | SQLite .db filename inside /home/container/databases/. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `mkdir -p /home/container/databases /home/container/backups; sqlite3 "/home/container/databases/${DB_FILE}" "PRAGMA journal_mode=WAL; PRAGMA integrity_check;"; echo "VIETNAM HOSTING SQLite Workspace Ready (file: /home/container/databases/${DB_FILE}, no network port)"; exec sqlite3 "/home/container/databases/${DB_FILE}"`
- **Stop Command:** `.quit`
- **Startup Detection:** `VIETNAM HOSTING SQLite Workspace Ready`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Lưu ý kiến trúc:** SQLite là cơ sở dữ liệu nhúng dựa trên file cục bộ (CLI / tích hợp trong ứng dụng), **không phải** database server lắng nghe cổng mạng TCP/IP.
- Bảo vệ quyền truy cập file `.db` thông qua Wings SFTP và không chia sẻ chung file SQLite qua NFS.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Luôn dùng lệnh `sqlite3 /home/container/databases/${DB_FILE} ".backup '/home/container/backups/snapshot.db'"` để sao lưu nhất quán khi bật chế độ WAL.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
