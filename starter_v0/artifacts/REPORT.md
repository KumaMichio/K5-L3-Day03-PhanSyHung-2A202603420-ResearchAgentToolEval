# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy bài đăng gần đây của một tài khoản | không |
| social_search | tìm bài đăng trên Twitter/X theo từ khoá | không |
| lookup | tra cứu thông tin trên internet / tin tức | không |
| fetch | đọc nội dung chi tiết từ một URL | không |
| format | trình bày dữ liệu đã có thành markdown digest | không |
| send | gửi text lên Telegram channel (khi đã xác nhận) | không |
| policy | tìm trong tài liệu nội bộ công ty | không |
| papers | tìm paper khoa học trên arXiv | không |
| paper_text | tải và trích xuất text từ bài báo arXiv | không |
| hn_search | tìm kiếm bài viết, thảo luận tech trên Hacker News | có (TV4) |
| citations | tra cứu số trích dẫn, venue, năm xuất bản paper qua OpenAlex | có (TV4) |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tests/test_tools_todo.py` | Kiểm tra token & chat_id, chỉ gửi khi `confirmed=True` | Chặn network call nếu `confirmed=False` |
| arXiv/company policy | `company_policy/`, `tests/` | Mock và query policy, filter area, tách `untrusted_text` | Prompt injection được cô lập vào `untrusted_text` |
| UI | `starter_v0/app.py` | Streamlit app chạy tương tác, log chi tiết từng round | Giới hạn max 4 rounds tránh loop vô tận |
| Tool unit tests (`tests/`) | `pytest tests/` (92 passed, 0 skipped, 0 failed) | 100% test xanh cho toàn bộ core tools + 2 tools mới | Mock offline bằng `fake_http`, không tốn credit API |
| Tool mới TV4 (`hn_search`, `citations`) | `tools/hn_search/`, `tools/citations/` | Không cần API key, gọi Algolia HN API và OpenAlex API | Kẹp limit 1-10, fallback 404 cho paper không tồn tại |

**Báo cáo Tool unit tests:**
- **Số test đã viết**: 20 unit tests hoàn chỉnh trong `test_tools_todo.py` (bao gồm 14 tests cho các core/bonus tools và 6 tests cho `hn_search` + `citations`).
- **Bug tìm được & sửa**: 
  1. Trong `hn_search`: Lỗi falsy check khi `limit=0` dẫn đến `0 or 5` trả về 5 thay vì bị kẹp thành 1. Đã sửa bằng ép kiểu an toàn và dùng `max(1, min(limit_int, 10))`.
  2. Trong `citations`: Xử lý ngoại lệ khi bài báo không tìm thấy (HTTP 404 hoặc `results: []`) trả về `items: []` thay vì crash unhandled.
  3. Trong `fetch`: Xác định chính xác hành vi cắt chuỗi 4000 ký tự không bị lỗi index.
- **Ví dụ lỗi unit test bắt được nhưng eval không bắt được**: 
  Model gọi đúng `hn_search(query="Rust", limit=0)` $\rightarrow$ eval routing báo PASS vì đúng tên tool và có gọi. Nhưng trong code thực tế nếu không có unit test kiểm tra `hitsPerPage` gửi lên Algolia thì `limit=0` sẽ bị lỗi gửi giá trị sai hoặc lấy sai số lượng kết quả. Unit test bắt được chính xác request HTTP gửi đi và assert `hitsPerPage == 1`.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
