# So sánh các version v0 → v4

Model: `openai/gpt-4o-mini` qua OpenRouter. Mỗi version chỉ đổi **một file** và kiểm **một giả thuyết**, nên mức tăng điểm gắn được với đúng thay đổi đó.
Nguồn số liệu: `artifacts/version_log.csv` và các file trong `runs/`.

## 1. Tổng quan

| Version | File đổi | Artifact version | Giả thuyết (tóm tắt) | Base case_accuracy | Group |
|---|---|---|---|---:|---:|
| v0 | (không đổi gì) | `v0+peb1c8179815b+t5b22a2476d41` | Đo hành vi gốc của prompt và tools starter | **0.65** (13/20) | — |
| v1 | `system_prompt.md` | `v1+p9352321c7609+t5b22a2476d41` | Lỗi hành vi do prompt starter cố tình ra lệnh xấu | **0.85** (17/20) | — |
| v2 | `tools.yaml` | `v2+p9352321c7609+t151898fd033d` | Lỗi chọn tool và args do mô tả tool sơ sài | **0.90** (18/20) | 0.90 (9/10) |
| v3 | `system_prompt.md` | `v3+pe20a0025fb65+t151898fd033d` | Model làm theo suy đoán thay vì câu chữ của user | **1.00** (20/20) | 0.90 (9/10) |
| v4 | `system_prompt.md` | `v4+pfc14bea47ff2+t151898fd033d` | Câu ngoài phạm vi bị xử lý không nhất quán vì rule chỉ liệt kê ví dụ | 1.00 (20/20) | 1.00 (10/10)* |

Hash trong artifact version chứng minh mỗi bước chỉ đổi một file:
- v0 → v1: `p…` đổi, `t…` giữ nguyên.
- v1 → v2: `t…` đổi, `p…` giữ nguyên.
- v2 → v3 và v3 → v4: `p…` đổi, `t…` giữ nguyên.

\* G04 pass ở v4 nhưng chạy lại 3 lần chỉ 2/3, nên chưa ổn định.

### Chi tiết metric (bộ base, 20 case)

| Version | case_accuracy | tool_routing | argument | multiturn |
|---|---:|---:|---:|---:|
| v0 | 0.65 | 0.75 | 0.65 | 1.00 |
| v1 | 0.85 | 0.95 | 0.85 | 0.83 |
| v2 | 0.90 | 0.95 | 0.90 | 0.83 |
| v3 | 1.00 | 1.00 | 1.00 | 1.00 |
| v4 | 1.00 | 1.00 | 1.00 | 1.00 |

## 2. Case fail qua từng version

✗ = fail, ✓ = pass.

| Case | Kiểm tra gì | v0 | v1 | v2 | v3 | v4 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| R03 | Tin AI hôm nay: `query="AI"`, `topic=news` | ✗ | ✓ | ✓ | ✓ | ✓ |
| R08 | Câu toán, ngoài phạm vi: không gọi tool | ✗ | ✓ | ✓ | ✓ | ✓ |
| R10 | Thiếu handle: phải `clarify` | ✗ | ✓ | ✓ | ✓ | ✓ |
| R11 | Thiếu URL: phải `clarify` | ✗ | ✓ | ✓ | ✓ | ✓ |
| R12 | Đăng Telegram: `clarify` `yes_no` trước | ✗ | ✗ | ✗ | ✓ | ✓ |
| R13 | Web và tweet song song, `topic=news` | ✗ | ✗ | ✓ | ✓ | ✓ |
| R14 | Viết code, ngoài phạm vi: không gọi tool | ✗ | ✓ | ✓ | ✓ | ✓ |
| M06 | "Bỏ Twitter" thì chuyển sang `lookup` news | ✓ | ✗ | ✗ | ✓ | ✓ |
| G04 (group) | Hỏi số trích dẫn theo tên paper | — | — | ✗ | ✗ | ✓* |

---

## 3. v0: Baseline

**Thay đổi:** không có. Dùng nguyên prompt và `tools.yaml` của starter. Prompt starter cố tình chứa chỉ dẫn xấu: đoán thay vì hỏi, gửi không cần xác nhận, ép làm trong một bước.

**7 case fail:**

| Case | Loại lỗi | Model làm gì |
|---|---|---|
| R03 | wrong_arg_value | `lookup(query="AI news")`: nhét "news" vào query |
| R08 | out_of_scope | `send(text="Nguyên hàm của x^2 là …")`: dùng Telegram để trả lời bài toán |
| R10 | missing_info | `timeline(screenname="sama")`: tự đoán account |
| R11 | missing_info | `fetch(url="https://example.com/article")`: bịa URL |
| R12 | wrong_boundary | `send(text="Bản tin này")`: gửi ngay, không hỏi xác nhận |
| R13 | wrong_arg_value | `lookup(query="AI news")`, thiếu `topic=news` |
| R14 | out_of_scope | `send(text="def fibonacci…")`: dùng Telegram để trả lời câu viết code |

