# Kiến trúc NAT Linux Container Hosting — Vietnam Hosting

## 1. Mô hình kết nối NAT

```text
Internet
  └──► Public IP của Node (IPv4 / IPv6 theo cấu hình thực tế của Node)
         └──► Pterodactyl Allocation Port (Port riêng cho từng khách hàng)
                └──► Docker Container (Unprivileged user `container`, `/home/container`)
                       ├──► Pterodactyl Web Console (Interactive Shell)
                       ├──► Wings SFTP (Cổng 2022 của Node, cách ly thư mục `/home/container`)
                       ├──► User-Space SSH Daemon (Dropbear / Unprivileged OpenSSH trên SSH_PORT)
                       └──► Ứng dụng khách hàng & User-Space Scheduler (`~/crontab`)
```

## 2. Phân biệt bắt buộc: Linux Container vs. KVM VPS

Vietnam Hosting minh bạch hoàn toàn với khách hàng về sự khác biệt kỹ thuật:

| Tính năng | NAT Linux Container (Wings + PRoot Writable RootFS) | KVM VPS Thực Sự |
| :--- | :---: | :---: |
| Quyền `root@` trong container & cài đặt gói `apt` / `dnf` / `dpkg` bền vững | **Có** (qua PRoot rootfs trong `/home/container/rootfs`, an toàn không cần host root) | **Có** |
| Kernel riêng & nạp module kernel (`iptables`, WireGuard, TUN/TAP) | **Không** (chia sẻ kernel host) | **Có** |
| Chạy `systemd` đầy đủ (`systemctl` PID 1) | **Không** (dùng `tini` + process supervisor) | **Có** |
| Chạy Docker-in-Docker / mount Docker Socket | **Không** (bị chặn vì bảo mật multi-tenant) | **Có** |
| Terminal trực tiếp, SSH (`ubuntu@` + `readme.md` hot-reload), Wings SFTP, lưu trữ bền vững | **Có** | **Có** |
| Cài đặt công cụ user-space (`pip`, `uv`, `npm`, `cargo`, `go`, `mise`, binary tĩnh) | **Có** (trong `/home/container`) | **Có** |
| Chi phí & mật độ triển khai | Rất tối ưu cho ứng dụng & dev workspace | Cao hơn do ảo hóa phần cứng |

> [!WARNING]
> **Khuyến nghị sản phẩm:** Nếu khách hàng yêu cầu toàn quyền `root`, `systemd`, VPN kernel, firewall riêng hoặc chạy Docker bên trong máy chủ, hãy điều hướng sang dịch vụ **KVM VPS riêng biệt** thay vì nới lỏng bảo mật của Pterodactyl Wings.

## 3. Cơ chế SSH Không Đặc Quyền (`core/nat-ssh.sh`)

Vì OpenSSH `sshd` mặc định thường yêu cầu đặc quyền `root` cho privilege separation và `setuid`, Vietnam Hosting triển khai mô hình tương thích hoàn toàn với Wings tiêu chuẩn:

1. **Ưu tiên Dropbear SSH (`dropbear -F -E -g -w`) kết hợp `libnss-wrapper` không đặc quyền** trên cổng `SSH_PORT` (`0.0.0.0:${SSH_PORT}`):
   - `-w -g`: Cấm tuyệt đối đăng nhập `root` qua SSH.
   - **Tài khoản & mật khẩu quản lý qua `/home/container/readme.md`:** Mặc định khởi tạo `SSH_USER: ubuntu` (`ssh -p <PORT> ubuntu@<NODE_IP>`) và `PASSWORD: vietnam999`. Khi người dùng sửa dòng `PASSWORD:` trong `/home/container/readme.md` (qua File Manager của Panel, SFTP hoặc terminal), watcher của `core/nat-ssh.sh` sẽ tự động băm SHA-512 (`openssl passwd -6`) và cập nhật `/home/container/run/passwd` trong vòng **2 giây** (áp dụng ngay cho phiên SSH mới, không cần khởi động lại container).
   - **SSH Public Key song song:** Hỗ trợ đồng thời xác thực khóa công khai qua `~/.ssh/authorized_keys` / `SSH_AUTHORIZED_KEYS`, và có thể tắt mật khẩu hoàn toàn bằng `ENABLE_SSH_PASSWORD=0`.
   - Khóa host key Ed25519/ECDSA được sinh riêng cho từng container và lưu bền vững tại `/home/container/.ssh/host_keys/` (không thay đổi fingerprint khi restart).
2. **Fallback OpenSSH không đặc quyền** (`PermitRootLogin no`, `PasswordAuthentication no`, `UsePAM no`) cho các distro RPM không đóng gói Dropbear mặc định.
3. **Phương án thay thế an toàn nhất:** Nếu quản trị viên muốn tắt hoàn toàn SSH trong container (`ENABLE_SSH=0`), khách hàng vẫn quản lý toàn diện qua **Pterodactyl Web Console** và **Wings SFTP** mà không cần mở thêm tiến trình mạng.

## 4. Không can thiệp tầng mạng Host

- Module `core/nat-ssh.sh` và toàn bộ 15 Linux OS Eggs **tuyệt đối không** sửa `iptables`, `nftables`, routing table của Host và không tự mở port ngoài dải Allocation mà Pterodactyl cấp.
- Hỗ trợ IPv4 và IPv6 hoàn toàn phụ thuộc vào cấu hình Docker/Wings Network của Node.
