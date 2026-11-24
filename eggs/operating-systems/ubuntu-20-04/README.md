# Vietnam Hosting — Ubuntu 20.04 Legacy (NAT Linux Container)

> **Nhà cung cấp:** Vietnam Hosting ([https://vietnam-hosting.net](https://vietnam-hosting.net))  
> **Mã Egg:** `ubuntu-20-04` | **Danh mục:** `operating-systems` | **Phiên bản:** `1.0.0`  
> **Trạng thái:** `Legacy` | **Kiểm thử tích hợp:** `UNVERIFIED (Static Validated)`  
> **Định dạng Schema:** `PTDL_v2` (`egg.json` — Pterodactyl 1.7–1.12+) & `PTDL_v1` (`egg-ptdl-v1.json` — Pterodactyl 1.0–1.6+ tương thích ngược)

## 1. Tổng quan

Unprivileged Ubuntu 20.04 Legacy NAT Linux container compatible with Pterodactyl Console, Wings SFTP, user-space SSH (pubkey-only), persistent storage, and container-safe task scheduling. Not a KVM VPS (no root/systemd/privileged mode). Standard support ended May 2025 (ESM only). Migrate to Ubuntu 24.04 or 26.04 LTS for new workloads.

- **Phiên bản hỗ trợ:** 20.04 LTS (ESM Legacy)
- **Kiến trúc CPU:** AMD64, ARM64
- **Cổng mạng inbound:** Có (bind `0.0.0.0:{{SERVER_PORT}}` theo allocation)
- **Nguồn Docker Image:** Custom Vietnam Hosting Dockerfile (cần build & publish lên GHCR trước khi triển khai)
- **Dự án upstream:** https://ubuntu.com (Giấy phép: `GPL/Ubuntu-Main`)

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
| Ubuntu 20.04 Legacy (Vietnam Hosting GHCR) | `ghcr.io/luuminhq29/yolks:ubuntu_20.04` |

> [!IMPORTANT]
> Dockerfile nguồn được cung cấp tại `docker/linux/ubuntu-20.04/Dockerfile`. Image đích trên GHCR: `ghcr.io/luuminhq29/yolks:*` (build & publish qua `.github/workflows/build-images.yml` hoặc `vnh-egg build`).

## 4. Biến môi trường (Egg Variables)

| Biến (`env_variable`) | Tên hiển thị | Mặc định | Chỉnh sửa | Quy tắc (`rules`) | Mô tả |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `ENABLE_SSH` | Enable Unprivileged SSH | `1` | Có | `required|boolean` | Set to 1 to start user-space Dropbear/OpenSSH daemon on SSH_PORT (root login always disabled). |
| `ENABLE_SSH_PASSWORD` | Enable readme.md Password SSH | `(bí mật / để trống)` | Có | `required|boolean` | Set to 1 to allow NAT SSH password login synced live from /home/container/readme.md (default ubuntu / vietnam999). Set 0 for pubkey-only. |
| `AUTO_RANDOM_SSH_PASSWORD` | Auto-Generate Random SSH Password | `(bí mật / để trống)` | Có | `required|boolean` | Set to 1 (recommended for commercial hosting) to generate a unique strong random password per server in readme.md instead of vietnam999. |
| `SSH_PORT` | SSH Allocation Port | `(trống)` | Có | `nullable|integer|between:1024,65535` | Dedicated Pterodactyl allocation port for SSH (leave blank to reuse SERVER_PORT). |
| `SSH_AUTHORIZED_KEYS` | SSH Authorized Public Key | `(bí mật / để trống)` | Có | `nullable|string|max:2048` | OpenSSH public key (ssh-ed25519 / ssh-rsa) added to ~/.ssh/authorized_keys. |
| `ENABLE_PROOT` | Enable Writable PRoot RootFS (VPS Mode) | `1` | Có | `required|boolean` | Set to 1 to enter persistent writable /home/container/rootfs via unprivileged PRoot (enables apt/dnf install as virtual root while keeping host isolated). |
| `ENABLE_CRON` | Enable User-Space Scheduler | `1` | Có | `required|boolean` | Set to 1 to enable container-safe scheduled tasks from ~/crontab. |
| `STARTUP_SCRIPT` | User Startup Script | `startup.sh` | Có | `nullable|string|max:128` | Relative path to user startup script managed with restart-loop protection. |
| `VNH_MAX_RESTARTS` | Max Restart Attempts | `5` | Có | `required|integer|between:1,20` | Maximum restarts within 60 seconds before halting to prevent restart loops. |

## 5. Lệnh khởi động & Dừng an toàn

- **Startup Command:** `if [[ -x /opt/vnh/nat-ssh.sh ]]; then exec /bin/bash /opt/vnh/nat-ssh.sh; else echo "VIETNAM HOSTING CONTAINER READY (Fallback Shell)"; exec /bin/bash; fi`
- **Stop Command:** `shutdown`
- **Startup Detection:** `VIETNAM HOSTING CONTAINER READY`

## 6. Hành vi Cài đặt, Khởi động lại & Reinstall

- **Cài đặt lần đầu:** Thiết lập môi trường trong `/mnt/server`, tải thành phần cần thiết (nếu có) với timeout/retry và tạo file đánh dấu `.vnh_installed`.
- **Khởi động lại (Restart):** Không ghi đè dữ liệu người dùng hoặc cấu hình hiện có trong `/home/container`.
- **Cài đặt lại (Reinstall):** Phát hiện `.vnh_installed` và bảo toàn dữ liệu người dùng mặc định; chỉ cập nhật binary/dependencies theo cấu hình biến môi trường.

## 7. Ranh giới bảo mật & Vận hành

- **Phân biệt rõ Container và KVM VPS:** Container vẫn chạy hoàn toàn **không đặc quyền trên máy chủ Node** (`Privileged=false`, `ReadonlyRootfs=true`, không `CAP_SYS_ADMIN`, không Docker Socket, không tắt AppArmor/Seccomp).
- **Chế độ PRoot Writable RootFS (`ENABLE_PROOT=1`):** Ở lần khởi động đầu tiên, hệ thống khởi tạo bản sao rootfs có thể ghi bền vững tại `/home/container/rootfs` bằng **PRoot user-space**. Người dùng đăng nhập vào `root@vietnam-hosting:~#`, có thể chạy trực tiếp `apt update && apt install ...`, sửa `/etc`, `/usr`, `/var` như VPS thông thường và giữ nguyên gói đã cài sau khi restart — mà **không cần quyền root thật trên Host**.
- **Giới hạn kỹ thuật minh bạch:** Vì vẫn dùng chung kernel máy chủ Node, các tính năng tầng kernel (`systemd` PID 1, nạp kernel module, `iptables`, WireGuard/OpenVPN TUN, Docker-in-Docker) cần sử dụng dịch vụ **KVM VPS riêng biệt** của Vietnam Hosting.
- **Đăng nhập NAT SSH qua `readme.md`:** Tài khoản mặc định `ubuntu` (`ssh -p <PORT> ubuntu@<NODE_IP>`) với mật khẩu mặc định `vietnam999` tại `/home/container/readme.md` (cũng mount vào `/root/readme.md`). Sửa dòng `PASSWORD:` trong `readme.md` tự động đổi mật khẩu SSH NAT ngay lập tức (2 giây, không cần restart). Tài khoản `root` qua SSH luôn bị chặn ở tầng đăng nhập.

- Container chạy không đặc quyền (`container` user, `/home/container`), không yêu cầu `--privileged`, không mount Docker Socket, không dùng `host` network và không thay đổi firewall/iptables của Node.
- Giới hạn CPU, RAM, PID, Disk Quota và bảo vệ mạng tầng Host do **Pterodactyl Wings, Docker Daemon và Firewall của Node** đảm nhiệm.
- Không hiển thị mật khẩu, token hoặc API key ra console.

## 8. Sao lưu và Phục hồi (Backup & Restore)

- Toàn bộ dữ liệu người dùng, khóa SSH (`/home/container/.ssh/host_keys`), script và ứng dụng user-space nằm trong `/home/container`.
- Sao lưu trực tiếp qua Pterodactyl Panel Backup hoặc rsync/SFTP qua Wings.

## 9. Trạng thái kiểm thử

- Kiểm tra tĩnh (Schema `PTDL_v2`, kiểm tra biến môi trường, kiểm tra cú pháp script): Chạy bằng `vnh-egg validate`.
- Kiểm tra tích hợp thực tế trên Pterodactyl Panel / Wings & Docker runtime: `UNVERIFIED (Static Validated)` (xem chi tiết tại `test.config.json` và `docs/TEST_REPORT.md`).
