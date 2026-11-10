# Team

- Team: HQHD
- Members: Lê Hồng Quân, Võ Huy Hoàng, Hồ Văn Dũng, Vũ Mạnh Hoạch
- Provider/model: Anthropic (`--provider anthropic`), model `claude-haiku-4-5-20251001`; v0–v2 còn có run trên OpenAI/OpenRouter (`gpt-4o-mini`)

---

## Tóm tắt

Nhóm xây dựng research agent tiếng Việt: agent nhận câu hỏi, chọn tool, gọi tool thật, rồi trả lời từ kết quả. Prompt và mô tả tool được sửa qua 4 phiên bản (v0 → v3) dựa trên run JSON thật, đo bằng base eval (20 case cố định) và group eval (16 case do nhóm viết).

Kết quả (đối chiếu với `runs/` và `artifacts/version_log.csv`, ngày 2026-11-10):

| Hạng mục | Kết quả |
|---|---|
| Base eval v0 (OpenAI `gpt-4o-mini`) | 0.70 (14/20) |
| Base eval v1 / v2 (OpenRouter `gpt-4o-mini`) | 0.90 (18/20) / 0.95 (19/20) |
| Base eval v3 (Anthropic Haiku 4.5) | 0.90 (18/20), routing 0.95, multiturn 1.00 |
| Group eval v3 (Anthropic Haiku 4.5) | 0.875 (14/16), routing 0.9375, multiturn 0.857 |
| Unit test (`pytest`) | 126 passed, 0 skipped, 0 failed |

Các phiên bản v4–v10 từ nhánh cũ đã được loại bỏ khỏi báo cáo. Lịch sử chính thức của nhóm là v0–v3 trong `version_log.csv`.

---

## 1. Tool của agent (16 tool)

Tool có sẵn từ starter (10): `clarify`, `timeline`, `social_search`, `lookup`, `fetch`, `format`, `send` (chỉ gửi khi `confirmed=true`), `policy`, `papers`, `paper_text`.

Tool nhóm tự viết (6). Mỗi tool có `tool.py` và `TOOL.md` trong `tools/<tên>/`, đã đăng ký trong `tools/__init__.py` (`TOOL_FUNCTIONS`) và khai báo trong `artifacts/tools.yaml`. Các thư mục này không bị `.gitignore` chặn:

| Tool | Làm gì |
|---|---|
| `calculate` | Tính biểu thức số học an toàn (phần trăm, tổng...), không chạy code tùy ý |
| `resolve_time_range` | Đổi "hôm nay / tuần này / tuần trước" thành khoảng ngày cụ thể |
| `extract_links` | Lấy các link http(s) trong đoạn text, bỏ trùng |
| `dedupe_items` | Gộp item trùng theo URL (sau khi bỏ UTM, dấu `/` cuối) hoặc tiêu đề |
| `wiki_summary` | Tóm tắt Wikipedia cho câu hỏi "X là gì" |
| `save_note` | Lưu ghi chú markdown vào file, chỉ khi `confirmed=true` |

Tool nhóm đã thêm: 6 (vượt mức bắt buộc 1 và mức bonus >3). Cùng có UI, nên đủ điều kiện điểm thưởng.

---

## 2. Lịch sử tối ưu (`artifacts/version_log.csv`)

| Version | Run | Kết quả |
|---|---|---|
| v0 | OpenAI `gpt-4o-mini`, base (2 lần, cùng kết quả) | 0.70 (14/20) |
| v1 | OpenRouter `gpt-4o-mini`, base | 0.90 (18/20); lỗi R12, M06 |
| v2 | OpenRouter `gpt-4o-mini`, base | 0.95 (19/20); lỗi R12 |
| v3 | Anthropic Haiku 4.5, base | 0.90 (18/20); lỗi R06, R12 |
| v3 | Anthropic Haiku 4.5, group | 0.875 (14/16); lỗi G05, G16 |

Run Anthropic của v1 và v2 lỗi 20/20 do thiếu API key lúc đó, nên không dùng để so sánh.

Bài học:
- Thêm tool mới có thể làm giảm routing: ở v3, `resolve_time_range` bị gọi thay cho `lookup` (R06).
- Prompt không kiểm soát được `response_type` của `clarify`: R12 và G16 vẫn dùng `text` thay vì `yes_no`.
- Mỗi cấu hình chỉ chạy 1 lần, nên chênh 1 case (0.05) có thể là nhiễu.
- Đổi provider/model làm đổi kết quả nhiều hơn đổi prompt, nên v0–v2 (OpenRouter) và v3 (Anthropic) không so sánh trực tiếp được.

---

## 3. Group eval (16 case)

File `data/eval_group.json`: **9 single-turn, 7 multi-turn**, mỗi case có `failure_type` và `metadata.what_it_tests`. Run: `runs/v3_B_group_anthropic_20261110T215305046582.json`.

Kết quả v3: 14/16 pass, case 0.875, routing 0.9375, argument 0.875, multiturn 0.857.

Còn lỗi:
- **G05** (`wrong_tool`): gọi `paper_text` cho arXiv URL, case kỳ vọng `fetch`.
- **G16** (`wrong_boundary`): `save_note` hỏi tiêu đề bằng `response_type=text`, kỳ vọng `yes_no`.

