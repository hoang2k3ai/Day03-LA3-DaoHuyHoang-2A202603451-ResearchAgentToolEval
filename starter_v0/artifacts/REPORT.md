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

**Link dùng thử:** [Mở Research Agent trên Vercel](https://vietchat-delta.vercel.app/). Frontend gọi backend qua `NEXT_PUBLIC_BACKEND_URL`; trạng thái kết nối cần backend và tunnel đang chạy. Backend đã kiểm tra cục bộ, xem B6.

### Chi tiết trang dùng thử

Snapshot HTML ban đầu của https://vietchat-delta.vercel.app/#home ngày 2026-11-10 từng hiển thị “Chưa kết nối”; sau đó nhóm đã kiểm tra UI Vercel cùng đồng đội và xác nhận frontend kết nối backend, hoạt động bình thường.

- **Nhận diện:** tiêu đề "Nghiên cứu — Trợ lý nghiên cứu AI", tên app "Research Agent", khẩu hiệu "Nghiên cứu nhanh hơn. Hiểu sâu hơn.", chân trang "Phiên bản v0".
- **Điều hướng:** "Trang chủ" (`#home`), "Cuộc trò chuyện mới", "Công cụ"; sidebar có "Hôm nay" và "Khám phá cùng Research Agent". Trang không có route riêng cho "dùng thử".
- **Trạng thái:** UI đã được nhóm kiểm tra trực tiếp và hoạt động bình thường khi backend/tunnel sẵn sàng.
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

## Phần B — Chi tiết và bằng chứng

Mọi số liệu dưới đây lấy từ file trong `runs/` và `artifacts/version_log.csv`. Chỉ các phiên bản có run JSON trong `runs/` được đưa vào báo cáo.

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
- **Group eval** (`data/eval_group.json`): 16 case do nhóm viết (9 single-turn, 7 multi-turn), đủ yêu cầu tối thiểu 5 + 5. Mỗi case có `failure_type` và `metadata.what_it_tests`; có case route tới cả 6 tool nhóm, `policy`, `papers`, `paper_text` và ranh giới xác nhận của `send` / `save_note`.
  - Run v3 (Anthropic Haiku 4.5): [`v3_B_group_anthropic_20261110T215305046582.json`](../runs/v3_B_group_anthropic_20261110T215305046582.json). Kết quả: 14/16 (0.875); routing 0.9375; argument 0.875; multiturn 0.857; 0 provider error.
  - Lỗi: `G05_fetch_url` (`wrong_tool`: gọi `paper_text` thay vì `fetch` cho arXiv URL) và `G16_save_note_needs_confirm` (`wrong_boundary`: `clarify` dùng `response_type=text` thay vì `yes_no`).

### B5. Kiểm tra lỗi tool

`pytest` (2026-11-10): **126 passed, 0 skipped, 0 failed**.
- `tests/test_tools_todo.py`: đã thay toàn bộ stub bằng test thật (happy path, input xấu như chuỗi rỗng/sai kiểu/ngoài enum, nhánh lỗi trả error dict, và assert request gửi đi).
- 6 tool nhóm đều có `tool.py`, `TOOL.md`, đăng ký trong `tools/__init__.py` và `tools.yaml`; mỗi tool ≥3 test. `tests/test_tool_contract.py` xanh cho cả 16 tool.
- Thư mục 6 tool nhóm không bị `.gitignore` chặn (`git check-ignore` không khớp), nên được nộp cùng repo.

### B6. Live chat và reflection

**Live chat (v3, OpenAI / gpt-4o-mini, 6 lượt)**: [`v3_openai_20261110T223901200376.transcript.json`](../transcripts/v3_openai_20261110T223901200376.transcript.json). Transcript ghi nhận hai lượt hỏi đáp về ca sĩ, sau đó người dùng yêu cầu gửi bản tin lên Telegram. Agent hỏi `clarify(response_type=yes_no)` trước; sau khi người dùng đồng ý, agent xin nội dung, trình bày bản nháp và xin xác nhận nội dung trước khi gọi `send` với `confirmed=true`. Lần gọi `send` trả `HTTPError` 400, nên gửi không thành công. Token bot trong URL lỗi đã được che trong bản transcript lưu trong repo; cần thu hồi/đổi token tương ứng trước khi dùng tiếp.

Transcript dùng artifact `v3+p3ec941697a79+t77a379b681e8`, trùng artifact của run v3 OpenAI 20/20 ở B7. Transcript thứ hai `v3_openai_20261110T224223510210.transcript.json` có 2 lượt hỏi đáp và không có lượt xác nhận gửi.

**Test backend của chatbot (2026-11-10):** chạy `server.py` cục bộ, `/api/health` OK, `/api/tools` trả 16 tool, CORS cho `https://vietchat-delta.vercel.app`. Hỏi "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." trả 3 tin có nguồn; hỏi "Tính 15% của 2400000" gọi `calculate` và trả 360,000. Tunnel mới: `https://chrome-prominent-damaged-geek.trycloudflare.com`.

**Reflection:**
- Thêm tool mới có thể làm giảm routing. Tool `resolve_time_range` được gọi trước `lookup` khi chưa có mô tả giới hạn rõ.
- Một thay đổi prompt ban đầu chưa đủ để sửa R12: model vẫn hỏi nội dung bằng `response_type=text`. Sau khi làm rõ thứ tự xác nhận trong prompt và đặt `response_type` thành tham số bắt buộc trong schema `clarify`, run v3 trên OpenAI đạt 20/20; R12 chuyển sang `yes_no`. Live chat xác nhận agent đã hỏi trước khi gửi và chỉ gọi `send` sau xác nhận, nhưng lần gửi thất bại với HTTP 400. Run group trên Anthropic trước thay đổi này vẫn còn G16, nên không suy rộng kết quả sang provider/run đó.
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
| v3 | OpenAI / `gpt-4o-mini` | 1.00 (20/20) | 1.00 | 1.00 | 1.00 | 0 | [`v3_B_base_openai_20261110T222940419872.json`](../runs/v3_B_base_openai_20261110T222940419872.json) |

Phân tích:
- **v1 → v2 trên OpenRouter** (cùng model `gpt-4o-mini`): tăng từ 0.90 lên 0.95. Lỗi còn lại của v2 là R12 (`wrong_boundary`); M06 đã được sửa.
- **v3 trên Haiku 4.5 (Anthropic)**: 0.90. Lỗi: R06 (gọi `resolve_time_range` thay cho `lookup`, `wrong_arg_value`) và R12 (`clarify` dùng `response_type=text`).
- **v3 cuối trên OpenAI**: 1.00 (20/20), gồm R12 pass với `clarify(response_type=yes_no)`. So với baseline v0 trên cùng provider/model `gpt-4o-mini` (0.70, 14/20), điểm tăng 0.30; tuy vậy v3 bao gồm nhiều thay đổi tích lũy nên đây không phải phép đo tác động riêng của một chỉnh sửa.
- Run group Anthropic (14/16) được đánh giá riêng và vẫn có G16 `response_type=text`; run này dùng artifact trước khi chỉnh schema/prompt cuối, nên không mâu thuẫn với R12 pass trên run OpenAI mới.
- Các run Anthropic v1 và v2 lỗi 20/20 vì thiếu API key, nên không dùng được để đánh giá prompt/tool.

`version_log.csv` có 9 bản ghi dữ liệu: v0 (2 lần), v1 (2), v2 (2), v3 Anthropic base, v3 group và v3 OpenAI base cuối. Run Anthropic của v1 và v2 không có số liệu do lỗi key.

### Small Local Model Challenge (Ollama)

Chưa có run local nào. Máy hiện chưa cài Ollama (không có `sudo`); đã tải bản Ollama cho Linux về `~/ollama` nhưng môi trường chặn việc giải nén và chạy binary tải về, nên không chạy được `ollama serve` và `ollama pull`. Máy có 8 core, 15 GB RAM, không GPU: dùng `llama3.2:3b` và `qwen2.5:3b`/`qwen2.5:7b`. Sau khi cài Ollama, chạy `run_eval.py --provider ollama --model <model> --version v3-<model> --suite base` cho từng model, rồi 2 vòng tối ưu `v4-local`, `v5-local` như README Step 7, và điền bảng cloud vs local tại đây.
