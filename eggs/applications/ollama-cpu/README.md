# Vietnam Hosting — Ollama CPU Inference Server

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `ollama-cpu` | **Danh mục:** `applications` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Stable` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

CPU-only Ollama 0.6 local LLM inference server storing models in /home/container/.ollama/models (GPU acceleration is NOT enabled by default).

- **Phiên bản hỗ trợ:** 0.6.2 (CPU Only)
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://ollama.com (Giấy phép: `MIT`)

## 2. Yêu cầu tài nguyên (Khuyến nghị)

> [!NOTE]
> Các thông số dưới đây là **giá trị khuyến nghị ước lượng cho vận hành sản xuất**, không phải kết quả benchmark trực tiếp trên phần cứng khách hàng cụ thể. Quản trị viên cần điều chỉnh theo lưu lượng thực tế.

| Tài nguyên | Mức tối thiểu | Mức khuyến nghị |
| :--- | :---: | :---: |
| RAM | 4096 MiB | 8192 MiB |
| Ổ cứng | 16384 MiB | ≥ 32768 MiB |

## 3. Docker Images

| Nhãn hiển thị | Docker Image |
| :--- | :--- |
| Ollama CPU 0.6 (Vietnam Hosting GHCR) | `ghcr.io/vietnam-hosting/yolks:ollama_cpu_0.6` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/services/ollama-cpu/Dockerfile`. Các tag `ghcr.io/vietnam-hosting/yolks:*` là tên registry dự kiến — quản trị viên cần build & publish bằng `.github/workflows/build-images.yml` hoặc `vnh-egg build` trước khi sử dụng trên production.

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `BIND_ADDRESS` | Bind Address | `127.0.0.1` | Không | `required|string|in:127.0.0.1,0.0.0.0` | Default 127.0.0.1 (admin may enable 0.0.0.0 behind auth proxy — Ollama has no built-in auth!). |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `export OLLAMA_HOST="${BIND_ADDRESS}:{{SERVER_PORT}}" OLLAMA_MODELS=/home/container/.ollama/models OLLAMA_NUM_PARALLEL=1; exec ollama serve`
- **Stop Command:** `^C`
- **Startup Detection:** `Listening on`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Cảnh báo bảo mật:** Ollama không có lớp xác thực tích hợp sẵn. Mặc định bind `127.0.0.1` — quản trị viên tuyệt đối không mở trực tiếp ra Internet nếu không có Reverse Proxy xác thực.
- **Chế độ CPU:** Egg này chỉ chạy suy luận CPU. Tăng tốc GPU yêu cầu Node chuyên dụng được quản trị viên cấu hình NVIDIA/ROCm riêng.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Sử dụng tính năng Backup tích hợp của Pterodactyl Panel/Wings để nén `/home/container`.
- Khuyến nghị dừng dịch vụ (Graceful Stop) trước khi sao lưu dữ liệu trạng thái hoặc dùng công cụ dump nhất quán nếu là cơ sở dữ liệu.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
