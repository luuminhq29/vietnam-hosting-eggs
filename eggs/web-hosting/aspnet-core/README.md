# Vietnam Hosting — ASP.NET Core Hosting

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `aspnet-core` | **Danh mục:** `web-hosting` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Production ASP.NET Core Kestrel hosting on .NET 10 LTS / 11 STS bound to http://0.0.0.0:{{SERVER_PORT}}.

- **Phiên bản hỗ trợ:** .NET 8.0, .NET 10.0 LTS, .NET 11.0 STS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://dotnet.microsoft.com/apps/aspnet (Giấy phép: `MIT`)

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
| .NET 10.0 LTS (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:dotnet_10` |
| .NET 11.0 STS (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:dotnet_11` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/dotnet/10/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `PROJECT_FILE` | Project File | `(trống)` | Có | `nullable|string|max:191` | Optional .csproj path to publish. |
| `APP_DLL` | Application DLL | `WebApp.dll` | Có | `required|string|max:191` | Compiled ASP.NET Core DLL. |
| `ASPNETCORE_ENVIRONMENT` | Environment | `Production` | Có | `required|string|in:Production,Staging,Development` | ASPNETCORE_ENVIRONMENT setting. |
| `GIT_ADDRESS` | Git Repository URL | `(trống)` | Có | `nullable|string|max:512` | Optional HTTPS Git repository URL to clone/pull on install or startup. |
| `BRANCH` | Git Branch | `(trống)` | Có | `nullable|string|max:128` | Git branch or tag to checkout (leave blank for repository default). |
| `USERNAME` | Git Username | `(trống)` | Có | `nullable|string|max:128` | Optional username for private HTTPS Git repositories. |
| `ACCESS_TOKEN` | Git Access Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Optional Personal Access Token for private repositories (never logged). |
| `AUTO_UPDATE` | Auto Update Git on Boot | `0` | Có | `required|boolean` | Set to 1 to run `git pull --ff-only` automatically before starting. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `export ASPNETCORE_URLS="http://0.0.0.0:{{SERVER_PORT}}" ASPNETCORE_ENVIRONMENT="${ASPNETCORE_ENVIRONMENT}"; if [[ -n "${PROJECT_FILE}" ]] && [[ -f "${PROJECT_FILE}" ]]; then dotnet publish "${PROJECT_FILE}" -c Release -o ./out --nologo; fi; if [[ -f "./out/${APP_DLL}" ]]; then exec dotnet "./out/${APP_DLL}"; else exec dotnet "./${APP_DLL}"; fi`
- **Stop Command:** `^C`
- **Startup Detection:** `Now listening on:|Application started`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Bind chuẩn container:** Ứng dụng luôn lắng nghe trên `0.0.0.0:{{SERVER_PORT}}` (không hardcode IP Node).
- **Reverse Proxy & Custom Domain:** Tên miền tùy chỉnh, TLS/HTTPS và Cloudflare Tunnel được quản lý ở tầng **Reverse Proxy / Ingress của nền tảng** do quản trị viên kiểm soát — container không bao giờ chỉnh sửa firewall hoặc Docker Network của host.
- **Health Check:** Cung cấp đường dẫn kiểm tra sức khỏe HTTP để reverse proxy giám sát trạng thái.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
