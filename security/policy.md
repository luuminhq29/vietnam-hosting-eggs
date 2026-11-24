# Kiến trúc Bảo mật & Chống Lạm dụng (Multi-Tenant Shared Hosting)

> **Áp dụng cho:** Vietnam Hosting — Universal Pterodactyl Egg System  
> **Hệ điều hành Node:** Ubuntu 24.04 LTS + Docker + Pterodactyl Wings

## 1. Phân định ranh giới trách nhiệm (Egg vs. Wings/Docker vs. Host/Network)

Hệ thống Vietnam Hosting **không tạo cơ chế bảo mật giả** và không tuyên bố Egg có thể chống DDoS hay thay thế tường lửa hạ tầng. Mọi lớp phòng thủ được tách bạch rõ ràng:

| Kiểm soát bảo mật | Tầng Egg / Container | Tầng Wings / Docker Daemon | Tầng Host OS / Firewall / Network |
| :--- | :---: | :---: | :---: |
| Chạy ứng dụng không quyền `root` (`USER container`) | **Có** | Cưỡng chế UID/GID | Kernel user/mount namespace |
| Không dùng `eval` cho biến đầu vào người dùng | **Có** | — | — |
| Ẩn mật khẩu, token, API key khỏi log console | **Có** (`vnh_redact`) | — | — |
| Tải gói có HTTPS, timeout, retry, kiểm tra SHA256 | **Có** | — | — |
| Giới hạn số luồng biên dịch (`CARGO_BUILD_JOBS`, `MAKEFLAGS`) | **Có** | Cưỡng chế CPU cgroup | — |
| Chống vòng lặp khởi động lại (restart-loop cap) | **Có** (`vnh_supervise_exec`) | Crash detection Wings | — |
| Giới hạn CPU / RAM / Swap / OOM Killer | Hỗ trợ tính Heap JVM | **Cưỡng chế chính (cgroups v2)** | Kernel |
| Giới hạn số tiến trình (`container_pid_limit: 512`) | — | **Cưỡng chế chính** | Kernel |
| Hạn mức dung lượng đĩa (Disk Quota) | — | **Cưỡng chế chính** | XFS/Ext4/ZFS quota |
| Giới hạn kích thước log (`max-size: 10m`, `max-file: 3`) | — | **Cưỡng chế chính** | Logrotate |
| Cô lập mạng giữa các container (`enable_icc: false`) | — | **Cưỡng chế chính** | iptables / nftables |
| AppArmor / Seccomp / chặn `--privileged`, `CAP_SYS_ADMIN` | Không yêu cầu đặc quyền | **Cưỡng chế chính** | Linux Kernel LSM |
| Chống DDoS L3/L4/L7, Rate Limit kết nối, Reverse Proxy / Cloudflare Tunnel | Bind `0.0.0.0:{{SERVER_PORT}}` | Port allocation mapping | **Cưỡng chế chính (Edge/BGP/WAF/nftables)** |

## 2. Nguyên tắc bắt buộc trên mọi Egg Vietnam Hosting

1. **Rootless Application Execution:** Mọi runtime image chạy dưới user `container` tại `/home/container`, không bao giờ yêu cầu `privileged: true`, `CAP_SYS_ADMIN`, `host` network hoặc mount `/var/run/docker.sock`.
2. **Secret Protection:** Không nhúng mật khẩu/token trong Dockerfile hoặc Egg JSON; không có mật khẩu mặc định yếu (`admin`, `123456`, `password`, `root`); các Database Egg tự động sinh mật khẩu mạnh qua `openssl rand` với quyền file `0600`.
3. **Download Integrity:** Mọi Installation Script chỉ cho phép `https://`, có `--connect-timeout` và `--max-time`, giới hạn 3 lần retry, kiểm tra SHA256/SHA1 khi upstream cung cấp, và tuyệt đối không chạy `curl ... | sh`.
4. **Image Vulnerability Scanning & SBOM:** Quét định kỳ bằng Trivy (`.github/workflows/security-scan.yml`) và tạo SBOM định dạng SPDX cho mỗi image trước khi đưa lên production.
5. **NAT Linux Container vs. KVM VPS:** Khách hàng cần toàn quyền `root`, `systemd`, tải module kernel, VPN TUN/TAP hoặc chạy Docker-in-Docker phải được định tuyến sang sản phẩm **KVM VPS** riêng biệt của Vietnam Hosting.