---

## 4. Kiểm thử tự động

`pytest`: **126 passed, 0 skipped, 0 failed**, chạy offline (conftest chặn mạng thật, HTTP mock bằng `fake_http`).
- `tests/test_tools_todo.py`: đã điền toàn bộ stub bằng test thật.
- Mỗi tool nhóm có ≥3 test: `calculate` (3), `resolve_time_range` (3), `extract_links` (3), `dedupe_items` (4), `wiki_summary` (3), `save_note` (3).
- `tests/test_tool_contract.py`: `tools.yaml` khớp code và `TOOL.md`.

---

## 5. UI và triển khai

- **Backend:** `starter_v0/server.py` (lấy từ nhánh `LeHongQuan_2A202603705`, chỉ lấy file server và `compare.html`). Chạy `python server.py --port 8000 --allowed-origin https://vietchat-delta.vercel.app`. Endpoint: `POST /api/chat`, `GET /api/health`, `GET /api/tools`, `GET /api/versions`.
- **Đã kiểm tra backend cục bộ (2026-11-10):** `/api/health` OK, `/api/tools` trả 16 tool; hỏi "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." trả 3 tin có nguồn; hỏi "Tính 15% của 2400000" gọi `calculate` và trả 360,000.
- **Tunnel:** `cloudflared tunnel --url http://127.0.0.1:8000` cho ra `https://chrome-prominent-damaged-geek.trycloudflare.com` (tạm thời, mất khi tắt `cloudflared`).
- **Frontend:** https://vietchat-delta.vercel.app/ (HTTP 200). Mã nguồn frontend không nằm trong repo. Frontend đọc `NEXT_PUBLIC_BACKEND_URL` lúc build, nên mỗi lần đổi tunnel cần đặt lại biến này trên Vercel và redeploy.
- **Trang so sánh:** `starter_v0/compare.html`, phục vụ qua `/compare`.

**Chi tiết trang dùng thử**

Nội dung lấy từ HTML tĩnh của https://vietchat-delta.vercel.app/#home (kiểm tra 2026-11-10). Lúc đó trang hiển thị "Chưa kết nối" nên chưa chat thật được; đây là mô tả giao diện, không phải kết quả agent trả lời.

- **Nhận diện:** tiêu đề "Nghiên cứu — Trợ lý nghiên cứu AI", tên app "Research Agent", khẩu hiệu "Nghiên cứu nhanh hơn. Hiểu sâu hơn.", chân trang "Phiên bản v0".
- **Điều hướng:** "Trang chủ" (`#home`), "Cuộc trò chuyện mới", "Công cụ"; sidebar có "Hôm nay" và "Khám phá cùng Research Agent". Trang không có route riêng cho "dùng thử".
- **Trạng thái:** hiển thị "Chạy backend" / "Chưa kết nối" (phụ thuộc backend và tunnel đang chạy).
- **Màn hình chat:** lời chào "Xin chào! Hôm nay tôi giúp gì cho bạn?", mục "Gợi ý nhanh" và ô nhập ở cuối trang.
- **Câu hỏi mẫu trên trang** (cột tool là suy ra từ mô tả tool của nhóm, không hiển thị trên trang):

| Nhóm | Câu hỏi mẫu | Tool dự kiến |
|---|---|---|
| Tin tức và tìm kiếm | "Tin tức AI hôm nay có gì nổi bật?" | `lookup` (news) |
| Tin tức và tìm kiếm | "Mọi người đang nói gì về Claude Opus trên mạng xã hội tuần này?" | `social_search` |
| Tweet | "Tweet mới nhất của Sam Altman là gì?" | `timeline` |
| Thời gian | "Tin AI tuần trước là từ ngày nào đến ngày nào?" | `resolve_time_range` |
| Tính toán | "Tính giúp mình 15% của 2 tỷ 400 triệu" | `calculate` |
| Link | "Lấy hết link trong đoạn này: https://a.com/x và https://b.org/y" | `extract_links` |
| Định nghĩa | "Trí tuệ nhân tạo là gì?" | `wiki_summary` |
| Ghi chú | "Lưu bản tin này vào ghi chú giúp mình" | `save_note` (hỏi xác nhận) |
| Hỏi lại | "Đăng bản tin này lên Telegram giúp mình" | `clarify` rồi `send` |

- **Kịch bản thử:** hỏi "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." rồi "Tóm tắt lại 3 tin đó" rồi "Gửi bản tin này lên Telegram" (agent phải hỏi xác nhận, không gửi ngay).

---

## 6. Bonus

| Bonus | Trạng thái |
|---|---|
| UI + >3 tool mới | Đạt (UI Vercel + backend; 6 tool mới) |
| `send` có xác nhận | Code và test đạt (`confirmed=false` thì không gửi); chưa gửi Telegram thật vì thiếu `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` |
| `policy`, `papers`, `paper_text` | Có tool, unit test, và case trong group eval (G02, G03, G06, G07) |
| Small Local Model (Ollama) | Chưa chạy được; xem `REPORT.md` B7 |

---

## 7. Ghi chú về dữ liệu

- Không commit `.env` và không ghi API key vào tài liệu.
- Run từ nhánh cũ (v4–v10, v0–v3 Anthropic) không được đưa vào repo này.
