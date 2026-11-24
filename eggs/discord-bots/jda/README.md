# Vietnam Hosting — JDA Discord Bot (Java)

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `jda` | **Danh mục:** `discord-bots` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Java Discord API (JDA) bot hosting with automatic JVM heap headroom, Maven/Gradle build, and Git deployment.

- **Phiên bản hỗ trợ:** Java 17, Java 21 LTS, Java 25 LTS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Không bắt buộc (ứng dụng kết nối outbound)
- **Nguồn Docker Image:** Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build
- **Dự án upstream:** https://github.com/discord-jda/JDA (Giấy phép: `Apache-2.0`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 512 MiB | 1024 MiB |
| Ổ cứng | 1024 MiB | ≥ 2048 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Java 21 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_21` |
| Java 25 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_25` |
| Java 17 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_17` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/java/21/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `BOT_JAR` | Bot JAR File | `bot.jar` | Có | `required|string|max:128` | Executable JDA JAR filename. |
| `DISCORD_TOKEN` | Discord Bot Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Bot token passed to JVM via DISCORD_TOKEN env var. |
| `GIT_ADDRESS` | Git Repository URL | `(trống)` | Có | `nullable|string|max:512` | Optional HTTPS Git repository URL to clone/pull on install or startup. |
| `BRANCH` | Git Branch | `(trống)` | Có | `nullable|string|max:128` | Git branch or tag to checkout (leave blank for repository default). |
| `USERNAME` | Git Username | `(trống)` | Có | `nullable|string|max:128` | Optional username for private HTTPS Git repositories. |
| `ACCESS_TOKEN` | Git Access Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Optional Personal Access Token for private repositories (never logged). |
| `AUTO_UPDATE` | Auto Update Git on Boot | `0` | Có | `required|boolean` | Set to 1 to run `git pull --ff-only` automatically before starting. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; exec java -Xms128M -Xmx"${HEAP}M" -XX:+UseG1GC -jar "${BOT_JAR}"`
- **Stop Command:** `^C`
- **Startup Detection:** `Finished Loading!|Login Successful|Ready|VIETNAM HOSTING`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Bảo vệ Token / API Key:** Token Bot (`DISCORD_TOKEN` / `TELEGRAM_BOT_TOKEN` / `BOT_TOKEN`) được truyền qua biến môi trường và tuyệt đối không được in ra console.
- **Tuân thủ Rate Limit & Chính sách nền tảng:** Không tự động đổi IP để né lệnh cấm API; áp dụng cơ chế reconnect với exponential backoff chống vòng lặp lỗi.
- **Outbound-Only:** Không yêu cầu mở port inbound bổ sung nếu bot chỉ kết nối outbound tới Discord/Telegram Gateway.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