**Nhận xét:** 5/7 lỗi (R08, R10, R11, R12, R14) là lỗi **hành vi**, đến thẳng từ các chỉ dẫn xấu trong prompt. 2 lỗi còn lại (R03, R13) là lỗi **args**.

---

## 4. v1: Viết lại `system_prompt.md`

**Giả thuyết:** bỏ các chỉ dẫn xấu và thay bằng rule rõ ràng thì sẽ sửa được các lỗi hành vi.

**Thay đổi:** bỏ 3 chỉ dẫn xấu của starter, thêm 4 nhóm rule:
1. **Ask instead of guessing:** thiếu account hoặc URL thì gọi `clarify` với `response_type="text"`. Không tự chọn account, không bịa URL.
2. **Confirm before sending:** muốn `send` thì phải `clarify` với `response_type="yes_no"` trước, và chỉ gọi `send(confirmed=true)` sau khi user nói có. Không dùng `send` để trả lời user.
3. **Stay in scope:** toán, code, công thức nấu ăn thì không gọi tool, trả lời ngắn bằng text. Câu hỏi về chính agent cũng trả lời bằng text.
4. **Use as many tools as the request needs:** yêu cầu có nhiều phần thì gọi đủ tool trong cùng một lượt.

**Kết quả:** 0.65 → **0.85**. R03, R08, R10, R11, R14 pass.

**Còn fail (3):**

| Case | Model làm gì | Vì sao |
|---|---|---|
| R12 | `clarify(response_type="text")` hỏi "muốn đăng nội dung gì" | Đã hỏi trước khi gửi, nhưng hỏi nội dung chứ không hỏi xác nhận |
| R13 | `lookup(query="AI")`, thiếu `topic=news` | Mô tả tool không nói khi nào dùng `topic=news` |
| M06 | Chỉ gọi `social_search` ở lượt cuối | **Regression** so với v0: đã bị bảo "bỏ Twitter" mà model vẫn quay lại Twitter |

---

## 5. v2: Viết lại `tools.yaml`

**Giả thuyết:** lỗi còn lại nằm ở chọn tool và args, vì mô tả tool của starter quá mơ hồ. Prompt giữ nguyên để đo riêng tác động của `tools.yaml`.

**Thay đổi:**
- Mỗi tool có mô tả đủ 3 phần: **làm gì / khi nào dùng / khi nào KHÔNG dùng**, và chỉ sang tool đúng.
- Quy ước args ghi trong description của từng param:
  - `query` chỉ là chủ đề; không thêm "news", "tin tức", ngày tháng
  - `topic="news"` khi hỏi tin tức
  - `timeframe`: hôm nay → `day`, tuần này → `week`, tháng này → `month`
  - handle không có `@` (`sama`, `karpathy`, `elonmusk`)
  - `search_type`: `Top` cho bài nổi bật, `Latest` cho bài mới
  - `clarify` dùng `yes_no` khi xác nhận gửi
  - `send` chỉ gọi sau khi user xác nhận
- `social_search` thêm câu: "If the user says to stop using Twitter … do NOT call this tool again."
- Khai báo 4 tool mới của nhóm: `wiki`, `github_repo` (TV3), `hn_search`, `citations` (TV4).

**Kết quả:** base 0.85 → **0.90**. R13 pass. Thêm 4 tool nhưng routing không giảm (vẫn 0.95). Bộ group của nhóm đạt 0.90.

**Còn fail (2 base + 1 group):**

| Case | Model làm gì | Vì sao |
|---|---|---|
| R12 | `clarify(response_type="text")` hỏi nội dung cụ thể | `tools.yaml` đã ghi "yes_no … always for anything before send" nhưng model vẫn hỏi nội dung |
| M06 | `lookup(query="OpenAI", topic="news")` **và** `social_search` | Đã gọi đúng `lookup` nhưng gọi thừa Twitter dù mô tả tool có cấm |
| G04 | `citations(paper="1706.03762")` | Tự đổi tên "Attention Is All You Need" sang arXiv id theo trí nhớ |

**Nhận xét:** rule cho R12 và M06 **đã có trong `tools.yaml`** mà model vẫn không theo. Lỗi ở đây không nằm ở mô tả tool, mà ở việc model ưu tiên suy đoán của nó hơn câu chữ của user.

---

## 6. v3: Sửa lỗi v2 bằng `system_prompt.md`

**Giả thuyết:** cả 3 lỗi của v2 có chung một gốc là **model làm theo suy đoán thay vì câu chữ của user**. Rule hội thoại cần nằm ở prompt, nơi model coi là chỉ dẫn chung, chứ không chỉ nằm trong mô tả từng tool. Thêm một mục rule ở prompt sẽ sửa được R12, M06 và G04.

**Thay đổi:** thêm mục mới vào cuối `system_prompt.md`. `tools.yaml` giữ nguyên (cùng hash `t151898fd033d`).

