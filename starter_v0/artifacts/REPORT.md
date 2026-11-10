# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: HQHD
- Members: Lê Hồng Quân, Võ Huy Hoàng, Hồ Văn Dũng,  Vũ Mạnh Hoạch
- Provider/model: Anthropic (gọi trực tiếp API, `--provider anthropic`), model mặc định trong code: `claude-haiku-4-5-20251001`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent nhận câu hỏi tiếng Việt, tự chọn tool phù hợp để tra cứu: bài đăng mạng xã hội (theo tài khoản hoặc từ khóa), tin tức và thông tin trên web, nội dung một URL, bài báo khoa học và tài liệu nội bộ. Khi thiếu thông tin (ví dụ thiếu tài khoản hoặc URL) agent hỏi lại người dùng thay vì đoán. Với hành động gửi đi, agent cần người dùng xác nhận trước.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: https://vietchat-delta.vercel.app/

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin (hỏi mở hoặc có/không) | không |
| timeline | lấy các bài đăng gần đây của một tài khoản | không |
| social_search | tìm bài đăng trên mạng xã hội theo từ khóa | không |
| lookup | tra cứu thông tin trên internet, có thể lọc tin tức theo thời gian | không |
| fetch | lấy nội dung từ một URL | không |
| format | trình bày dữ liệu đã có thành văn bản | không |
| send | gửi một đoạn văn bản đi (chỉ khi người dùng đã xác nhận) | không |
| policy | tìm trong tài liệu nội bộ | không |
| papers | tìm bài báo khoa học | không |
| paper_text | lấy nội dung text của một bài báo | không |
| calculate | tính toán số học (phần trăm, tổng, quy đổi) trong bản tin | có |
| resolve_time_range | đổi cụm thời gian tiếng Việt ("hôm nay", "tuần này"...) thành khoảng ngày cụ thể | có |
| extract_links | lấy tất cả link http(s) trong đoạn văn bản người dùng dán vào | có |
| dedupe_items | gộp tin trùng URL hoặc trùng tiêu đề trước khi format | có |
| wiki_summary | lấy đoạn tóm tắt Wikipedia của một chủ đề ("X là gì") | có |
| save_note | lưu ghi chú markdown vào thư mục dự án (chỉ khi người dùng xác nhận) | có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tweet mới nhất của Sam Altman là gì?
2. Mọi người đang bàn gì về GPT-5 trên Twitter?
3. Tin tức AI hôm nay có gì nổi bật?
4. Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-5
5. Đăng bản tin này lên Telegram giúp mình (agent phải hỏi xác nhận trước)

---

# PHẦN B — Chi tiết / Bằng chứng

**Bản nộp:** `system_prompt.md` = v2 (một dòng rule gửi/đăng → `clarify` yes_no), `tools.yaml` = v6 (16 tool, gồm 6 tool nhóm tự viết, mô tả `resolve_time_range` có ví dụ GỌI / KHÔNG GỌI). Kết quả base eval của bản nộp: **case_accuracy 0.90 (18/20)**.

Lưu ý: run có điểm cao nhất là **v3 (0.95, 19/20)** nhưng khi đó `tools.yaml` chỉ có 10 tool, chưa có 6 tool nhóm. Chênh lệch 0.05 tương đương 1 case, mỗi case chỉ chạy 1 lần nên chưa đo được nhiễu. Tất cả run dùng provider `anthropic`, model `claude-haiku-4-5-20251001`, suite `base` (20 case).

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (git HEAD) | — | — | case_accuracy=0.90 (18/20) | `runs/v0_B_base_anthropic_20261110T101120279603.json` |
| v1 | `tools.yaml` + `system_prompt.md` (đổi cả hai, vi phạm "một giả thuyết") | Convention args (R03) + rule clarify yes_no (R12). **Bác bỏ**: giảm | 0.90 (18/20) | 0.75 (15/20) | `runs/v1_B_base_anthropic_20261110T105944292745.json` |
| v2 | `system_prompt.md`: 1 dòng rule gửi/đăng → clarify yes_no (nền v0) | Chặn gửi trực tiếp (R12). R12 đổi sang clarify nhưng `response_type` vẫn `text`; **không tăng điểm** | 0.90 (18/20) | 0.90 (18/20) | `runs/v2_B_base_anthropic_20261110T110945475237.json` |
| v3 | `tools.yaml`: mô tả `lookup.query` (nền v2) | Quy ước query không chứa thời gian / loại tin (R03). **Nhận** | 0.90 (18/20) | 0.95 (19/20) | `runs/v3_B_base_anthropic_20261110T111128550003.json` |
| v4 | `tools.yaml`: thêm 6 tool nhóm (16 tool) | Thêm tool không làm giảm routing. **Bác bỏ**: `resolve_time_range` được gọi trước rồi agent dừng | 0.95 (19/20) | 0.70 (14/20) | `runs/v4_B_base_anthropic_20261110T112615559413.json` |
| v5 | `tools.yaml`: mô tả `resolve_time_range` hẹp lại | Giảm gọi nhầm. Cải thiện một phần | 0.70 (14/20) | 0.85 (17/20) | `runs/v5_B_base_anthropic_20261110T112904543496.json` |
| v6 (**bản nộp**) | `tools.yaml`: mô tả `resolve_time_range` có ví dụ GỌI / KHÔNG GỌI | Ví dụ cụ thể sửa R03, R06, M02, R13. Còn R10, R12 | 0.85 (17/20) | 0.90 (18/20) | `runs/v6_B_base_anthropic_20261110T113121707961.json` |

