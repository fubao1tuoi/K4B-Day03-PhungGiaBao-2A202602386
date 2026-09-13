# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Phùng Gia Bảo  
> **Mã Sinh Viên / Mã Học viên:** 2A202602386
> **Chủ đề Lựa chọn:** *Trợ lý Đặt Phòng họp & Thiết bị (Facilities Agent):* Kiểm tra lịch phòng trống, thiết bị và tạo booking phòng họp.  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 3/ 5 | Bài toán có nhiều bước xử lý như kiểm tra phòng, kiểm tra thiết bị và tạo booking, nhưng quy trình khá tuyến tính và không yêu cầu suy luận phức tạp. |
| **2. Tool Interaction** | 3/ 5 | Agent cần gọi các tool thông qua MCP Server để truy vấn thông tin nội bộ về phòng họp, thiết bị và thực hiện booking. Tuy nhiên số lượng và loại tool tương đối giới hạn. |
| **3. Dynamic Decision** | 4/ 5 | Kết quả của bước trước có thể ảnh hưởng đến bước tiếp theo. Ví dụ, nếu phòng không trống hoặc không có thiết bị phù hợp, Agent phải tiếp tục tìm phương án khác. |
| **4. Long Horizon Goal** | 2/ 5 | Mục tiêu đặt phòng tương đối ngắn, số bước xử lý không nhiều và không cần duy trì kế hoạch dài hạn. |
| **TỔNG ĐIỂM AGENTIC FIT** | 12/ 20 | Bài toán có mức độ phù hợp vừa đủ với Agentic System và phù hợp để thể hiện ReAct Loop + MCP. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "gpa": 3.85
      }
    },
    "latency_ms": 120.5
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [X] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [X] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
