# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Thành viên ghi trong [TEAM.md](../../TEAM.md).
- Provider/model: OpenRouter · `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tra cứu tin web, bài đăng trên X và bài nghiên cứu arXiv. Agent có thể đọc URL, gom các nguồn theo tên miền và trình bày kết quả kèm liên kết. Khi yêu cầu thiếu thông tin, agent hỏi để bổ sung trước khi tra cứu.

**Link dùng thử (deploy):**

Chạy demo trên máy local từ `starter_v0` bằng `python -m streamlit run app.py --server.address 127.0.0.1`. Mở [http://localhost:8501](http://localhost:8501) sau khi khởi động. Bản dùng thử có chế độ mã truy cập đã được kiểm thử. Link công khai đang chờ triển khai.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới? |
|---|---|---|
| `clarify` | Hỏi bổ sung thông tin hoặc yêu cầu xác nhận. | Không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X. | Không |
| `social_search` | Tìm bài đăng trên X theo chủ đề. | Không |
| `lookup` | Tìm thông tin hoặc tin tức trên web. | Không |
| `fetch` | Đọc nội dung của một URL web cụ thể. | Không |
| `format` | Trình bày những nguồn đã có thành bản tin Markdown. | Không |
| `policy` | Tra cứu bộ tài liệu chính sách mẫu trong repo. | Không |
| `papers` | Tìm bài nghiên cứu trên arXiv. | Không |
| `paper_text` | Trích văn bản từ bài arXiv đã xác định. | Không |
| `send` | Gửi bản tin lên Telegram từ CLI sau khi xác nhận. | Không |
| `source_inventory` | Gom URL đã có theo tên miền và loại URL trùng. | Có |

## A3. Câu hỏi mẫu để thử

1. Tìm ba tin web về robot hình người trong tuần này, kèm link nguồn.
2. Tóm tắt ba bài đăng mới nhất trên X giúp mình. Sau khi agent hỏi lại, trả lời “của @NASA”.
3. Đọc trang https://www.iana.org/help/example-domains và tóm tắt nội dung chính.
4. Gom theo tên miền các link https://example.com/a, https://example.com/b và https://example.org/c.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Kết quả theo phiên bản

Preflight OpenRouter trả lời gọi `timeline` đúng cấu trúc. Tavily, Firecrawl và hai endpoint Twitter API45 đều trả kết quả khi kiểm tra riêng. Bốn vòng base dùng cùng `openai/gpt-4o-mini` và cùng 20 case. Chi tiết hash và điểm trước/sau nằm trong [version log](version_log.csv).

| Phiên bản | Thay đổi và giả thuyết | Case pass | Routing | Args | Multi-turn | Bằng chứng |
|---|---|---:|---:|---:|---:|---|
| v0 | Đo prompt và khai báo tool gốc. | 14/20 | 75% | 70% | 100% | [Run v0](../runs/v0_B_base_openrouter_20261110T103345360306.json) |
| v1 | Quy tắc xử lý yêu cầu thiếu dữ kiện, ngoài phạm vi và yêu cầu đăng giúp tránh chọn nhầm tool. | 18/20 | 100% | 90% | 100% | [Run v1](../runs/v1_B_base_openrouter_20261110T103604787933.json) |
| v2 | Làm rõ quy ước tham số trong mô tả tool, dùng lại prompt v1 và giữ nguyên bộ 10 tool. | 18/20 | 100% | 90% | 83,33% | [Run v2](../runs/v2_B_base_openrouter_20261110T113630184121.json) |
| v3 | Ưu tiên xác nhận ý định đăng trước quy tắc hỏi khi thiếu dữ kiện, dùng lại đúng khai báo tool của v2. | 19/20 | 95% | 95% | 100% | [Run v3](../runs/v3_B_base_openrouter_20261110T113812149355.json) |

Các phép đo base dùng cùng bộ 10 tool. Snapshot trong `eval_versions/` giữ prompt `v1` cho `v2` và cùng khai báo tool cho `v2` và `v3`. Bộ eval nhóm và demo dùng khai báo đầy đủ trong `artifacts/tools.yaml` có thêm `source_inventory`. Hai run base cũ dùng chung khai báo có tool mới được giữ trong `runs/` làm bằng chứng thử nghiệm trước khi tách riêng phép đo.

`v2` sửa tham số `topic` của `R13` nhưng `M03` chọn sai handle, nên tổng điểm vẫn là 18/20. `v3` đạt 19/20 và `R12` chuyển sang `clarify(yes_no)`. Điểm routing giảm một case vì model chọn sai tool ở `R10`.

## B2. Phân tích lỗi

| Case v0 | Loại lỗi trong bộ đề | Điều quan sát được | Kết quả thay đổi |
|---|---|---|---|
| `R08` | `out_of_scope` | Gọi `send` cho câu hỏi nguyên hàm. | `v1` trả lời ngoài phạm vi mà không gọi tool. |
| `R10` | `missing_info` | Gọi `timeline` với `sama` khi người dùng chưa nói tài khoản. | `v1` hỏi lại với `clarify(text)`. |
| `R11` | `missing_info` | Gọi `fetch` với một URL do model tự đoán. | `v1` hỏi URL với `clarify(text)`. |
| `R12` | `wrong_boundary` | Chọn `send` khi chưa hỏi xác nhận. `v1` và `v2` chọn `clarify` nhưng truyền `text`. | `v3` chọn `clarify(yes_no)` và dừng. |
| `R13` | `wrong_tool` | Gọi đúng hai tool nhưng gửi `query="AI news"` và thiếu `topic="news"` cho `lookup`. | `v1` sửa được query. `v2` bổ sung đúng `topic`. |
| `R14` | `out_of_scope` | Gọi `send` với lời giải lập trình. | `v1` giữ yêu cầu ngoài phạm vi khỏi tool. |

Trong `v2`, `M03` truyền `AndrejKarpathy` thay vì `karpathy`, dù giữ đúng `limit=3`. `M03` pass ở `v3`. Case còn lỗi ở `v3` base là `R10`. Model chọn `social_search` với truy vấn rỗng thay vì hỏi tên tài khoản. Việc gửi Telegram được tắt trong các lượt đo.

## B3. Bộ eval nhóm

Lượt chạy bổ sung với cấu hình `v2` theo checkpoint trong slide đạt **8/10**, routing **90%**, args **80%** và multi-turn **80%**. `G05` gọi `clarify` cho yêu cầu đặt vé ngoài phạm vi. `GM02` đổi bộ lọc từ `news` sang `general` khi chỉ được yêu cầu đổi khoảng thời gian. [Run nhóm v2](../runs/v2_B_group_openrouter_20261110T114607812057.json)

Bộ nhóm gồm 5 single-turn và 5 multi-turn, dùng cấu hình có `source_inventory` và đạt **9/10**, routing **100%**, args **90%** và multi-turn **80%**. [Run nhóm v3](../runs/v3_B_group_openrouter_20261110T104023600219.json)

| Case | Kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|
| `G01` | Gom URL đã có | `source_inventory` với hai URL | Pass |
| `G02` | Chuẩn hóa handle và số bài | `timeline` với `NASA`, `limit=2` | Pass |
| `G03` | Tin theo tháng và số kết quả | `lookup` với `news`, `month`, `max_results=3` | Pass |
| `G04` | Tìm theo ngày nộp arXiv | `papers` với `submittedDate`, `max_results=2` | Pass routing và args. arXiv trả lỗi kết nối. |
| `G05` | Đặt vé ngoài phạm vi | Không gọi tool | Pass |
| `GM01` | Sửa URL ở lượt cuối | `fetch` với URL mới | Pass |
| `GM02` | Đổi thời gian, giữ bộ lọc | `lookup` giữ `news`, đổi sang `week` | Fail. Model đổi `news` thành `general`. |
| `GM03` | Đổi cách sắp xếp bài X | `social_search` với `Latest`, `limit=4` | Pass |
| `GM04` | Giữ và bổ sung URL qua các lượt | `source_inventory` với ba URL | Pass |
| `GM05` | Hủy một yêu cầu đăng đang chờ | Không gọi tool | Pass |

## B4. Chat trực tiếp

Bốn lượt dùng `chat.py` với `v3` và OpenRouter. [Transcript](../transcripts/v3_openrouter_20261110T104015149987.transcript.json)

| Lượt | Yêu cầu | Tool | Kết quả |
|---|---|---|---|
| 1 | Tìm 2 tin về robot công nghiệp trong tuần | `lookup` | Trả 2 kết quả kèm liên kết. |
| 2 | Tóm tắt 3 bài X nhưng chưa nêu tài khoản | Không gọi tool | Hỏi tên tài khoản bằng văn bản. |
| 3 | Bổ sung `@NASA` | `timeline` | Giữ `limit=3`, trả tóm tắt 3 bài kèm link. |
| 4 | Đề nghị đăng nội dung mẫu lên Telegram | Không gọi tool | Hỏi xác nhận bằng văn bản, dừng trước khi gửi. |

Eval buộc model trả lời bằng tool ở các case yêu cầu tool. Trong chat trực tiếp, model hỏi lại bằng văn bản ở lượt 2 và 4. Case `R12` của run `v3` base chọn `clarify` với `response_type="yes_no"`.

## B5. Kiểm tra code và demo

- `pytest` chạy offline với **99 passed**, **0 failed**, **0 skipped**. Test `source_inventory` kiểm tra gom nhóm, loại trùng, sai kiểu và URL lỗi. Test lịch sử kiểm tra mở lại cơ sở dữ liệu, tách cuộc trò chuyện và giữ ảnh cùng tin nhắn. Các bài test HTTP dùng phản hồi giả lập.
- Test hồi quy của `send` kiểm tra rằng chuỗi `"false"` không được dùng như xác nhận. Code chỉ chấp nhận boolean `True` và che bot token trong thông báo lỗi. Unit test kiểm tra hành vi thực thi mà eval routing không chấm.
- `app.py` dùng Streamlit và vòng chat chung. UI giới hạn tool theo danh sách dành cho phiên demo. Khi bật `RESEARCH_DEMO_ACCESS_CODE`, app yêu cầu mã trước khi hiện chat và dùng cố định `openai/gpt-4o-mini`. Kiểm thử local xác nhận mã sai bị từ chối và mã đúng cho phép chạy OpenRouter cùng `source_inventory`.
- Streamlit local lưu các lượt đã trả lời trong SQLite. Người dùng bấm trực tiếp tên cuộc chat trong thanh bên để mở và tiếp tục trao đổi. Phiên demo có mã truy cập giữ chat riêng trong bộ nhớ của từng phiên.

## B6. Rút kinh nghiệm

- Quy tắc xác nhận, ưu tiên ý định ở lượt cuối và hỏi lại khi thiếu dữ kiện thuộc `system_prompt.md`. Cách biểu diễn `topic`, `timeframe`, `search_type` và handle thuộc `tools.yaml`.
- `R13` có nhãn bài tập `wrong_tool` nhưng log cho thấy sai args. `G04` pass theo bộ chấm dù dịch vụ arXiv báo lỗi kết nối. Cần đọc `observed_mismatch` và `tool_results` để phân biệt các tình huống này.
- Giả thuyết của `v3` xuất phát từ lỗi xác nhận ở `R12` trong eval base `v2`. Bằng chứng thử chéo giữa các nhóm đang chờ link demo chia sẻ.
- Kết quả gợi ý kiểm tra thêm các yêu cầu thiếu tên tài khoản, ánh xạ tên hiển thị sang handle và cách giữ bộ lọc `news` khi người dùng chỉ đổi thời gian. Mỗi dòng trong bảng chính lấy từ một lượt đo, nên kết quả từng case có thể biến động giữa các lần chạy.

## B7. Small Local Model Challenge (bonus)

Phạm vi lần chạy này là model cloud OpenRouter. Bonus Ollama để trống.
