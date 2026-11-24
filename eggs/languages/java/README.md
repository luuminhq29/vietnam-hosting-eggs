# Vietnam Hosting — Java Hosting

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `java` | **Danh mục:** `languages` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Multi-version Java hosting (Eclipse Temurin / OpenJDK 8, 11, 17, 21, 25) with Maven/Gradle support, Spring Boot compatibility, and automatic JVM heap tuning reserving off-heap/metaspace headroom.

- **Phiên bản hỗ trợ:** 8, 11, 17, 21 LTS, 25 LTS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build
- **Dự án upstream:** https://adoptium.net (Giấy phép: `GPL-2.0-with-classpath-exception`)

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
| Java 25 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_25` |
| Java 21 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_21` |
| Java 17 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_17` |
| Java 11 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_11` |
| Java 8 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:java_8` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/java/21/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `SERVER_JARFILE` | Application JAR File | `app.jar` | Có | `required|string|max:191` | Path to the executable JAR file inside /home/container. |
| `BUILD_TOOL` | Build Tool | `none` | Có | `required|string|in:none,maven,gradle` | Optional pre-start build tool: none, maven, or gradle. |
| `JVM_OVERHEAD_MB` | Off-Heap Reserved RAM (MiB) | `256` | Có | `required|integer|between:64,4096` | RAM reserved for Metaspace, CodeCache, and OS overhead. |
| `JVM_HEAP_PERCENT` | Max Heap Percentage | `75` | Có | `required|integer|between:30,85` | Maximum percentage of SERVER_MEMORY allocated to JVM -Xmx. |
| `GIT_ADDRESS` | Git Repository URL | `(trống)` | Có | `nullable|string|max:512` | Optional HTTPS Git repository URL to clone/pull on install or startup. |
| `BRANCH` | Git Branch | `(trống)` | Có | `nullable|string|max:128` | Git branch or tag to checkout (leave blank for repository default). |
| `USERNAME` | Git Username | `(trống)` | Có | `nullable|string|max:128` | Optional username for private HTTPS Git repositories. |
| `ACCESS_TOKEN` | Git Access Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Optional Personal Access Token for private repositories (never logged). |
| `AUTO_UPDATE` | Auto Update Git on Boot | `0` | Có | `required|boolean` | Set to 1 to run `git pull --ff-only` automatically before starting. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `MEM={{SERVER_MEMORY}}; OVERHEAD=${JVM_OVERHEAD_MB:-256}; PCT=${JVM_HEAP_PERCENT:-75}; HEAP_PCT=$(( MEM * PCT / 100 )); HEAP_SUB=$(( MEM - OVERHEAD )); HEAP=$(( HEAP_SUB < HEAP_PCT ? HEAP_SUB : HEAP_PCT )); (( HEAP < 128 )) && HEAP=128; if [[ "${BUILD_TOOL}" == "maven" ]] && [[ -f pom.xml ]]; then mvn -B -DskipTests package; elif [[ "${BUILD_TOOL}" == "gradle" ]] && [[ -x ./gradlew ]]; then ./gradlew bootJar --no-daemon || ./gradlew build -x test --no-daemon; fi; exec java -Xms128M -Xmx"${HEAP}M" -XX:+UseG1GC -Dserver.address=0.0.0.0 -Dserver.port={{SERVER_PORT}} -jar "${SERVER_JARFILE}"`
- **Stop Command:** `^C`
- **Startup Detection:** `Started |Listening on|Done|VIETNAM HOSTING`

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
