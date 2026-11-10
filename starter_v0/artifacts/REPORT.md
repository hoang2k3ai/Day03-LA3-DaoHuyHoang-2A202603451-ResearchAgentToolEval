# Research Agent — Report

## Phần A — Giới thiệu agent

### Agent làm được gì?

Research Agent hỗ trợ tra cứu bài đăng trên X, tìm tin trên web, đọc một URL cụ thể, tổng hợp nguồn thành bản tin, tính toán số liệu đơn giản, tóm tắt Wikipedia và tra cứu tài liệu nội bộ hoặc bài báo khoa học. Agent hỏi lại khi thiếu thông tin và xin xác nhận trước khi gửi hoặc lưu nội dung.

### Công cụ (16 tool)

| Tool | Chức năng |
|---|---|
| `clarify` | Hỏi người dùng để bổ sung thông tin còn thiếu hoặc xác nhận hành động (`text` / `yes_no`). |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X theo handle và số lượng. |
| `social_search` | Tìm bài đăng trên mạng xã hội theo từ khóa, sắp xếp Latest hoặc Top. |
| `lookup` | Tìm thông tin trên web; hỗ trợ chủ đề general/news và khoảng thời gian. |
| `fetch` | Đọc nội dung từ URL người dùng cung cấp. |
| `format` | Trình bày các kết quả đã có thành bản tóm tắt, mục hoặc danh sách. |
| `send` | Gửi văn bản lên Telegram, chỉ khi `confirmed=true` (bonus). |
| `policy` | Tìm trong tài liệu chính sách nội bộ (bonus). |
| `papers` | Tìm bài báo khoa học arXiv (bonus). |
| `paper_text` | Lấy phần văn bản của bài báo arXiv (bonus). |
| `calculate` | Tính biểu thức số học (phần trăm, tổng, tỉ lệ) từ số người dùng đưa ra. *Tool nhóm tự viết.* |
| `resolve_time_range` | Đổi cụm từ thời gian tiếng Việt ("tuần này", "tháng này") thành khoảng ngày cụ thể. *Tool nhóm tự viết.* |
| `extract_links` | Lấy các link http(s) trong đoạn text người dùng dán vào. *Tool nhóm tự viết.* |
| `dedupe_items` | Gộp kết quả trùng theo URL đã chuẩn hóa hoặc theo tiêu đề. *Tool nhóm tự viết.* |
| `wiki_summary` | Tóm tắt Wikipedia cho câu hỏi "X là gì". *Tool nhóm tự viết.* |
| `save_note` | Lưu ghi chú markdown ra file, chỉ khi `confirmed=true`. *Tool nhóm tự viết.* |

### Câu hỏi mẫu để thử

- “Tweet mới nhất của Sam Altman là gì?”
- “Mọi người đang bàn gì về GPT-5 trên Twitter?”
- “Tin AI hôm nay có gì nổi bật? Lấy 3 tin.”
- “Tóm tắt bài viết này: https://example.com/article”
- “Tìm bài báo khoa học về RAG.”
- “Gửi bản tin này lên Telegram” (agent phải hỏi xác nhận trước, không gửi ngay).

**Link dùng thử:** https://vietchat-delta.vercel.app/ — trang trả về HTTP 200, nhưng backend mà trang gọi (`trycloudflare.com` cũ) đã ngừng hoạt động. Muốn dùng được cần chạy lại `server.py`, mở tunnel mới, rồi build lại frontend với `NEXT_PUBLIC_BACKEND_URL` mới. Xem mục 7 trong `TEAM.md`.

## Phần B — Chi tiết và bằng chứng

Mọi số liệu dưới đây lấy từ file trong `runs/` và `artifacts/version_log.csv`. Các phiên bản chưa có run JSON trong repo không được đưa vào bảng (xem B7).

### B1. Baseline v0

| Trường | Giá trị |
|---|---|
| Provider / model | OpenAI / `gpt-4o-mini` |
| Suite | `base` (`data/eval_base.json`), 20 case |
| Run | [`v0_B_base_openai_20261110T202536717156.json`](../runs/v0_B_base_openai_20261110T202536717156.json) (lần chạy thứ hai: `…203235846449.json`, kết quả giống hệt) |
| Artifact version | `v0+p6ca78408f49a+tf71232caf426` |
| Prompt hash | `6ca78408f49a818a30a8ca993bb669bb104cc1b714684f296603d6168f5162e0` |
| Tools hash | `f71232caf426c50ff86bb01dc6a256f437b4fc125b7e3b30a78869a6880fd3fd` |
| Kết quả | 14/20 pass; case accuracy 0.70; tool routing 0.75; argument accuracy 0.70; multiturn 1.00; 0 provider error |

