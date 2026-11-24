# Hướng dẫn Đóng góp (Contributing) — Vietnam Hosting Universal Eggs

Cảm ơn bạn đã quan tâm đóng góp vào hệ sinh thái **Vietnam Hosting Universal Pterodactyl Eggs**.

## Quy trình thêm Runtime hoặc Egg mới (Không cần sửa source core)

Hệ thống CLI `vnh-egg` hỗ trợ mở rộng khai báo Egg mới trong `generator/specs/custom/*.json`:

1. Khởi tạo cấu hình Egg mới:
   ```bash
   python3 -m generator create my-runtime --category languages --image ghcr.io/pterodactyl/yolks:debian
   ```
2. Chỉnh sửa file JSON vừa sinh tại `generator/specs/custom/my-runtime.json`.
3. Sinh đầy đủ file Egg, `install.sh`, `README.md`, `metadata.json`, `catalog.json`:
   ```bash
   python3 -m generator generate
   ```
4. Chạy kiểm tra nghiêm ngặt trước khi mở Pull Request:
   ```bash
   python3 -m generator validate --strict
   python3 -m unittest discover -s tests -v
   ```

## Tiêu chuẩn bắt buộc cho mọi Pull Request

- Tuân thủ chính xác schema `PTDL_v2` (`schemas/ptdl_v2.schema.json`), không thêm trường JSON ngoài chuẩn Pterodactyl.
- Không sử dụng tag `:latest` thiếu kiểm soát trong `Dockerfile` hoặc `docker_images`.
- Không sử dụng `eval` trên input người dùng, không dùng `curl | sh`, không đặt mật khẩu mặc định yếu.
- Ghi rõ kiến trúc CPU được hỗ trợ thực tế (`amd64` vs `arm64`); không tuyên bố hỗ trợ `arm64` nếu upstream không phát hành bản biên dịch chính thức.
- Không tuyên bố `PASS` cho kiểm thử runtime/Pterodactyl nếu chưa thực sự kiểm thử trên môi trường thật; giữ nguyên trạng thái `UNVERIFIED` cho tới khi xác nhận thực tế.
- Source code và comment kỹ thuật bằng tiếng Anh; tài liệu hướng dẫn và README bằng tiếng Việt.