Chi tiết từng dòng nằm trong `artifacts/version_log.csv` (hash prompt/tools, artifact_version).

## B2. Failure Analysis

Lỗi từ các run, lấy từ `results[*].result` của run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix / Trạng thái |
|---|---|---|---|---|
| R03_web_news_routing (v0–v2) | wrong_arg_value | `lookup(query="AI tin tức hôm nay", topic="news", timeframe="day")` | Mong đợi `query="AI"`, model đưa cả cụm thời gian vào query | Đã sửa ở v3 (mô tả `lookup.query`) |
| R12_confirm_before_send (v0–v6) | wrong_boundary | `clarify(question=..., response_type="text")` | Đã chuyển sang gọi `clarify` (v2), nhưng `response_type` là `text` thay vì `yes_no` | **Chưa sửa**. Khi chưa có nội dung cụ thể, `text` là hợp lý; grader chỉ so khớp field |
| R06_timeframe_arg, R13 (v4–v5) | wrong_tool | `resolve_time_range("tuần này")` rồi dừng; hoặc gọi trước `lookup` | Tool mới bị gọi nhầm trước tool tìm kiếm | Đã sửa ở v6 (ví dụ GỌI / KHÔNG GỌI) |
| R10_missing_handle (v4, v6) | missing_info | `timeline(screenname="elonmusk")` | Model tự đoán handle thay vì hỏi lại. v3 đạt case này | **Chưa sửa**. Là regression khi thêm tool, chưa xác định nguyên nhân chắc chắn |

## B3. Team Eval Cases

`data/eval_group.json` có 16 case do nhóm thêm: **10 single-turn, 6 multi-turn** (đạt yêu cầu ≥5 + ≥5).

**Các lần chạy group eval** (cùng 16 case, prompt/tools khác nhau):

| Lần chạy | case_accuracy | multiturn_accuracy | Ghi chú |
|---|---|---|---|
| v8 (case gốc) | 0.50 (8/16) | 0.17 | Trước khi sửa case; 5 case thiếu ngữ cảnh |
| v8 (case đã sửa ngữ cảnh) | 0.69 (11/16) | 0.57 | Cùng prompt/tools v8, chỉ đổi case |
| v9 (+ policy.query) | 0.81 (13/16) | 0.71 | Sửa G03, G07 |
| **v10** (+ rule send/save) | 0.88 (14/16) | 0.86 | **Bản hiện tại**. Sửa G10; G16 còn lỗi |

**Sửa case (không phải thay đổi prompt):** G06, G09, G10, G15, G16 là case thiếu ngữ cảnh: agent được yêu cầu đọc/gộp/gửi/lưu một thứ không có trong hội thoại, nên hỏi lại là hành vi đúng. Nhóm đã thêm vào lượt trước đoạn kết quả/nội dung mà case giả định (ghi trong `metadata.eval_fix`). Kỳ vọng (`expect`) không đổi. So sánh chính là v8 (case đã sửa) → v9 → v10.

**Bảng kết quả v10 theo case:**

| Case ID | Kiểm tra | Expected | Result (v10) |
|---|---|---|---|
| G01_social_search_topic | Tìm bài theo chủ đề | `social_search(query="Claude Opus")` | PASS |
| G02_papers_search | Tìm bài báo | `papers(query="retrieval-augmented generation")` | PASS |
| G03_policy_internal | Tra tài liệu nội bộ | `policy(query="hoàn tiền")` | PASS |
| G04_out_of_scope_code | Câu ngoài phạm vi | Không gọi tool | PASS |
| G05_fetch_url | Đọc URL cụ thể (arXiv abs) | `fetch(url="https://arxiv.org/abs/2005.11401")` | FAIL (`wrong_tool`): `paper_text` |
| G06_papers_then_text | Đọc text bài báo sau khi tìm | `paper_text` | PASS |
| G07_policy_followup | Tra chính sách (bảo hành) | `policy(query="bảo hành")` | PASS |
| G08_clarify_then_timeline | Map tên người thành handle | `timeline(screenname="karpathy")` | PASS |
| G09_fetch_then_no_tool | Đã đọc URL, không cần tool nữa | Không gọi tool | PASS |
| G10_send_after_confirm | Gửi sau xác nhận | `send(confirmed=True)` | PASS |
| G11_calculate_percent | Tính phần trăm | `calculate` | PASS |
| G12_time_range_week | Đổi "tuần này" thành ngày | `resolve_time_range` | PASS |
| G13_extract_links_paste | Lấy link từ đoạn dán | `extract_links` | PASS |
| G14_wiki_definition | Định nghĩa "X là gì" | `wiki_summary` | PASS |
| G15_dedupe_after_search | Gộp tin trùng sau khi tìm | `dedupe_items` | PASS |
| G16_save_note_needs_confirm | Lưu ghi chú cần xác nhận | `clarify(response_type="yes_no")` | FAIL (`wrong_boundary`): `clarify` |

