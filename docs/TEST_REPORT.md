# Báo cáo Kiểm thử Hệ thống — Vietnam Hosting Universal Eggs

> **Ngày lập báo cáo:** 2026-11-24  
> **Môi trường kiểm thử cục bộ:** Windows + Python 3.14.7 (không có Docker Engine và không có Pterodactyl Panel/Wings trực tiếp trên máy build)  
> **Nguyên tắc trung thực:** Mọi hạng mục đòi hỏi Docker runtime hoặc Pterodactyl Panel/Wings trực tiếp được ghi rõ là **`UNVERIFIED`**, tuyệt đối không khai báo giả là `PASS`.

## 1. Kết quả Kiểm thử Tĩnh & Tự động (Đã thực thi cục bộ)

| Bộ kiểm thử | Phạm vi | Kết quả | Chi tiết |
| :--- | :--- | :---: | :--- |
| `vnh-egg validate --strict` | 147 Eggs (`PTDL_v1` + `PTDL_v2` = 294 tệp JSON), 90 Dockerfiles, `core/*.sh`, `catalog.json` | **PASS** | 0 lỗi, 0 cảnh báo |
| `unittest` (`tests/test_eggs_suite.py`) | Kiểm tra số lượng 147 Egg, schema, trùng biến, biến chưa khai báo, không `eval`, không `curl \| sh`, tính trung thực AMD64/ARM64, SQLite/Linux unprivileged, CLI dry-run & cổng `--confirm-publish` | **PASS** | Toàn bộ test case đạt |
| `vnh-egg package` | Đóng gói `dist/vietnam-hosting-universal-eggs.zip` + SHA256 | **PASS** | Tạo gói phát hành và mã băm thành công |

## 2. Bảng 17 Tiêu chí Kiểm thử Bắt buộc (Mục XIX)

| STT | Tiêu chí kiểm thử bắt buộc | Trạng thái hiện tại | Phương thức xác minh |
| :---: | :--- | :---: | :--- |
| 1 | Import vào Pterodactyl Panel thành công | `UNVERIFIED` (Schema `PTDL_v2` đã `PASS` kiểm tra tĩnh) | Cần import thực tế trên Panel 1.11.x / 1.12.x Staging |
| 2 | Installation Script chạy thành công | `UNVERIFIED` (Cú pháp/chính sách script đã `PASS` tĩnh) | Chạy thực tế qua Wings installer container + CI `ShellCheck` |
| 3 | Docker Image tồn tại và tải được | `UNVERIFIED` | Official Yolks cần `docker pull` kiểm chứng; 90 image `ghcr.io/vietnam-hosting/yolks:*` cần chạy `build-images.yml` |
| 4 | Server khởi động thành công | `UNVERIFIED` | Kiểm thử trên CI `test-eggs.yml` & Node Staging |
| 5 | Startup Detection hoạt động | `UNVERIFIED` | Kiểm chứng regex `config.startup.done` trên Wings thực tế |
| 6 | Console hoạt động | `UNVERIFIED` | Kiểm chứng stdin/stdout trực tiếp qua Pterodactyl Web Console |
| 7 | Stop Command hoạt động | `UNVERIFIED` | Kiểm chứng `SIGTERM`/`^C`/`stop`/`end`/`quit` trên Wings |
| 8 | Restart không mất dữ liệu | `UNVERIFIED` | Kiểm chứng dữ liệu `/home/container` sau chu kỳ Stop → Start |
| 9 | Reinstall đúng hành vi tài liệu hóa | `UNVERIFIED` | Kiểm chứng cờ `.vnh_installed` bảo toàn dữ liệu người dùng |
| 10 | SFTP hoạt động | `UNVERIFIED` | Kiểm chứng đăng nhập Wings SFTP cổng 2022 trên Node |
| 11 | Port Allocation hoạt động (nếu cần inbound) | `UNVERIFIED` | Kiểm chứng kết nối tới `0.0.0.0:{{SERVER_PORT}}` |
| 12 | RAM và CPU Limit hoạt động | `UNVERIFIED` | Kiểm chứng cgroups v2 của Wings trên Ubuntu 24.04 LTS |
| 13 | Không yêu cầu quyền đặc quyền | `PASS (Static)` / `UNVERIFIED (Runtime)` | Đã kiểm chứng tĩnh 100% Dockerfile dùng `USER container`, metadata không `privileged`; cần xác nhận lại trên Wings |
| 14 | Không làm lộ secrets | `PASS (Static)` / `UNVERIFIED (Runtime)` | Đã kiểm chứng không mật khẩu yếu & tích hợp `vnh_redact`; CI `test-eggs.yml` kiểm chứng log thực tế |
| 15 | Không gây ảnh hưởng sang container khác | `UNVERIFIED` | Yêu cầu cấu hình Wings `enable_icc: false`, `container_pid_limit: 512` trên Node thật |
| 16 | Có thể phục hồi từ backup | `UNVERIFIED` | Kiểm chứng backup/restore thực tế trên Panel/Wings và dump DB |
| 17 | Kiểm tra trên AMD64 và ARM64 (nếu hỗ trợ) | `UNVERIFIED` | Chạy ma trận `linux/amd64,linux/arm64` trong `build-images.yml` và Node ARM64 staging |

## 3. Lộ trình chuyển từ `UNVERIFIED` sang `INTEGRATION_VERIFIED`

1. Kích hoạt GitHub Actions trên repository: chạy `.github/workflows/validate.yml`, `.github/workflows/security-scan.yml` và `.github/workflows/test-eggs.yml`.
2. Build & publish 90 Docker images bằng `.github/workflows/build-images.yml` lên GHCR (có xác nhận quản trị viên).
3. Triển khai Node Staging Ubuntu 24.04 LTS (AMD64 + ARM64) kèm Pterodactyl Panel 1.12 + Wings cấu hình từ `security/wings-hardening.yml`, kiểm thử từng hạng mục 1–17 và cập nhật `test.config.json` của từng Egg trước khi gắn nhãn production.
