# Vietnam Hosting — Node.js Hosting

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `nodejs` | **Danh mục:** `languages` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Production Node.js runtime (20/22/24/26) supporting NPM, Yarn, PNPM, JavaScript/TypeScript, Discord.js, Express, NestJS, Next.js, Nuxt.js, lockfiles, native addons, and build commands without nodemon.

- **Phiên bản hỗ trợ:** 20 (Legacy), 22 LTS, 24 LTS, 26 Active LTS
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Official Yolks mặc định + Dockerfile GHCR Vietnam Hosting tùy chọn build
- **Dự án upstream:** https://nodejs.org (Giấy phép: `MIT`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 256 MiB | 512 MiB |
| Ổ cứng | 1024 MiB | ≥ 2048 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Node.js 24 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:nodejs_24` |
| Node.js 22 LTS (Official Yolk) | `ghcr.io/pterodactyl/yolks:nodejs_22` |
| Node.js 20 Legacy (Official Yolk) | `ghcr.io/pterodactyl/yolks:nodejs_20` |
| Node.js 26 LTS (Vietnam Hosting GHCR - Build Required) | `ghcr.io/vietnam-hosting/yolks:nodejs_26` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/languages/nodejs/24/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `MAIN_FILE` | Main JS File | `index.js` | Có | `required|string|max:128` | Entrypoint JS file when START_SCRIPT is empty. |
| `PACKAGE_MANAGER` | Package Manager | `auto` | Có | `required|string|in:auto,npm,yarn,pnpm` | Package manager: auto, npm, yarn, or pnpm. |
| `BUILD_SCRIPT` | NPM Build Script | `(trống)` | Có | `nullable|string|max:64` | Optional package.json script name to run before start (e.g. build). |
| `START_SCRIPT` | NPM Start Script | `(trống)` | Có | `nullable|string|max:64` | Optional package.json script name to execute (e.g. start). Leave blank to run MAIN_FILE. |
| `INSTALL_DEPS` | Install Dependencies on Boot | `1` | Có | `required|boolean` | Set to 1 to install dependencies from lockfile/package.json. |
| `NODE_ENV` | Node Environment | `production` | Có | `required|string|in:production,staging,development` | Runtime NODE_ENV (production recommended; never uses nodemon). |
| `GIT_ADDRESS` | Git Repository URL | `(trống)` | Có | `nullable|string|max:512` | Optional HTTPS Git repository URL to clone/pull on install or startup. |
| `BRANCH` | Git Branch | `(trống)` | Có | `nullable|string|max:128` | Git branch or tag to checkout (leave blank for repository default). |
| `USERNAME` | Git Username | `(trống)` | Có | `nullable|string|max:128` | Optional username for private HTTPS Git repositories. |
| `ACCESS_TOKEN` | Git Access Token | `(bí mật / để trống)` | Có | `nullable|string|max:256` | Optional Personal Access Token for private repositories (never logged). |
| `AUTO_UPDATE` | Auto Update Git on Boot | `0` | Có | `required|boolean` | Set to 1 to run `git pull --ff-only` automatically before starting. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `export NODE_ENV="${NODE_ENV:-production}"; if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then   if [[ "${PACKAGE_MANAGER}" == "pnpm" ]] || { [[ "${PACKAGE_MANAGER}" == "auto" ]] && [[ -f pnpm-lock.yaml ]]; }; then pnpm install --frozen-lockfile || pnpm install;   elif [[ "${PACKAGE_MANAGER}" == "yarn" ]] || { [[ "${PACKAGE_MANAGER}" == "auto" ]] && [[ -f yarn.lock ]]; }; then yarn install --frozen-lockfile || yarn install;   elif [[ -f package-lock.json ]]; then npm ci --omit=dev || npm install --omit=dev;   else npm install --omit=dev; fi; fi; if [[ -n "${BUILD_SCRIPT}" ]] && [[ -f package.json ]]; then npm run "${BUILD_SCRIPT}"; fi; if [[ -n "${START_SCRIPT}" ]] && [[ -f package.json ]]; then exec npm run "${START_SCRIPT}"; else exec node "${MAIN_FILE}"; fi`
- **Stop Command:** `^C`
- **Startup Detection:** `Listening on|Ready in|Server running|Logged in as|VIETNAM HOSTING`

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
