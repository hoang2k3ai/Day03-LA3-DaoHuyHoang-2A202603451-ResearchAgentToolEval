# Team

- Team: HQHD
- Members: Lê Hồng Quân, Võ Huy Hoàng, Hồ Văn Dũng, Vũ Mạnh Hoạch
- Provider/model: Anthropic (gọi trực tiếp API, `--provider anthropic`), model mặc định trong code: `claude-haiku-4-5-20251001`

---

## Tóm tắt

Nhóm xây dựng research agent tiếng Việt: agent nhận câu hỏi, chọn tool, gọi tool thật, rồi trả lời từ kết quả. Qua 10 vòng tối ưu (v0 → v10), nhóm sửa prompt và mô tả tool dựa trên log thật, đo bằng base eval (20 case cố định) và group eval (16 case do nhóm viết).

Kết quả hiện tại:
- Base eval: **0.90 (18/20)**, không hồi quy qua v8, v9, v10.
- Group eval: **0.875 (14/16)** ở v10 (từ 0.50 ở v8 với case gốc).
- Unit test: **126 passed, 0 skipped**.

---

## 1. Tool của agent (16 tool)

Tool có sẵn từ starter (10):

| Tool | Làm gì |
|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận (`text` / `yes_no`) |
| `timeline` | Lấy bài đăng gần đây của một tài khoản |
| `social_search` | Tìm bài đăng theo từ khóa (Latest/Top) |
| `lookup` | Tìm web, có `topic` (general/news) và `timeframe` |
| `fetch` | Đọc nội dung một URL |
| `format` | Trình bày các item đã có thành bản tin/bullet/thread |
| `send` | Gửi text lên Telegram, chỉ khi `confirmed=true` (bonus) |
| `policy` | Tìm trong tài liệu chính sách nội bộ (bonus) |
| `papers` | Tìm bài báo arXiv (bonus) |
| `paper_text` | Tải PDF arXiv và trích text (bonus) |

Tool nhóm tự viết (6), mỗi tool có `TOOL.md`, đăng ký trong `tools/__init__.py` và `artifacts/tools.yaml`:

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

## 2. Lịch sử tối ưu prompt và tool declaration

Mỗi vòng chỉ đổi một giả thuyết, ghi trong `artifacts/version_log.csv` (11 dòng, v0–v10).

| Version | Thay đổi | Base eval |
|---|---|---|
| v0 | Baseline (prompt starter đã sửa các chỉ dẫn xấu) | 0.90 |
| v1 | Viết lại description + convention args (đổi 2 file cùng lúc, vi phạm nguyên tắc) | 0.75, **bị bác bỏ** |
| v2 | Một rule: gửi/đăng → `clarify yes_no` | 0.90, không tăng |
| v3 | Mô tả `lookup.query`: chỉ chủ đề, không kèm thời gian | **0.95 (19/20)**, cao nhất khi chưa có 6 tool nhóm |
| v4 | Thêm 6 tool nhóm vào `tools.yaml` | 0.70, **bị bác bỏ** (`resolve_time_range` bị gọi nhầm trước `lookup`) |
| v5 | Thu hẹp mô tả `resolve_time_range` | 0.85 |
| v6 | Thêm ví dụ GỌI / KHÔNG GỌI cho `resolve_time_range` | 0.90 |
| v7 | Khôi phục prompt, mô tả đủ 16 tool | 0.90 |
| v8 | Rule routing cho đủ 16 tool trong prompt | 0.90 |
| v9 | `policy.query`: chỉ cụm từ chủ đề, không kèm "chính sách/quy định" | 0.90 (không hồi quy) |
| v10 | Rule `send` / `save_note`: không hỏi chat ID hoặc tiêu đề, xác nhận luôn `yes_no` | 0.90 (không hồi quy) |

Các bài học rút ra:
- Thêm tool mới có thể làm giảm routing (v4), nên mô tả tool quan trọng hơn số lượng tool.
- Một thay đổi hợp lý trên giấy có thể không có tác dụng (v2, R12): prompt không kiểm soát được tham số `response_type`.
- Với 1 lần chạy mỗi case, chênh lệch 1 case (0.05) có thể là nhiễu; chưa đo lặp lại.

---

## 3. Group eval (16 case)

File: `data/eval_group.json`. Có **10 single-turn** và **6 multi-turn**, đạt yêu cầu ≥5 + ≥5. Mỗi case có `failure_type` và `metadata.what_it_tests`.

Kết quả các lần chạy:

| Lần chạy | case_accuracy | multiturn_accuracy | Ghi chú |
|---|---|---|---|
| v8, case gốc | 0.50 (8/16) | 0.17 | 5 case thiếu ngữ cảnh |
| v8, case đã sửa ngữ cảnh | 0.69 (11/16) | 0.57 | Chỉ đổi case, không đổi prompt |
| v9 | 0.81 (13/16) | 0.71 | Sửa G03, G07 |
| **v10** | **0.875 (14/16)** | **0.86** | Sửa G10 |

