# Vietnam Hosting — SFTP Storage Vault

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `sftp-storage` | **Danh mục:** `utilities` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Dedicated persistent SFTP storage box powered natively by Pterodactyl Wings SFTP daemon (no root SSH daemon required). Reports disk usage and integrity status in Console.

- **Phiên bản hỗ trợ:** Debian 13 / Wings Native SFTP
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Không bắt buộc (ứng dụng kết nối outbound)
- **Nguồn Docker Image:** Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build
- **Dự án upstream:** https://vietnam-hosting.net (Giấy phép: `MIT`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 128 MiB | 256 MiB |
| Ổ cứng | 5120 MiB | ≥ 10240 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Debian Official Yolk | `ghcr.io/pterodactyl/yolks:debian` |
| Base Debian 13 (Vietnam Hosting GHCR - Build Required) | `ghcr.io/luuminhq29/yolks:base_debian13` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/base/debian-13/Dockerfile`. Image đích trên GHCR: `ghcr.io/luuminhq29/yolks:*` (build & publish qua `.github/workflows/build-images.yml` hoặc `vnh-egg build`).

## 4. Biến môi trường (Egg Variables)

_Egg này không yêu cầu biến môi trường bổ sung ngoài biến hệ thống của Pterodactyl._

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `mkdir -p /home/container/storage; echo "VIETNAM HOSTING SFTP Storage Vault Ready — connect via Pterodactyl Wings SFTP credentials."; du -sh /home/container/storage 2>/dev/null || true; trap "exit 0" TERM INT; while true; do sleep 3600; done`
- **Stop Command:** `^C`
- **Startup Detection:** `VIETNAM HOSTING SFTP Storage Vault Ready`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- Truy cập SFTP được xác thực và cô lập hoàn toàn bởi **Pterodactyl Wings SFTP Server** — không chạy `sshd` đặc quyền bên trong container.
- Giới hạn dung lượng đĩa được Wings/Host Disk Quota cưỡng chế.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
