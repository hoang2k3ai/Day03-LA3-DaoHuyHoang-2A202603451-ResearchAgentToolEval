# Kịch bản demo — Research Agent (v0)

**Link UI:** https://vietchat-delta.vercel.app/
**Backend:** tunnel Cloudflare trỏ về `server.py` trên máy demo (xem bên dưới).

## Trước khi demo (checklist 2 phút)

1. Chạy backend: `.venv/bin/python server.py --port 8000`
2. Chạy tunnel: `cloudflared tunnel --url http://127.0.0.1:8000`
3. Kiểm tra: `curl <tunnel>/api/health` → `{"ok": true, ...}`; `curl <tunnel>/api/tools` → danh sách 16 tool.
4. Mở UI, thấy chấm trạng thái trên header màu xanh là sẵn sàng.

Nếu tunnel đổi URL, cập nhật `NEXT_PUBLIC_BACKEND_URL` trên Vercel rồi publish lại.

## Luồng demo (khoảng 8 phút)

### 1. Giới thiệu (30 giây)
- "Đây là research agent: model chọn tool, gọi tool thật, rồi trả lời từ kết quả."
- Chỉ panel **Công cụ**: 16 tool, mỗi tool có mô tả khi nào nên dùng.

### 2. Tool có sẵn (2 phút)
| Câu hỏi | Tool được gọi | Điểm cần nhấn |
|---|---|---|
| Tin tức AI hôm nay có gì nổi bật? | `lookup` (topic=news, timeframe=day) | Route đúng, có nguồn |
| Tweet mới nhất của Sam Altman là gì? | `timeline` (screenname=sama) | Map tên người thành handle |
| Đăng bản tin này lên Telegram giúp mình | `clarify` (yes_no) | Hỏi xác nhận trước khi gửi |

### 3. Tool mới của nhóm (4 phút)
| Câu hỏi | Tool mới | Điểm cần nhấn |
|---|---|---|
| Tính giúp mình 15% của 2 tỷ 400 triệu | `calculate` | Tính bằng biểu thức an toàn, không chạy code tùy ý |
| Tin AI tuần trước là từ ngày nào đến ngày nào? | `resolve_time_range` | Đổi "tuần trước" thành ngày cụ thể theo giờ VN |
| Lấy hết link trong đoạn này: https://a.com/x và https://b.org/y | `extract_links` | Liệt kê link, bỏ trùng |
| Trí tuệ nhân tạo là gì? | `wiki_summary` | Tóm tắt Wikipedia, không dùng tin tức |
| Lưu bản tin này vào ghi chú giúp mình | `clarify` rồi `save_note` | Chỉ ghi file sau khi người dùng xác nhận |

Nhiều lượt (cho thấy nhớ ngữ cảnh):
1. "Tìm tin AI hôm nay" → `lookup`
2. "Gộp các tin bị trùng trong kết quả trên giúp mình" → `dedupe_items` (không tìm lại)

### 4. Cái gì đã làm và kiểm chứng (1 phút)
- 16 tool, 6 tool mới có `TOOL.md`, đăng ký trong registry, khai báo trong `tools.yaml`.
- Unit test: 19 test cho tool mới, chạy offline, mock HTTP.
- Contract test: 85 test, đảm bảo `tools.yaml` khớp code.
- Eval: 16 case trong `data/eval_group.json` (10 case nhóm viết thêm + 6 case route tool mới). Chưa chạy eval nhóm trên model; chỉ nói về eval khi đã có số liệu trong `runs/`.

## Nếu có sự cố

- **UI báo "Không kết nối được backend"**: tunnel đã đổi hoặc `server.py` đã dừng. Chạy lại hai lệnh ở phần chuẩn bị.
- **Trả lời chậm**: model và tool gọi API bên ngoài, chờ thêm vài giây là bình thường.
- **Model không gọi đúng tool**: đây là điểm để thảo luận, ghi lại câu hỏi và kết quả thật thay vì sửa trực tiếp khi đang demo.
