# Ma trận Tương thích — Vietnam Hosting Universal Eggs

> Dữ liệu chi tiết dạng máy đọc được duy trì tự động tại [`compatibility.json`](../compatibility.json).

## 1. Tổng hợp tương thích kiến trúc CPU (147 Eggs)

| Chỉ số | Số lượng | Ghi chú kỹ thuật |
| :--- | :---: | :--- |
| **Tổng số Eggs** | **147** | Đầy đủ 8 danh mục |
| **Hỗ trợ AMD64 (`x86_64`)** | **147 / 147** | 100% tương thích Node Ubuntu 24.04 AMD64 |
| **Hỗ trợ ARM64 (`aarch64`)** | **131 / 147** | Không tuyên bố giả lập ARM64 cho binary chỉ có x86_64 |
| **Chỉ hỗ trợ AMD64** | **16 / 147** | Xem danh sách cụ thể bên dưới |
| **Chạy không đặc quyền (Unprivileged Wings)** | **147 / 147** | Không yêu cầu `--privileged`, `CAP_SYS_ADMIN` hay Docker Socket |

## 2. Danh sách 16 Egg chỉ hỗ trợ AMD64 (Không hỗ trợ ARM64 gốc)

1. `operating-systems/arch-linux` — Official Docker Hub `archlinux:base` chỉ phát hành kiến trúc `amd64`.
2. `game-servers/minecraft-bedrock` — Mojang chỉ phát hành Bedrock Dedicated Server Linux `x86_64`.
3. `game-servers/terraria` — SteamCMD (AppID `105600`) & binary Linux `x86_64`.
4. `game-servers/tshock` — Bản phát hành Linux chính thức của Pryaxis TShock là `linux-x64`.
5. `game-servers/factorio` — Wube chỉ cung cấp Factorio Headless Linux `x86_64`.
6. `game-servers/valheim` — SteamCMD (AppID `896660`), binary `x86_64`.
7. `game-servers/palworld` — SteamCMD (AppID `2394010`), binary `x86_64`.
8. `game-servers/rust-game` — SteamCMD (AppID `258550`), binary `x86_64`.
9. `game-servers/ark` — SteamCMD (AppID `376030`), binary `x86_64`.
10. `game-servers/cs2` — SteamCMD (AppID `730`), binary `x86_64`.
11. `game-servers/project-zomboid` — SteamCMD (AppID `380870`), binary `x86_64`.
12. `game-servers/dont-starve-together` — SteamCMD (AppID `343050`), binary `x86_64`.
13. `game-servers/tf2` — SteamCMD (AppID `232250`), binary `x86_64`.
14. `game-servers/fivem` — Cfx.re FXServer Linux artifact chỉ hỗ trợ `x86_64`.
15. `game-servers/mta-sa` — MTA:SA Linux Server chỉ cung cấp gói `x64`.
16. `game-servers/unturned` — SteamCMD (AppID `1110390`), binary `x86_64`.

## 3. Tương thích Pterodactyl Panel & Wings (`PTDL_v1` & `PTDL_v2`)

- **Pterodactyl Panel 1.7–1.12+ (`PTDL_v2` — `egg.json`):** Định dạng khuyên dùng chính, hỗ trợ đầy đủ `docker_images` (nhãn hiển thị + image), `file_denylist` và `variables[].field_type` (`schemas/ptdl_v2.schema.json`).
- **Pterodactyl Panel 1.0–1.6+ (`PTDL_v1` — `egg-ptdl-v1.json`):** Định dạng tương thích ngược hoàn toàn cho các Panel 1.x cũ (và tự động chuyển đổi khi import trên Panel 1.7–1.12), dùng mảng `images[]` phẳng, không có trường mới `file_denylist` hay `field_type` (`schemas/ptdl_v1.schema.json`).
- **Pterodactyl Panel 2.x / Pelican (`PLCN_v1`):** **CHƯA XÁC MINH (`UNVERIFIED`)** — cần kiểm tra bộ chuyển đổi nhập khẩu thực tế trên môi trường thử nghiệm trước khi đưa vào sản xuất.

## 4. Lưu ý đặc biệt về phần cứng, giấy phép & ngoại lệ

- **Ollama CPU (`ollama-cpu`) & Open WebUI (`open-webui`):** Chỉ cấu hình chế độ **CPU / Remote API** mặc định. Không bật GPU passthrough (NVIDIA/ROCm) trong container chia sẻ tiêu chuẩn.
- **Code Server (`code-server`), JupyterLab (`jupyterlab`), n8n (`n8n`):** Không hỗ trợ Docker-in-Docker / mount Docker Socket mặc định để bảo toàn cô lập đa khách hàng.
- **SQLite Workspace (`sqlite-workspace`):** Là không gian làm việc file/CLI SQLite nhúng (`requires_inbound_port: false`), **không phải** database server lắng nghe cổng mạng.
- **EULA & Giấy phép upstream:** Các Egg Minecraft Java/Bedrock, Factorio, FiveM và các game SteamCMD yêu cầu người dùng cuối tuân thủ EULA/điều khoản nhà phát triển; Spigot biên dịch trực tiếp qua BuildTools chính thức thay vì phân phối lại JAR vi phạm bản quyền.
- **Phiên bản Legacy:** `ubuntu-20-04` (ESM only) và `minecraft-waterfall` (PaperMC đã ngừng phát triển) được đánh dấu `status: "Legacy"`.
