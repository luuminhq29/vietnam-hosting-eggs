# Tài liệu Egg Catalog API — Tích hợp Admin Dashboard Vietnam Hosting

Hệ thống cung cấp đồng thời **Static JSON Catalog API** (không tốn tài nguyên server) và **HTTP JSON API / CLI tìm kiếm cục bộ** (`scripts/catalog-search.py`).

## 1. Các tệp Static Catalog API

Được tự động sinh mỗi lần chạy `vnh-egg generate`:

- `catalog.json` / `docs/catalog-api/index.json`: Toàn bộ 147 Egg kèm đầy đủ metadata, yêu cầu RAM/Disk khuyến nghị, kiến trúc CPU, trạng thái (`Stable`, `Beta`, `Experimental`, `Legacy`, `Deprecated`) và `verification_status`.
- `docs/catalog-api/categories/<category>.json`: Danh sách lọc sẵn theo từng danh mục (`languages`, `operating-systems`, `discord-bots`, `web-hosting`, `databases`, `game-servers`, `applications`, `utilities`).
- `docs/catalog-api/architectures/amd64.json` & `arm64.json`: Danh sách lọc sẵn theo kiến trúc CPU của Node.
- `compatibility.json`: Ma trận tương thích chi tiết để Dashboard tự động ẩn các Egg chỉ hỗ trợ AMD64 khi khách hàng chọn Node ARM64.

## 2. Tra cứu qua CLI & Chạy HTTP Catalog API

```bash
# Lọc tất cả Egg Game Server hỗ trợ ARM64
python3 scripts/catalog-search.py --category game-servers --arch arm64

# Tìm kiếm theo từ khóa & phiên bản
python3 scripts/catalog-search.py --search python --version 3.14

# Khởi chạy Read-Only JSON API Server cho Admin Dashboard nội bộ
python3 scripts/catalog-search.py --serve --host 127.0.0.1 --port 8090
```

### Các Endpoint của HTTP API:

- `GET /healthz` — Kiểm tra trạng thái dịch vụ và tổng số Egg.
- `GET /api/v1/categories` — Số lượng Egg theo từng danh mục.
- `GET /api/v1/eggs?category=databases&arch=arm64&status=Stable&version=17&q=postgres` — Tìm kiếm và lọc đa điều kiện.
- `GET /api/v1/eggs/<id>` — Chi tiết một Egg cụ thể (ví dụ `/api/v1/eggs/minecraft-paper`).

## 3. Lưu ý về thông số tài nguyên

Trường `resource_basis` trong mỗi mục Catalog ghi rõ nguồn gốc số liệu:
- `recommended_estimate`: Giá trị khuyến nghị vận hành ước lượng.
- `upstream_documented`: Thông số tối thiểu trích dẫn từ tài liệu nhà phát triển upstream.
- `benchmarked`: Chỉ sử dụng khi đội ngũ Vietnam Hosting đã thực sự đo benchmark trên phần cứng thực tế.
