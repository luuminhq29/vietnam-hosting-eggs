# Vietnam Hosting — Swift Hosting

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `swift` | **Danh mục:** `languages` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Server-side Swift 6.1 hosting (Vapor/Hummingbird ready) with Swift Package Manager and release builds.

- **Phiên bản hỗ trợ:** 6.1
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://www.swift.org (Giấy phép: `Apache-2.0`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 1024 MiB | 2048 MiB |
| Ổ cứng | 2048 MiB | ≥ 4096 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Swift 6.1 (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:swift_6.1` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/swift/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `BIN_NAME` | Executable Name | `App` | Có | `required|string|max:128` | SwiftPM release binary name under .build/release/. |
| `MAIN_FILE` | Fallback Swift File | `main.swift` | Có | `required|string|max:128` | Swift script when Package.swift is absent. |
| `AUTO_BUILD` | Auto Build Release | `1` | Có | `required|boolean` | Compile with `swift build -c release` on boot. |
| `BUILD_JOBS` | Build Jobs | `2` | Có | `required|integer|between:1,4` | Maximum parallel Swift compilation jobs. |
| `GIT_ADDRESS` | Git Repository URL | `(trống)` | Có | `nullable|string|max:512` | Optional HTTPS Git repository URL to clone/pull on install or startup. |
| `BRANCH` | Git Branch | `(trống)` | Có | `nullable|string|max:128` | Git branch or tag to checkout (leave blank for repository default). |
| `USERNAME` | Git Username | `(trống)` | Có | `nullable|string|max:128` | Optional username for private HTTPS Git repositories. |
| `ACCESS_TOKEN` | Git Access Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Optional Personal Access Token for private repositories (never logged). |
| `AUTO_UPDATE` | Auto Update Git on Boot | `0` | Có | `required|boolean` | Set to 1 to run `git pull --ff-only` automatically before starting. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `if [[ -f Package.swift ]] && [[ "${AUTO_BUILD}" == "1" ]]; then swift build -c release -j "${BUILD_JOBS}"; fi; if [[ -x ".build/release/${BIN_NAME}" ]]; then exec ".build/release/${BIN_NAME}"; else exec swift "${MAIN_FILE}"; fi`
- **Stop Command:** `^C`
- **Startup Detection:** `Server starting|Listening|Ready|VIETNAM HOSTING`

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
