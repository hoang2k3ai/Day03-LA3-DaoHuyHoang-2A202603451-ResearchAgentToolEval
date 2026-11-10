# Research Agent — Report

## Phần A — Giới thiệu agent

### Agent làm được gì?

Research Agent hỗ trợ tra cứu bài đăng trên X, tìm tin trên web, đọc một URL cụ thể, tổng hợp nguồn thành bản tin và tra cứu tài liệu nội bộ hoặc bài báo khoa học. Agent có thể hỏi lại khi thiếu thông tin và cần xin xác nhận trước khi gửi hoặc đăng nội dung.

### Công cụ

| Tool | Chức năng |
|---|---|
| `timeline` | Lấy bài đăng gần đây của một tài khoản X theo handle và số lượng. |
| `social_search` | Tìm bài đăng trên mạng xã hội theo từ khóa, sắp xếp Latest hoặc Top. |
| `lookup` | Tìm thông tin trên web; hỗ trợ chủ đề general/news và khoảng thời gian. |
| `fetch` | Đọc nội dung từ URL người dùng cung cấp. |
| `format` | Trình bày các kết quả đã có thành bản tóm tắt, mục hoặc danh sách. |
| `clarify` | Hỏi người dùng để bổ sung thông tin còn thiếu hoặc xác nhận hành động. |
| `send` | Gửi văn bản sau khi người dùng xác nhận. |
| `policy` | Tìm trong tài liệu chính sách nội bộ. |
| `papers` | Tìm bài báo khoa học. |
| `paper_text` | Lấy phần văn bản của bài báo khoa học. |

### Câu hỏi mẫu để thử

- “Tweet mới nhất của Sam Altman là gì?”
- “Mọi người đang bàn gì về GPT-5 trên Twitter?”
- “Tìm tin AI hôm nay trên web.”
- “Tóm tắt bài viết này: https://example.com/article”
- “Tìm bài báo khoa học về RAG.”

**Link dùng thử:** Chưa có URL demo được ghi nhận.

## Phần B — Chi tiết và bằng chứng

### B1. Baseline v0

| Trường | Giá trị |
|---|---|
| Provider / model | OpenAI / `gpt-4o-mini` |
| Suite | `base` (`data/eval_base.json`) |
| Thời điểm chạy | 2026-11-10 20:25:36 |
| Run | [`v0_B_base_openai_20261110T202536717156.json`](../runs/v0_B_base_openai_20261110T202536717156.json) |
| Artifact version | `v0+p6ca78408f49a+tf71232caf426` |
| Prompt hash | `6ca78408f49a818a30a8ca993bb669bb104cc1b714684f296603d6168f5162e0` |
| Tools hash | `f71232caf426c50ff86bb01dc6a256f437b4fc125b7e3b30a78869a6880fd3fd` |
| Kết quả | 14/20 pass; case accuracy 0.70; tool routing 0.75; argument accuracy 0.70; multiturn accuracy 1.00; 0 provider errors. |

Lệnh chạy: `python run_eval.py --provider openai --version v0 --suite base --eval-cases data/eval_base.json`.

### B2. Phân tích các case thất bại

| Case | Loại lỗi | Quan sát trong run | Hướng cải thiện |
|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | Gọi `send` với lời giải tích phân thay vì từ chối yêu cầu ngoài phạm vi. | Nêu rõ phạm vi agent; không dùng `send` để trả lời nội dung thông thường. |
| `R10_missing_handle` | `missing_info` | Tự chọn tài khoản `sama` khi người dùng chỉ yêu cầu tóm tắt 5 tweet mà không nêu tài khoản. | Bắt buộc hỏi handle bằng `clarify` nếu thiếu người/tài khoản. |
| `R11_missing_url` | `missing_info` | Tự đoán `https://example.com/article` cho “bài viết này”. | Bắt buộc xin URL khi chưa được cung cấp. |
| `R12_confirm_before_send` | `wrong_boundary` | Gọi `send` ngay với nội dung “Bản tin này”, không xin xác nhận. | Yêu cầu xác nhận yes/no trước mọi hành động gửi/đăng. |
| `R13_parallel_web_and_tweets` | `wrong_tool` / sai argument | Đã gọi cả `lookup` và `social_search`; truy vấn web là `AI news` thay vì `AI` và thiếu `topic: news`. | Giữ query chủ đề `AI`, đặt topic news và vẫn thực hiện cả hai nhánh tìm kiếm độc lập. |
| `R14_out_of_scope_coding` | `out_of_scope` | Dùng `send` để cung cấp mã Fibonacci thay vì từ chối yêu cầu lập trình ngoài phạm vi. | Nêu rõ agent không viết code tổng quát; tránh dùng tool gửi cho câu trả lời này. |

### B3. Tổng hợp mismatch

Run ghi nhận 2 `unexpected_tool_call`, 3 `missing_tool_call` và 1 `wrong_arg_value`. Các lỗi tập trung ở ba điểm: system prompt v0 khuyến khích đoán khi thiếu dữ liệu, ranh giới xác nhận gửi chưa được tuân thủ, và phạm vi agent chưa được giới hạn rõ. Bốn case multiturn đều pass (multiturn accuracy 1.00).

### B4. Eval cases

Đánh giá dùng bộ cố định `data/eval_base.json`, gồm 20 case. Danh sách và kỳ vọng của từng case nằm trong run JSON được dẫn ở B1; không chỉnh sửa bộ eval cho báo cáo này.

### B5. Kiểm tra lỗi tool

Chưa có kết quả kiểm tra hoặc regression test về bug nội tại của tool được ghi nhận trong run v0 này.

### B6. Live chat và reflection

Chưa có transcript live chat nào được ghi nhận. Baseline cho thấy các câu hỏi có đủ thông tin và hội thoại nhiều lượt đạt tốt, nhưng prompt v0 còn chỉ dẫn đoán thông tin, trái với hành vi cần cho các case thiếu handle/URL và xác nhận gửi. Ưu tiên sửa prompt và mô tả tool theo các lỗi B2, sau đó chạy lại cùng bộ eval để so sánh trên cùng thước đo.

### B7. So sánh phiên bản / model

| Phiên bản | Provider/model | Suite | Kết quả | Run |
|---|---|---|---|---|
| v0 | OpenAI / `gpt-4o-mini` | base | 14/20 (0.70) | [`v0_B_base_openai_20261110T202536717156.json`](../runs/v0_B_base_openai_20261110T202536717156.json) |

Chưa có run v1–v3 hoặc local model trong `version_log.csv`; vì vậy chưa thể lập so sánh tiến triển hay kết luận về hiệu quả của các thay đổi.
