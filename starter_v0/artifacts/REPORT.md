# Day 03 Lab — Research Agent Report

## Team

- Team: Chưa điền
- Members: Chưa điền
- Provider/model dùng cho base eval: OpenAI / ghi model trong từng run JSON

## PHẦN A — Giới thiệu agent

### A1. Agent làm được gì

Research Agent định tuyến yêu cầu nghiên cứu tới công cụ phù hợp: tìm bài đăng trên X, tra cứu web, đọc URL, tìm bài báo arXiv, tra cứu policy nội bộ, định dạng hoặc loại kết quả trùng lặp. Agent có thể hỏi lại khi thiếu thông tin bắt buộc. Gửi Telegram là hành động có tác động bên ngoài và cần xác nhận theo quy tắc của agent.

**Link demo:** Chưa triển khai; chạy UI cục bộ bằng `streamlit run app.py` từ thư mục `starter_v0/`.

### A2. Công cụ

| Tool | Chức năng | Tool nhóm tự thêm? |
|---|---|---|
| clarify | Hỏi người dùng để lấy thông tin còn thiếu hoặc xác nhận | Không |
| timeline | Lấy bài đăng gần đây của tài khoản X được nêu tên | Không |
| social_search | Tìm bài đăng trên X theo chủ đề/từ khóa | Không |
| lookup | Tìm kiếm web, gồm tin tức theo chủ đề và khoảng thời gian | Không |
| fetch | Đọc nội dung từ URL được cung cấp | Không |
| format | Chuyển các kết quả đã thu thập thành digest Markdown | Không |
| send | Gửi nội dung lên Telegram sau xác nhận | Không |
| policy | Tìm trong tài liệu policy nội bộ | Không |
| papers | Tìm bài nghiên cứu trên arXiv | Không |
| paper_text | Trích xuất nội dung văn bản từ bài arXiv | Không |
| dedupe | Loại các item trùng URL, giữ item xuất hiện đầu tiên và thứ tự ban đầu | Có |

### A3. Câu hỏi mẫu để demo

1. “Tìm tin tức AI trong ngày hôm nay.”
2. “Tìm bài đăng gần đây của Sam Altman trên X.”
3. “Đọc URL này và tóm tắt các ý chính: `<dán URL>`.”
4. “Tìm các bài nghiên cứu arXiv về RAG.”
5. “Loại các kết quả trùng URL trong danh sách này: `<dán danh sách>`.”

## PHẦN B — Chi tiết và bằng chứng

### B1. Kết quả version

Số liệu lấy từ JSON run. `v3` ghi nhận run cuối cùng hiện có, đạt 20/20; các run v3 trước đó vẫn nằm trong `runs/` để đối chiếu lịch sử.

| Version | Thay đổi | Giả thuyết | Metric trước | Metric sau | Run được ghi nhận |
|---|---|---|---|---|---|
| v0 | Baseline starter artifacts | Đo chất lượng prompt/tool ban đầu | — | case 0.70; routing 0.75; arguments 0.70; multiturn 1.00 | `runs/v0_B_base_openai_20261110T102647452815.json` |
| v1 | Prompt, tool declarations, tool `dedupe` | Routing rõ ràng và quy tắc hỏi lại/xác nhận sẽ giảm gọi sai hoặc gọi thiếu | case 0.70; routing 0.75; arguments 0.70; multiturn 1.00 | case 0.70; routing 0.80; arguments 0.70; multiturn 0.8333 | `runs/v1_B_base_openai_20261110T104420162849.json` |
| v2 | System prompt | Nêu rõ xử lý thông tin thiếu, mapping handle đã biết và ưu tiên lựa chọn nguồn mới nhất | case 0.70; routing 0.80; arguments 0.70; multiturn 0.8333 | case 0.80; routing 0.85; arguments 0.80; multiturn 0.6667 | `runs/v2_B_base_openai_20261110T124300117483.json` |
| v3 | System prompt: duy trì một nguồn đang hoạt động, hủy nguồn cũ khi người dùng đổi nguồn | Quy tắc trạng thái nguồn qua nhiều lượt sẽ ngăn gọi thêm tool của nguồn đã bị hủy | case 0.80; routing 0.85; arguments 0.80; multiturn 0.6667 | case 1.00; routing 1.00; arguments 1.00; multiturn 1.00 | `runs/v3_B_base_openai_20261110T125821521307.json` |

Run v3 được ghi nhận có 20 case đo được, 0 lỗi provider, 20 case pass và không có mismatch. Kết quả này chứng minh pass bộ `eval_base.json` hiện tại với cấu hình run ghi trong JSON; không đảm bảo mọi yêu cầu ngoài bộ eval đều đúng.

### B2. Phân tích lỗi