**Lỗi còn lại (v10):**
- **G05** (`wrong_tool`): prompt yêu cầu `paper_text` khi đã có arXiv ID/URL, còn case kỳ vọng `fetch`. Đây là **mâu thuẫn giữa prompt và case**; nhóm cần quyết định bên nào đúng. Chưa sửa.
- **G16** (`wrong_boundary`): agent vẫn hỏi "tiêu đề" bằng `response_type=text` dù prompt v10 đã yêu cầu yes_no và không hỏi chi tiết tùy chọn. Rule trong prompt chưa đủ; cần thử hướng khác (ví dụ mô tả `save_note` trong `tools.yaml`) ở vòng sau.

**Hồi quy base:** eval cơ sở với v10 đạt case_accuracy 0.90 (18/20), bằng v8 và v9. File: `runs/v10_B_base_anthropic_20261110T145642595527.json`.

## B4. Live Chat Evidence

Transcript: `transcripts/v3_anthropic_20261110T111846041319.transcript.json` (chạy bằng `chat.py --provider anthropic --version v3`).

Lưu ý: transcript mang nhãn `v3` nhưng `tools_hash` là `c60d95b53e7c`, tức bản 16 tool **trước** khi sửa mô tả `resolve_time_range` ở v5/v6. Nên lượt 1 vẫn gọi `resolve_time_range` trước `lookup`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin AI hôm nay có gì nổi bật? Lấy 3 tin." | `resolve_time_range("hôm nay")` → `lookup(query="AI", topic="news", timeframe="day", max_results=3)` → `format(template="sections")` | prompt v2, tools hash c60d95b53e7c | Trả về 3 tin có link nguồn |
| 2 | "Tóm tắt lại 3 tin đó thành bản tin ngắn cho mình." | `format(template="brief")` | cùng artifact | Bản tin tóm tắt, có link |
| 3 | "Gửi bản tin này lên Telegram giúp mình." | `clarify(response_type="yes_no")` | cùng artifact | Hỏi xác nhận, **không gửi** |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | Transcript lượt 3 ở B4 | Agent hỏi xác nhận yes_no trước khi gửi, không gọi `send` | **Chưa gửi thật**: `.env` chưa có `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`. Tool có guard `confirmed=false` → `needs_confirmation` |
| arXiv / company policy | `tests/test_tools_todo.py` (unit test) | `policy` có test lọc theo `policy_area` và test tách nội dung kiểu prompt injection vào `untrusted_text` | Chưa có run eval riêng cho `papers` / `policy` |
| UI | (đã chạy, theo checklist) | UI chạy được | Link đã điền ở mục A1 (kiểm tra HTTP 200) |
| Tool unit tests | `pytest tests/` → 126 passed, 0 skipped | Thay 15 stub trong `test_tools_todo.py` bằng test thật (16 lần chạy, 1 test có tham số). Test chạy offline, chặn mạng thật | Chưa ghi nhận bug mới trong tool có sẵn. Chưa có ví dụ "unit test bắt được, eval không bắt được" đã xác minh |

Tool unit tests: đã viết 15 stub thành test thật (16 lần chạy). Toàn bộ suite 126 test, 0 skipped, 0 failed.

## B6. Reflection

- **Fix trong `system_prompt.md`:** rule gửi/đăng ở v2 làm model chuyển sang gọi `clarify` thay vì gửi trực tiếp. Nhưng prompt không kiểm soát được `response_type` (text hay yes_no), nên R12 vẫn lỗi.
- **Fix trong `tools.yaml`:** mô tả `lookup.query` (v3) sửa R03. Mô tả `resolve_time_range` có ví dụ GỌI / KHÔNG GỌI (v6) sửa R06, M02, R13. Đây là chỗ hiệu quả nhất trong lần tối ưu này.
- **Cần người xem tay thay vì tự chấm:** R12. Chọn `text` hay `yes_no` khi chưa có nội dung để xác nhận đều hợp lý. Eval chấm theo field nên báo lỗi, nhưng cần người xem để biết hành vi có đúng ý định không. Ngoài ra, G10 (single-turn, `send(confirmed=True)`) cần xem lại vì thiếu bước xác nhận.
- **Cải tiến tiếp:** (1) thêm 5 case multi-turn vào `eval_group.json` và chạy group suite; (2) chạy lặp để đo nhiễu, vì mỗi case chỉ chạy 1 lần; (3) mỗi version chỉ đổi một artifact. v1 vi phạm điều này; (4) cố định `tools.yaml` trong suốt một lần chạy. Trong lúc làm v3, file này bị sửa bởi một tiến trình khác, làm hash của v3 không khớp với file hiện tại.

## B7. Small Local Model Challenge (bonus)

Không làm trong lần nộp này. Chưa chạy model Ollama nào, nên không có bảng metric local.