```markdown
## Follow the user's words, not your own guess
- A request to send, post or publish ("đăng", "gửi", "post") always gets `clarify` with
  `response_type="yes_no"` first, even if you are not sure what content they mean. Ask them to
  confirm sending it, for example "Bạn xác nhận đăng bản tin này lên Telegram?". Do not switch
  to asking for the content with `response_type="text"`.
- When the user drops a source ("bỏ Twitter", "không cần web nữa"), stop calling that source's
  tools for the rest of the conversation. Only call the source they switched to.
- Pass names, titles, handles and IDs into arguments as the user wrote them. Do not replace a
  paper title with an arXiv ID (or the reverse) from your own memory.
```

**Kết quả:**
- Base 0.90 → **1.00** (20/20). R12 và M06 pass. Cả 4 metric đều đạt 1.00.
- Group giữ **0.90**. G04 vẫn truyền `1706.03762`.

**Vì sao G04 vẫn fail, và có phải bug không:** tool `citations` nhận cả arXiv id lẫn tiêu đề. Kết quả trả về là đúng paper ("Attention Is All You Need", 135k trích dẫn). Như vậy hành vi của model **đúng về mặt chức năng**; chỉ là grader so khớp chuỗi chính xác với tiêu đề. Đây là ví dụ cho câu hỏi B6 "failure nào cần review tay". Hướng xử lý tiếp nếu muốn: cho eval case chấp nhận cả hai giá trị, hoặc thử một v4 chỉ sửa param `paper` trong `tools.yaml`.

---

## 6b. v4: viết lại mục "Stay in scope"

**Giả thuyết:** eval v3 đạt 1.00 nhưng chat thật xử lý câu ngoài phạm vi không nhất quán, vì rule v3 chỉ liệt kê ví dụ ("such as math, code…") nên model tự đoán ranh giới. Định nghĩa rõ phạm vi và cho một câu trả lời mẫu sẽ làm agent từ chối nhất quán, đúng `behavior: refuse` của R08, R14, G05.

**Thay đổi:** chỉ mục "Stay in scope" trong `system_prompt.md` (diff đầy đủ: `SYSTEM_PROMPT_DIFF.md` mục 6).

**Bằng chứng** (chat thật, `tool_choice` auto):

| Câu hỏi | v3 | v4 |
|---|---|---|
| 1 chia 0 bằng mấy? | Từ chối nhưng vẫn trả lời "không xác định" | Từ chối |
| giải phương trình x^2 = -1 | Trả lời | Từ chối |
| Viết hàm Python đảo ngược chuỗi | Trả lời (đưa code) | Từ chối |
| 2 + 2, nguyên hàm x^2, nấu phở | Từ chối | Từ chối, cùng một câu |
| Bạn là gì và làm được những gì? | Trả lời | Trả lời |

**Kết quả:** base giữ 1.00, group 0.90 → 1.00. Eval không đo được thay đổi chính, vì grader chỉ chấm "không gọi tool". G04 pass là phụ, và chạy lại 3 lần chỉ đạt 2/3.

---

## 7. Bài học (dùng cho REPORT B6)

| Câu hỏi B6 | Trả lời |
|---|---|
| Fix nào thuộc `system_prompt.md`? | Rule **hành vi và hội thoại**: hỏi lại khi thiếu thông tin, xác nhận trước khi gửi, giữ phạm vi (v1). Làm theo câu chữ user, bỏ nguồn đã bị loại (v3). |
| Fix nào thuộc `tools.yaml`? | **Chọn tool và args**: khi nào dùng tool nào, quy ước args (`topic=news`, `query` chỉ chứa chủ đề, `timeframe`, handle không `@`), khai báo tool mới (v2). |
| Failure nào cần review tay? | G04: model truyền arXiv id thay vì tiêu đề, kết quả vẫn đúng paper nhưng grader chấm fail. |
| Cải thiện gì tiếp? | Eval case cho `wiki` và `github_repo`. Grader cho phép nhiều giá trị đúng. Thêm case multi-turn đổi nguồn (M06 từng regress ở v1). |

Thêm hai quan sát:
- **Rule đặt trong mô tả tool chưa chắc được theo.** R12 và M06 đã có rule trong `tools.yaml` từ v2 nhưng chỉ pass khi rule được nhắc lại ở prompt (v3).
- **Sửa prompt có thể gây regression.** M06 pass ở v0 nhưng fail ở v1 và v2, vì v1 làm model gọi nhiều tool hơn ("use as many tools as needed"). Nên luôn chạy lại **toàn bộ** eval sau mỗi lần sửa, không chỉ các case đang fail.

## 8. Lưu ý kỹ thuật: hash và line ending

Hash trong artifact version tính trên **byte** của file. Repo bật `core.autocrlf=true`, nên mỗi lần `git switch` hoặc merge, Windows có thể đổi đuôi dòng LF thành CRLF. Khi đó hash đổi dù nội dung không đổi; lần đầu chạy v3 ra `t852f380cc2e1` thay vì `t151898fd033d`.

Cách xử lý: trước khi chạy eval, chuyển `artifacts/*.md` và `artifacts/*.yaml` về LF (`sed -i 's/\r$//' …`) để hash khớp với version trước.
