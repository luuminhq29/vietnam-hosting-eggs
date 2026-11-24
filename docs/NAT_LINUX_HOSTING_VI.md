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

| Tính năng | NAT Linux Container (Pterodactyl Wings) | KVM VPS Thực Sự |
| :--- | :---: | :---: |
| Kernel riêng & nạp module kernel (`iptables`, WireGuard, TUN/TAP) | **Không** (chia sẻ kernel host) | **Có** |
| Toàn quyền `root` hệ thống & chạy `apt install` / `dnf install` runtime | **Không** (gói hệ thống cài lúc build image) | **Có** |
| Chạy `systemd` đầy đủ (`systemctl`) | **Không** (dùng `tini` + process supervisor) | **Có** |
| Chạy Docker-in-Docker / mount Docker Socket | **Không** (bị chặn vì bảo mật multi-tenant) | **Có** |
| Terminal trực tiếp, SSH Public Key, Wings SFTP, lưu trữ bền vững | **Có** | **Có** |
| Cài đặt công cụ user-space (`pip`, `uv`, `npm`, `cargo`, `go`, `mise`, binary tĩnh) | **Có** (trong `/home/container`) | **Có** |
| Chi phí & mật độ triển khai | Rất tối ưu cho ứng dụng & dev workspace | Cao hơn do ảo hóa phần cứng |

> [!WARNING]
> **Khuyến nghị sản phẩm:** Nếu khách hàng yêu cầu toàn quyền `root`, `systemd`, VPN kernel, firewall riêng hoặc chạy Docker bên trong máy chủ, hãy điều hướng sang dịch vụ **KVM VPS riêng biệt** thay vì nới lỏng bảo mật của Pterodactyl Wings.

## 3. Cơ chế SSH Không Đặc Quyền (`core/nat-ssh.sh`)

Vì OpenSSH `sshd` mặc định thường yêu cầu đặc quyền `root` cho privilege separation và `setuid`, Vietnam Hosting triển khai mô hình tương thích hoàn toàn với Wings tiêu chuẩn:

1. **Ưu tiên Dropbear SSH (`dropbear -F -E -s -g -w`)** chạy hoàn toàn dưới user `container` trên cổng `SSH_PORT` (`0.0.0.0:${SSH_PORT}`):
   - `-w`: Cấm đăng nhập `root`.
   - `-s -g`: Tắt đăng nhập bằng mật khẩu mặc định — **chỉ chấp nhận SSH Public Key Authentication**.
   - Khóa host key Ed25519/ECDSA được sinh riêng cho từng container và lưu bền vững tại `/home/container/.ssh/host_keys/` (không thay đổi fingerprint khi restart).
2. **Fallback OpenSSH không đặc quyền** (`PermitRootLogin no`, `PasswordAuthentication no`, `UsePAM no`) cho các distro RPM không đóng gói Dropbear mặc định.
3. **Phương án thay thế an toàn nhất:** Nếu quản trị viên muốn tắt hoàn toàn SSH trong container (`ENABLE_SSH=0`), khách hàng vẫn quản lý toàn diện qua **Pterodactyl Web Console** và **Wings SFTP** mà không cần mở thêm tiến trình mạng.

## 4. Không can thiệp tầng mạng Host

- Module `core/nat-ssh.sh` và toàn bộ 15 Linux OS Eggs **tuyệt đối không** sửa `iptables`, `nftables`, routing table của Host và không tự mở port ngoài dải Allocation mà Pterodactyl cấp.
- Hỗ trợ IPv4 và IPv6 hoàn toàn phụ thuộc vào cấu hình Docker/Wings Network của Node.