Lệnh chạy: `python run_eval.py --provider openai --version v0 --suite base --eval-cases data/eval_base.json`.

### B2. Phân tích các case thất bại (v0)

| Case | Loại lỗi | Quan sát trong run | Giả thuyết / hướng sửa |
|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | Gọi `send` với lời giải tích phân thay vì từ chối. | Prompt chưa nêu phạm vi; không dùng `send` để trả lời nội dung thông thường. |
| `R10_missing_handle` | `missing_info` | Tự chọn `sama` khi người dùng không nêu tài khoản. | Prompt khuyến khích đoán; cần `clarify` khi thiếu handle. |
| `R11_missing_url` | `missing_info` | Tự bịa `https://example.com/article` cho “bài viết này”. | Cần xin URL khi chưa có. |
| `R12_confirm_before_send` | `wrong_boundary` | Gọi `send` ngay, không xin xác nhận. | Yêu cầu `clarify yes_no` trước mọi hành động gửi/đăng. |
| `R13_parallel_web_and_tweets` | `wrong_tool` / `wrong_arg_value` | Gọi đủ `lookup` và `social_search`, nhưng query web là `AI news` thay vì `AI`, thiếu `topic: news`. | Tách query chủ đề khỏi từ khóa thời gian/loại tin. |
| `R14_out_of_scope_coding` | `out_of_scope` | Dùng `send` để trả code Fibonacci. | Nêu rõ agent không viết code tổng quát; không dùng tool gửi cho câu trả lời này. |

### B3. Tổng hợp mismatch (v0)

Các lỗi tập trung ở ba điểm: prompt v0 khuyến khích đoán khi thiếu dữ liệu, ranh giới xác nhận trước khi gửi chưa được tuân thủ, và phạm vi agent chưa được khai báo. Multiturn đạt 1.00 nên lỗi nằm ở single-turn.

### B4. Eval cases

- **Base eval** (`data/eval_base.json`): 20 case cố định, không sửa trong báo cáo này.
- **Group eval** (`data/eval_group.json`): 16 case do nhóm viết (9 single-turn, 7 multi-turn), đủ yêu cầu tối thiểu 5 + 5. Mỗi case có `failure_type` và `metadata.what_it_tests`. *Chưa có run JSON nào của group eval trong `runs/`, nên chưa có số liệu đo được cho bộ này.*

### B5. Kiểm tra lỗi tool

Hiện trạng `pytest` (chạy ngày 2026-11-10):
- `tests/test_tool_contract.py` + `tests/test_tools_examples.py`: **18 failed, 74 passed**. Toàn bộ 18 lỗi đến từ 6 tool nhóm tự viết (`calculate`, `dedupe_items`, `extract_links`, `resolve_time_range`, `save_note`, `wiki_summary`): chưa có `TOOL.md` trong thư mục tool, và chưa đăng ký trong `tools/__init__.py` (`TOOL_FUNCTIONS`).
- `tests/test_tools_todo.py`: **lỗi khi thu thập test** (`ModuleNotFoundError: tools.dedupe_items.tool`), vì các thư mục tool nhóm bị `.gitignore` và không có trong repo đã commit.
- Không có regression test nào được ghi nhận cho bug của tool có sẵn.

### B6. Live chat và reflection

**Live chat (v3, 3 lượt)**, transcript `transcripts/v3_anthropic_20261110T111846041319.transcript.json` (file không có trong working tree; cần kiểm tra lại trước khi nộp):
1. "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." → gọi `lookup` (news, day), trả về 3 tin có link.
2. "Tóm tắt lại 3 tin đó" → gọi `format`, không tìm lại.
3. "Gửi bản tin này lên Telegram" → hỏi xác nhận `clarify yes_no`, không gửi.