**Sửa case (đã ghi trong `metadata.eval_fix`):** G06, G09, G10, G15, G16 được thêm đoạn kết quả/nội dung trong lượt trước, vì case giả định agent đã có dữ liệu đó nhưng thực tế không có. Kỳ vọng (`expect`) không đổi. Lần chạy đầu với case gốc được giữ làm mốc.

**Còn lỗi:**
- **G05**: prompt yêu cầu `paper_text` khi đã có arXiv URL, còn case kỳ vọng `fetch`. Mâu thuẫn giữa prompt và case, nhóm cần quyết định bên nào đúng.
- **G16**: agent vẫn hỏi tiêu đề bằng `response_type=text` dù prompt đã yêu cầu `yes_no`. Dự kiến thử ở v11 (mô tả `save_note` trong `tools.yaml`), chưa làm.

---

## 4. Base eval (20 case, cố định)

Chạy đầy đủ cho v0–v10. Kết quả cuối (v10): case_accuracy 0.90, tool_routing 0.95, argument 0.90, multi-turn 1.00. Lỗi còn lại: 1 `wrong_arg_value` và 1 `wrong_boundary`. Theo báo cáo trước đó, `wrong_boundary` là R12 (`clarify` dùng `text`, không phải `yes_no`); chưa kiểm tra lại từng case cho v10.

---

## 5. Kiểm thử tự động

- `pytest`: **126 passed, 0 skipped, 0 failed**. Chạy offline, chặn mạng thật (conftest), HTTP được mock bằng `fake_http`.
- `tests/test_tools_todo.py`: đã thay toàn bộ stub bằng test thật (happy path, input xấu, nhánh lỗi trả error dict, và kiểm tra request gửi đi).
- Test cho 6 tool nhóm: `calculate` (3 test), `resolve_time_range` (3), `extract_links` (3), `dedupe_items` (4), `wiki_summary` (3), `save_note` (3).
- `tests/test_tool_contract.py`: `tools.yaml` khớp với code và `TOOL.md`.

---

## 6. Chạy thử trực tiếp (live chat)

Transcript: `transcripts/v3_anthropic_20261110T111846041319.transcript.json`, 3 lượt:
1. "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." → gọi `lookup` (news, day), trả về 3 tin có link.
2. "Tóm tắt lại 3 tin đó" → gọi `format` (brief), không tìm lại.
3. "Gửi bản tin này lên Telegram" → hỏi xác nhận `clarify yes_no`, **không gửi**.

Lưu ý: transcript mang nhãn v3 nhưng `tools_hash` là bản 16 tool trước khi sửa `resolve_time_range`, nên lượt 1 còn gọi `resolve_time_range` trước `lookup`.

---

## 7. UI và triển khai

- **Backend**: `starter_v0/server.py`, chạy `python server.py --port 8000`. Các endpoint: `POST /api/chat`, `GET /api/health`, `GET /api/tools`, `GET /api/versions`. CORS có thể cấu hình qua `--allowed-origin`.
- **Frontend**: hosted trên Vercel, link https://vietchat-delta.vercel.app/ (trả về HTTP 200 khi kiểm tra). Mã nguồn frontend **không nằm trong repo này**.
- **Tunnel**: backend được expose bằng Cloudflare Tunnel (`cloudflared tunnel --url http://127.0.0.1:8000`). Link tunnel là tạm thời, sống theo phiên.
- **Trang so sánh**: `starter_v0/compare.html`, so sánh các version.
- **Demo**: kịch bản trong `artifacts/DEMO.md`.

---

## 8. Bonus

| Bonus | Trạng thái |
|---|---|
| UI + >3 tool mới | **Đạt** (UI có link; 6 tool mới) |
| `send` có xác nhận | Code và test đạt (`confirmed=false` → không gửi, có test). **Chưa gửi thật**: thiếu `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`, admin đã khóa quyền remote |
| `policy`, `papers`, `paper_text` | Đã có tool và unit test; chưa có eval riêng |
| Small Local Model Challenge (Ollama) | **Chưa làm**: chưa cài Ollama, chưa chạy model local nào |

---

## 9. Việc còn lại

- [ ] Sửa G16 (v11), hoặc ghi nhận là lỗi còn lại trong báo cáo.
- [ ] Nhóm quyết định G05: `paper_text` hay `fetch` cho arXiv URL.
- [ ] Chạy lại base eval và group eval ít nhất 2 lần để đo nhiễu (hiện mỗi case chỉ chạy 1 lần).
- [ ] Hoàn thiện `artifacts/REPORT.md` Phần B (B6 Reflection, B7 local model).
- [ ] Bonus local model (tùy chọn).
- [ ] Commit và nộp: `runs/`, `transcripts/`, các thư mục tool mới, `server.py`, `compare.html`, `TEAM.md`, `artifacts/`. Mã nguồn frontend cần nộp riêng nếu yêu cầu.
- [ ] Ghi chú: trong lúc làm v3, `REPORT.md` bị một tiến trình khác sửa, làm hash v3 không khớp với file hiện tại (đã ghi trong B6).

---

## 10. Ghi chú về dữ liệu

- Không commit `.env` và không ghi API key vào tài liệu.
- Các bản sửa case (`eval_fix`) là thay đổi do nhóm tự làm, đã ghi rõ trong file case và trong báo cáo.
