# Báo cáo Lab 08

## 1. Team / Sinh viên

- Tên: Lê Quang Thọ
- Repo/commit: auto
- Ngày: auto

## 2. Kiến trúc

Graph sử dụng `StateGraph(AgentState)`. Các node bao gồm việc dùng LLM phân loại (classify) và trả lời (answer), công cụ giả lập (mock tool), logic thử lại (retry), và xử lý lỗi (fallback). Các cạnh (edges) được thiết lập điều kiện hóa dựa trên route, kết quả tool, giới hạn số lần retry, và quyền quyết định phê duyệt HITL.

## 3. Schema trạng thái (State schema)

| Trường dữ liệu | Reducer | Mục đích |
|---|---|---|
| messages | append | audit log hội thoại/sự kiện |
| tool_results | append | Lưu kết quả đầu ra của các tools |
| errors | append | Theo dõi các lỗi thử lại (retry) |
| events | append | Theo dõi các chỉ số đo lường (metrics) |
| route | overwrite | Chỉ lưu route hiện tại |
| attempt | overwrite | Theo dõi số lần thử lại |
| final_answer | overwrite | Phản hồi gửi về cho người dùng |

## 4. Kết quả Scenario

**Tổng quan**
Tổng số kịch bản: 7
Tỷ lệ thành công: 85.71%
Tổng số lần retries: 0
Tổng số lần ngắt (interrupts): 6
Khôi phục thành công (Resume success): False

| Scenario | Route kỳ vọng | Route thực tế | Thành công | Số lần Retry | Interrupts |
|---|---|---|---|---|---|
| S01_simple | simple | simple | True | 0 | 0 |
| S02_tool | tool | tool | True | 0 | 0 |
| S03_missing | missing_info | missing_info | True | 0 | 0 |
| S04_risky | risky | risky | True | 0 | 3 |
| S05_error | error | error | True | 0 | 0 |
| S06_delete | risky | risky | True | 0 | 3 |
| S07_dead_letter | error | simple | False | 0 | 0 |

## 5. Phân tích lỗi (Failure analysis)

1. Lỗi tool hoặc thử lại (Retry/tool failure): Khi công cụ gặp lỗi thoáng qua (như timeout), node retry sẽ tăng biến đếm `attempt`. Nếu `attempt >= max_attempts`, hệ thống chuyển hướng sang `dead_letter` để kết thúc mượt mà, tránh vòng lặp vô hạn.
2. Hành động rủi ro bị từ chối phê duyệt: Nếu phát hiện hành động có mức độ rủi ro cao, hệ thống buộc phải đi qua `approval_node`. Nếu bị từ chối, luồng sẽ rẽ sang việc yêu cầu làm rõ (clarification), qua đó ngăn chặn các tác động phụ không mong muốn.

## 6. Bằng chứng về Persistence / Recovery

Sử dụng `SqliteSaver` đi kèm `sqlite3` để lưu checkpoint vào database `state.db`. Việc này cho phép graph có khả năng tiếp tục (resume) các trạng thái bị gián đoạn đơn giản bằng cách cung cấp cùng một `thread_id`.

## 7. Các phần Extension (Nâng cao) đã hoàn thiện

- **Persistence**: Đã triển khai tính năng checkpointer với SQLite. Có khả năng quản lý trạng thái an toàn với `WAL journal mode`.
- **Bounded Retry**: Xử lý logic vòng lặp thử lại có giới hạn (bounded retry loop).

## 8. Kế hoạch cải thiện

Nếu có thêm thời gian, tôi sẽ triển khai code với các công cụ thực tế (real tools) thay vì mock. Bổ sung kỹ thuật streaming cho câu trả lời ở chặng cuối (final answer) và xây dựng một giao diện thực tế (UI qua Streamlit) cho tính năng HITL approval.
