# Chính sách Bảo mật (Security Policy) — Vietnam Hosting Universal Eggs

## Phiên bản được hỗ trợ

| Phiên bản | Trạng thái hỗ trợ bảo mật |
| :--- | :---: |
| `1.x` (PTDL_v2 / Pterodactyl 1.11.x–1.12.x) | Đang hỗ trợ tích cực |

## Nguyên tắc bảo mật cốt lõi

1. **Không chạy đặc quyền (`--privileged`):** Mọi container chạy dưới user `container` không đặc quyền tại `/home/container`.
2. **Không dùng `eval` cho biến người dùng:** Entrypoint (`core/entrypoint.sh`) và toàn bộ script cài đặt loại bỏ hoàn toàn `eval` trên input không đáng tin cậy.
3. **Không lộ thông tin xác thực:** Module `core/environment.sh` (`vnh_redact`) che tự động token/password trong log và không sử dụng mật khẩu mặc định yếu.
4. **Không giả mạo bảo vệ tầng Host bằng Egg:** Giới hạn CPU, RAM, PID, Disk Quota, cô lập mạng (`enable_icc: false`) và chống DDoS được thực thi ở tầng **Pterodactyl Wings, Docker Daemon và Firewall/Edge Network** (xem `security/policy.md` và `security/wings-hardening.yml`).
5. **Quét lỗ hổng & SBOM:** Mọi Dockerfile và image được quét định kỳ bằng Trivy và xuất SBOM định dạng SPDX qua `.github/workflows/security-scan.yml`.

## Báo cáo lỗ hổng bảo mật

Nếu bạn phát hiện lỗ hổng bảo mật trong Egg JSON, Dockerfile hoặc Core Runtime Script:

- **Không** mở Public Issue chứa mã khai thác.
- Gửi báo cáo chi tiết về: `security@vietnam-hosting.net` (kèm đường dẫn file, kịch bản tái hiện và mức độ ảnh hưởng).
- Thời gian phản hồi cam kết: trong vòng **24–48 giờ làm việc**.