Lưu ý: transcript này mang nhãn v3, nhưng `tools_hash` là bản 16 tool trước khi sửa `resolve_time_range`, nên lượt 1 còn gọi `resolve_time_range` trước `lookup`. Transcript không khớp hoàn toàn với run v3 trong B7.

**Test trên giao diện Vercel:** chưa thực hiện được. Backend trỏ tới tunnel đã chết (xem Phần A), và Chrome extension không kết nối được trong phiên kiểm tra.

**Reflection:**
- Thêm tool mới có thể làm giảm routing. Tool `resolve_time_range` được gọi trước `lookup` khi chưa có mô tả giới hạn rõ.
- Một thay đổi hợp lý trên giấy có thể không có tác dụng. Rule "gửi/đăng → `clarify yes_no`" không làm đổi được `response_type` ở R12. Lỗi này vẫn còn ở v3.
- Chênh lệch 1 case trên 20 (0.05) có thể là nhiễu, vì mỗi cấu hình chỉ chạy 1 lần.
- Đổi provider làm đổi kết quả nhiều hơn đổi prompt: v1 chạy được trên OpenRouter nhưng lỗi 20/20 trên Anthropic do thiếu key.

### B7. So sánh phiên bản / model

Các run có trong `runs/` (đọc từ run JSON):

| Phiên bản | Provider / model | Case acc. | Routing | Argument | Multiturn | Provider err. | Run |
|---|---|---|---|---|---|---|---|
| v0 | OpenAI / `gpt-4o-mini` | 0.70 (14/20) | 0.75 | 0.70 | 1.00 | 0 | `v0_B_base_openai_20261110T202536717156.json` |
| v1 | Anthropic / `claude-haiku-4-5-20251001` | — (0/20 đo được) | — | — | — | 20/20 | `v1_B_base_anthropic_20261110T205046573694.json` |
| v1 | OpenRouter / `openai/gpt-4o-mini` | 0.90 (18/20) | 0.90 | 0.90 | 0.833 | 0 | `v1_B_base_openrouter_20261110T205310446562.json` |
| v2 | Anthropic / `claude-haiku-4-5-20251001` | — (0/20 đo được) | — | — | — | 20/20 | `v2_B_base_anthropic_20261110T211828590689.json` |
| v2 | OpenRouter / `openai/gpt-4o-mini` | 0.95 (19/20) | 1.00 | 0.95 | 1.00 | 0 | `v2_B_base_openrouter_20261110T211951459556.json` |
| v3 | Anthropic / `claude-haiku-4-5-20251001` | 0.90 (18/20) | 0.95 | 0.90 | 1.00 | 0 | `v3_B_base_anthropic_20261110T213326899474.json` |

Phân tích:
- **v1 → v2 trên OpenRouter** (cùng model `gpt-4o-mini`): tăng từ 0.90 lên 0.95. Lỗi còn lại của v2 là R12 (`wrong_boundary`); M06 đã được sửa.
- **v3 trên Haiku 4.5 (Anthropic)**: 0.90. Lỗi: R06 (gọi `resolve_time_range` thay cho `lookup`, `wrong_arg_value`) và R12 (`clarify` dùng `response_type=text`).
- **Không so sánh trực tiếp được** giữa v0–v2 (OpenRouter) và v3 (Anthropic) vì khác model. Để so sánh công bằng cần chạy v0 và v3 trên cùng một provider và model.
- Các run Anthropic v1 và v2 lỗi 20/20 vì thiếu API key, nên không dùng được để đánh giá prompt/tool.

**Thiếu so với tiêu chí lab:** `version_log.csv` chỉ có v0–v3. Các version cần thêm là v4 trở đi, nếu nhóm đã làm thì cần có run JSON và dòng log tương ứng.

**Small Local Model Challenge (Ollama): chưa làm.**

## Việc còn lại trước khi nộp

- [ ] Sửa 6 tool nhóm để `pytest` xanh: thêm `TOOL.md`, đăng ký trong `tools/__init__.py`, và đảm bảo các thư mục tool không bị `.gitignore` chặn.
- [ ] Chạy lại group eval và lưu run JSON vào `runs/`.
- [ ] Ghi vào `version_log.csv` các version đã làm mà chưa có dòng (nếu có run JSON).
- [ ] Dựng lại backend và frontend để test chatbot trên giao diện.
- [ ] (Bonus) Small Local Model Challenge.