| Version/case | Loại lỗi | Quan sát | Hướng sửa | Kết quả sau sửa |
|---|---|---|---|---|
| v0 — R08, R14 | `out_of_scope` | Agent gọi tool cho yêu cầu ngoài phạm vi | Bỏ chỉ dẫn đoán và gọi tool; nêu rõ ranh giới phạm vi | v3 base pass |
| v0 — R10, R11 | `missing_info` | Agent tự chọn handle/URL thay vì hỏi lại | Quy tắc `clarify` khi thiếu thông tin bắt buộc | v3 base pass |
| v0 — R12 | `wrong_boundary` | Gửi nội dung khi chưa xác nhận đúng cách | Yêu cầu xác nhận rõ trước hành động gửi | v3 base pass |
| v0 — R13 | `wrong_tool` | Dùng tool X thay vì kết hợp đúng nguồn web và X | Quy tắc định tuyến theo nguồn được yêu cầu | v3 base pass |
| v2 — R10 | `missing_info` | Gọi `timeline` dù thiếu tài khoản | Làm rõ trường bắt buộc trước khi gọi tool | v3 base pass |
| v2 — R12 | `wrong_boundary` | `clarify` dùng `response_type="text"` thay vì `yes_no` | Nêu chính xác loại phản hồi cần cho xác nhận | v3 base pass |
| v2 — M02 | `wrong_tool` / `wrong_arg_value` | Chọn `social_search`, thiếu `lookup` cần thiết | Giữ nguồn web đang hoạt động qua lượt đổi chủ đề | v3 base pass |
| v2 — M06 | `wrong_tool` | Gọi thêm `social_search` sau khi người dùng hủy nguồn X | Đổi nguồn phải hủy nguồn cũ; chỉ định tuyến theo yêu cầu đã giải quyết | v3 base pass |

Các phân loại v0/v1 được tóm tắt từ kết quả trao đổi trước và version log; chi tiết chắc chắn có thể kiểm tra lại trong run JSON tương ứng. Hai run v2/v3 được đọc trực tiếp trong lần cập nhật report này.

### B3. Eval nhóm

README yêu cầu 10 case (5 single-turn và 5 multi-turn). Hiện `data/eval_group.json` chỉ có **1 case**, chưa đủ yêu cầu; chưa có run group để báo kết quả.

| Case ID | Nội dung kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| G01_dedupe_research_items | Định tuyến yêu cầu loại item trùng URL và giữ thứ tự | Gọi `dedupe` với danh sách đầu vào | Chưa chạy group eval |
| G02–G10 | Chưa được tạo | Cần bổ sung 4 single-turn và 5 multi-turn để đủ 10 case | Chưa có |

### B4. Bằng chứng live chat

Chưa có thư mục/file `transcripts/*.transcript.json` trong repo tại thời điểm cập nhật. Vì vậy chưa thể ghi nhận 3 lượt chat live; cần chạy `chat.py` ít nhất 3 lượt và lưu transcript để hoàn tất mục này.

| Lượt | Yêu cầu | Tool call | Phiên bản | Kết quả |
|---|---|---|---|---|
| Chưa có | Chưa có transcript | — | — | Chưa thực hiện/không có bằng chứng lưu |

### B5. Bằng chứng khác

| Hạng mục | Bằng chứng hiện có | Trạng thái |
|---|---|---|
| UI | `app.py` có trong repo; chưa có URL demo được ghi nhận | Code có; cần xác nhận chạy và cung cấp link nếu yêu cầu demo ngoài máy |
| Tool mới | `tools/dedupe/`, đăng ký trong `tools/__init__.py` và khai báo trong `artifacts/tools.yaml` | Có |
| Unit test tool mới | `tests/test_dedupe_tool.py` | Có file test; trạng thái chạy test cần ghi từ kết quả `pytest` |
| Send confirmation | Quy tắc trong system prompt và tool declaration | Được đánh giá trong base eval; run v3 pass |

### B6. Reflection

- Prompt phù hợp để quy định cách hiểu ngữ cảnh, chọn nguồn, hỏi lại khi thiếu thông tin và duy trì lựa chọn qua nhiều lượt.
- `tools.yaml` phù hợp để mô tả chức năng, điều kiện dùng/không dùng và convention của arguments; tool mới phải đồng bộ với registry.
- Eval tự động giúp phát hiện tool/argument thừa hoặc thiếu, nhưng các hành động có tác động bên ngoài như gửi Telegram vẫn cần guardrail và kiểm tra thủ công.
- Hướng tiếp theo: bổ sung đủ 10 eval nhóm, chạy suite group, kiểm tra unit tests không skip, lưu transcript live chat và hoàn thiện thông tin nhóm/link demo.

### B7. Small Local Model Challenge (bonus)

Chưa thực hiện/không có run Ollama được ghi nhận trong repo.
