# Vietnam Hosting — Minecraft Spigot (Official BuildTools)

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `minecraft-spigot` | **Danh mục:** `game-servers` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Official SpigotMC server compiled legally on-demand using SpigotMC BuildTools (never redistributes prebuilt Spigot JARs).

- **Phiên bản hỗ trợ:** 1.20.x, 1.21.x, latest
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build
- **Dự án upstream:** https://www.spigotmc.org (Giấy phép: `GPL-3.0 / CraftBukkit`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 1536 MiB | 3072 MiB |
| Ổ cứng | 6144 MiB | ≥ 12288 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Java 21 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_21` |
| Java 25 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_25` |
| Java 17 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_17` |
| Java 11 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_11` |
| Java 8 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_8` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/java/21/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `DL_VERSION` | Spigot Version | `latest` | Có | `required|string|max:32` | Minecraft revision for BuildTools (e.g. latest or 1.21.4). |
| `SERVER_JARFILE` | Server JAR File | `server.jar` | Có | `required|string|max:128` | Target JAR filename. |
| `JVM_OVERHEAD_MB` | JVM Off-Heap Reserve (MiB) | `512` | Có | `required|integer|between:128,4096` | Off-heap memory reserve. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `MEM={{SERVER_MEMORY}}; OVERHEAD=${JVM_OVERHEAD_MB:-512}; HEAP=$(( MEM - OVERHEAD )); (( HEAP < 512 )) && HEAP=$(( MEM * 80 / 100 )); (( HEAP < 256 )) && HEAP=256; exec java -Xms256M -Xmx"${HEAP}M" -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -Dterminal.jline=false -Dterminal.ansi=true -jar "${SERVER_JARFILE}" nogui`
- **Stop Command:** `stop`
- **Startup Detection:** `)! For help, type `

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- Chạy hoàn toàn trong không gian người dùng không đặc quyền (`container`).
- Mọi token/mật khẩu phải truyền qua biến môi trường, tuyệt đối không commit vào Git hoặc in ra log.
- **Yêu cầu EULA:** Người dùng phải đồng ý điều khoản giấy phép (EULA) của nhà phát triển upstream trước khi vận hành.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
