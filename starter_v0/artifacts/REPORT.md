# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 
- Members: Phan Sỹ Hùng - Lead, prompt & eval, Nguyễn Tiến Hưng – UI, Dương Thị Huệ – tool `wiki`/`github_repo`, Dương Minh Tân – tool `hn_search`/`citations`, Dương Ngọc Tuyên – eval cases
- Provider/model: OpenRouter, `openai/gpt-4o-mini` (mọi run eval v0–v5 và transcript v3)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent đa nguồn: Tra cứu thông tin trên Web, Twitter/X, cộng đồng công nghệ Hacker News, paper khoa học arXiv, số trích dẫn OpenAlex và policy nội bộ; tự động hỏi lại khi thiếu thông tin (clarify), tổng hợp digest và gửi Telegram khi có xác nhận.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: https://k5-l3-day03-phansyhung-2a202603420-researchagenttooleval.streamlit.app/ (hoặc link Cloudflare Tunnel trycloudflare.com)

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
| wiki | định nghĩa và bối cảnh của khái niệm, người, tổ chức từ Wikipedia (en/vi) | có (TV3) |
| github_repo | số sao, fork, lần push gần nhất và release mới nhất của một repo GitHub | có (TV3) |

## A3. Câu hỏi mẫu để thử

1. "Dân Hacker News đang bàn gì về Rust?" *(Thử tool mới `hn_search`)*
2. "Paper 2106.09685 được cite bao nhiêu lần và đăng ở đâu?" *(Thử tool mới `citations`)*
3. "Tweet mới nhất của Sam Altman là gì?" *(Thử map tên sang handle `sama` và lấy timeline)*
4. "Tin tức AI hôm nay có gì nổi bật trên web?" *(Thử `lookup` với topic=news, timeframe=day)*
5. "Tóm tắt bài viết này giúp mình: https://openai.com/research/overview" *(Thử `fetch` URL)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` và `runs/*.json`. Metric là `case_accuracy` trên bộ base (20 case). Mỗi version chỉ đổi một file, nên trong artifact version chỉ một trong hai hash `p…` / `t…` thay đổi. So sánh chi tiết: `artifacts/VERSIONS.md` và `artifacts/SYSTEM_PROMPT_DIFF.md`. Bản prompt/tools của từng version: `artifacts/versions/<v>/`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (`v0+peb1c8179815b+t5b22a2476d41`) | Đo hành vi của prompt và tools starter trước khi sửa | – | 0.65 | `runs/v0_B_base_openrouter_20261110T104043342893.json` |
| v1 | `system_prompt.md` (`v1+p9352321c7609+t5b22a2476d41`) | 5/7 lỗi v0 là lỗi hành vi do prompt starter ra lệnh đoán handle/URL, gửi không cần xác nhận, ép một tool. Thay bằng rule: thiếu thông tin thì `clarify`, `send` phải xác nhận `yes_no`, ngoài phạm vi thì không gọi tool, gọi đủ tool cần thiết | 0.65 | 0.85 | `runs/v1_B_base_openrouter_20261110T114726420246.json` |
| v2 | `tools.yaml` (`v2+p9352321c7609+t151898fd033d`) | Lỗi còn lại là lỗi chọn tool/args do mô tả tool mơ hồ. Viết lại mọi description (làm gì / khi nào dùng / khi nào không) + quy ước args (`query` chỉ là chủ đề, `topic=news`, `timeframe`, handle không `@`, `search_type`) + khai báo 4 tool mới | 0.85 | 0.90 (group 0.90) | `runs/v2_B_base_openrouter_20261110T114920297691.json` |
| v3 | `system_prompt.md` (`v3+pe20a0025fb65+t151898fd033d`) | 3 lỗi của v2 cùng một gốc: model làm theo suy đoán thay vì câu chữ của user. Thêm mục "Follow the user's words": đăng/gửi luôn `clarify` `yes_no`, bỏ nguồn nào thì không gọi lại, truyền tên/ID đúng như user viết | 0.90 | **1.00** (group 0.90) | `runs/v3_B_base_openrouter_20261110T124444004699.json` |
| v4 | `system_prompt.md` (`v4+pfc14bea47ff2+t151898fd033d`) | Eval v3 đã 1.00 nhưng chat thật xử lý câu ngoài phạm vi không nhất quán: 2+2, nấu phở bị từ chối; x²=−1, viết hàm Python lại được trả lời; 1/0 vừa từ chối vừa trả lời. Rule v3 chỉ liệt kê ví dụ. Viết lại *Stay in scope*: mọi câu toán/code/nấu ăn/việc cá nhân đều từ chối bằng một câu mẫu + định hướng về research, đúng `behavior: refuse` của R08, R14, G05 | 1.00 | 1.00 (group 0.90 → 1.00, xem G04 ở B2) | `runs/v4_B_base_openrouter_20261110T141502032712.json` |
| v5 | `tools.yaml` (`v5+pfc14bea47ff2+td908e6fef2e2`) | Live chat lượt 4 (B4): chữ "mới nhất" ở lượt nói về tweet bị mang sang câu hỏi HN, nên model gọi `hn_search(sort="recent")` (3/5 lần khi có lịch sử). Mô tả `sort` chỉ ghi "'recent' for newest". Viết lại: chỉ `recent` khi "mới nhất" nói về chính cuộc tìm HN đó | 1.00 | 1.00 (group 1.00) | `runs/v5_B_base_openrouter_20261110T142303807872.json` |

Metric chi tiết (base):

| Version | case_accuracy | tool_routing | argument | multiturn |
|---|---:|---:|---:|---:|
| v0 | 0.65 | 0.75 | 0.65 | 1.00 |
| v1 | 0.85 | 0.95 | 0.85 | 0.83 |
| v2 | 0.90 | 0.95 | 0.90 | 0.83 |
| v3 | 1.00 | 1.00 | 1.00 | 1.00 |
| v4 | 1.00 | 1.00 | 1.00 | 1.00 |
| v5 | 1.00 | 1.00 | 1.00 | 1.00 |

v5 cũng không đo được bằng eval, vì không case nào có lịch sử nói "mới nhất" về chủ đề khác. Bằng chứng là chạy lại 5 lần mỗi tình huống ở chế độ chat:

| Tình huống | Đúng là | v4 | v5 |
|---|---|---|---|
| Lượt trước "5 tweet mới nhất", rồi hỏi "Dân HN bàn gì về Rust?" | `popular` | 3/5 `recent` ❌ | 5/5 `popular` ✅ |
| "Thảo luận nổi bật về Mojo trên HN" → "Lấy bài mới nhất thôi" (như GM02) | `recent` | 5/5 `recent` | 5/5 `recent` ✅ |
| "Bài mới nhất trên HN về Llama" (như G02) | `recent` | 5/5 `recent` | 5/5 `recent` ✅ |

Cùng lúc sửa **bug code** của `hn_search`: `sort="recent"` gọi Algolia `search_by_date`, endpoint này trả về bài mới nhất không chứa từ khoá (0/5 bài về Rust). Thêm `restrictSearchableAttributes=title` và `typoTolerance=false`; test thật với Rust, Llama, Mojo được 15/15 bài đúng chủ đề. Có thêm unit test hồi quy `test_hn_search_recent_matches_title_strictly`. Code tool không nằm trong artifact hash nên không tính là một version riêng.

Eval không phân biệt được v3 và v4, vì grader chỉ chấm "không gọi tool" chứ không chấm agent có từ chối hay không. Bằng chứng cho v4 là test chat thật 8 câu, mỗi câu chạy ở `tool_choice` auto như khi chat:

| Câu hỏi | v3 | v4 |
|---|---|---|
| 1 chia 0 bằng mấy? | Từ chối nhưng vẫn trả lời "không xác định" | Từ chối |
| giải phương trình x^2 = -1 | **Trả lời** | Từ chối |
| 2 + 2 bằng mấy? | Từ chối | Từ chối |
| Giải giúp mình nguyên hàm của x^2 | Từ chối | Từ chối |
| Viết hàm Python đảo ngược chuỗi | **Trả lời** (đưa code) | Từ chối |
| Cách nấu phở bò | Từ chối | Từ chối |
| Bạn là gì và làm được những gì? | Trả lời | Trả lời (R09 không bị từ chối nhầm) |
| chào | — | Chào lại bình thường |

Ở v4, 6 câu ngoài phạm vi đều nhận cùng một câu: *"Xin lỗi, câu này nằm ngoài phạm vi của mình. Mình là trợ lý research, có thể giúp bạn tìm và tóm tắt thông tin, paper, tin tức."*

## B2. Failure Analysis

Lấy từ `results[*].result.failures` của các run. Cột Fix ghi version đã sửa được case đó.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là …")` | Câu toán ngoài phạm vi nhưng model gửi lời giải lên Telegram, vì prompt starter ép "pick one tool" | v1: rule *Stay in scope* + "never use `send` to answer" |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text="def fibonacci(n): …")` | Giống R08: dùng `send` để trả lời câu viết code | v1: như R08 |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama")` | Không có account mà model tự đoán Sam Altman, làm đúng như prompt starter bảo | v1: rule *Ask instead of guessing* → `clarify` |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | Bịa URL thay vì xin link | v1: "Never invent a URL" → `clarify` |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này")` | Gửi ngay, không xác nhận | v1 hết gửi bừa, nhưng xem dòng R12 (v1, v2) |
| R03_web_news_routing (v0) | wrong_arg_value | `lookup(query="AI news", topic="news", timeframe="day")` | Nhét "news" vào `query`; expected `query="AI"` | Pass từ v1 (không có rule args nào trong v1, có thể chỉ là dao động); v2 thêm quy ước `query` chỉ chứa chủ đề |
| R13_parallel_web_and_tweets (v0, v1) | wrong_arg_value | v0: `lookup(query="AI news")` + `social_search`; v1: `lookup(query="AI")` không có `topic` | Thiếu `topic="news"` cho câu hỏi tin tức | v2: description `topic`: "'news' whenever the user asks for news, tin tức…" |
| M06_switch_tool (v1) | wrong_tool | `social_search(query="OpenAI")` | User đã nói "Bỏ Twitter, chuyển sang web" mà vẫn gọi Twitter. **Regression**: v0 pass case này | v3 (xem dòng dưới) |
| M06_switch_tool (v2) | wrong_tool (extra_tool_call) | `lookup(query="OpenAI", topic="news")` + `social_search(query="OpenAI")` | Gọi đúng `lookup` nhưng thừa `social_search`, dù `tools.yaml` v2 đã ghi "do NOT call this tool again" | v3: rule "stop calling that source's tools" trong prompt |
| R12_confirm_before_send (v1, v2) | wrong_boundary (wrong_arg_value) | `clarify(question="Bạn muốn đăng nội dung gì…", response_type="text")` | Có hỏi trước khi gửi, nhưng hỏi nội dung (`text`) thay vì xác nhận (`yes_no`). `tools.yaml` v2 đã nói rõ `yes_no` mà model vẫn bỏ qua | v3: rule "always `clarify` `yes_no` … even if you are not sure what content" |
| G04_citations_by_title (v2, v3) | wrong_arg_value | `citations(paper="1706.03762")` | Expected tiêu đề "Attention Is All You Need"; model tự đổi sang arXiv id. Tool vẫn trả về đúng paper (135k trích dẫn) | v3 thêm rule "pass titles as the user wrote them" nhưng không có tác dụng. v4 pass trong run chính thức, nhưng chạy lại 3 lần chỉ 2/3 truyền tiêu đề, nên **chưa ổn định**. Cần review tay (xem B6) |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single-turn G01–G05, 5 multi-turn GM01–GM05), viết cho 2 tool mới `hn_search` và `citations`. Kết quả theo run v3 (`runs/v3_B_group_openrouter_20261110T124558509816.json`): **9/10 pass**, giống v2. Ở v4 (`runs/v4_B_group_openrouter_20261110T141530922633.json`) là 10/10, nhưng G04 chưa ổn định (xem B2).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hn_search_dev_community | "Dân Hacker News bàn gì về Rust" → `hn_search`, không phải `social_search` | `hn_search(query="Rust")` | ✅ pass |
| G02_hn_search_recent_sort | "Bài mới nhất trên HN" → `sort="recent"` | `hn_search(query="Llama", sort="recent")` | ✅ pass |
| G03_citations_arxiv_lookup | Số trích dẫn theo arXiv id → `citations`, không phải `papers` | `citations(paper="2106.09685")` | ✅ pass |
| G04_citations_by_title | Số trích dẫn theo tiêu đề paper | `citations(paper="Attention Is All You Need")` | ❌ fail: model truyền `1706.03762` (đúng paper, sai chuỗi) |
| G05_out_of_scope_cooking | Hỏi nấu phở, ngoài phạm vi | Không gọi tool, từ chối lịch sự | ✅ pass |
| GM01_papers_then_citations | Lượt 1 tìm paper LoRA, lượt 2 hỏi số cite | `citations(paper="2106.09685")` | ✅ pass |
| GM02_hn_search_switch_sort | Đổi từ bài nổi bật sang bài mới nhất | `hn_search(query="Mojo", sort="recent")` | ✅ pass |
| GM03_hn_search_limit_update | Lượt 2 "chỉ lấy đúng 3 bài" | `hn_search(query="AI agents", limit=3)` | ✅ pass |
| GM04_clarify_then_hn_query | Lượt 1 thiếu từ khoá, lượt 2 bổ sung | `hn_search(query="Python 3.13")` | ✅ pass |
| GM05_citations_doi_correction | User đính chính arXiv id ở lượt 2 | `citations(paper="2106.09685")` | ✅ pass |

Chưa có case cho `wiki` và `github_repo` (tool của TV3).

## B4. Live Chat Evidence

Transcript chính: `transcripts/v3_openrouter_20261110T135727861487.transcript.json`. Chạy bằng `chat.py --provider openrouter --model openai/gpt-4o-mini --version v3`, artifact `v3+pe20a0025fb65+t151898fd033d`, khớp `version_log.csv`. `.env` chỉ có key OpenRouter, nên các tool cần key riêng (`timeline`, `send`) trả về lỗi thiếu key; phần cần chứng minh là model chọn tool và args nào.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tóm tắt 5 tweet mới nhất giúp mình | (không gọi tool) | v3, rule *Ask instead of guessing* | Hỏi lại "tài khoản Twitter nào?". Đúng ý là không đoán account, nhưng hỏi bằng text thay vì gọi `clarify`. Chạy lại 5 lần ở chế độ chat: 5/5 như vậy (nguyên nhân ở B6) |
| 2 | Của Sam Altman nhé | `timeline(screenname="sama", limit=5)` | v3: tên → handle không `@`, giữ `limit=5` từ lượt 1 | Args đúng. Tool báo thiếu `RAPIDAPI_KEY`, agent báo lại cho user |
| 3 | Giải giúp mình nguyên hàm của x^2 | (không gọi tool) | v3, rule *Stay in scope* (v0 gọi `send` ở case này) | Từ chối lịch sự bằng text ✅ |
| 4 | Dân Hacker News đang bàn gì về Rust? | `hn_search(query="Rust", sort="recent", limit=5)` | v3 + tool mới `hn_search` (TV4) | Route đúng tool. Nhưng model tự thêm `sort="recent"` (mang từ "mới nhất" ở lượt 1; chạy lại có lịch sử: 3/5), và `search_by_date` trả về bài không liên quan đến Rust (bug tool, xem B6) |
| 5 | Đăng bản tin này lên Telegram giúp mình | `clarify(question="Bạn xác nhận đăng bản tin này lên Telegram?", response_type="yes_no")` | v3, rule mới *Follow the user's words* (v1, v2 hỏi bằng `text`) | Dừng lại chờ xác nhận ✅ |
| 6 | Có | `send(text="…5 bài HN…", confirmed=true)` | v3, rule *Confirm before sending* | Chỉ gọi `send` sau khi user nói có, với `confirmed=true` ✅. Không có `TELEGRAM_BOT_TOKEN` nên không có gì được đăng thật |

Các transcript khác trong `transcripts/` do TV2 tạo khi thử UI. Chúng dùng model `openai/gpt-oss-120b` và nhãn version không khớp hash prompt (ví dụ file `v2_…113006…` có prompt hash `eb1c8179815b` của v0), nên chỉ dùng làm bằng chứng UI chạy được, không dùng để so sánh version.

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tests/test_tools_todo.py`, `transcripts/v3_openrouter_20261110T135727861487.transcript.json` (lượt 5–6) | Kiểm tra token & chat_id, chỉ gửi khi `confirmed=True`. Live chat v3: model hỏi `clarify(response_type="yes_no")` trước, chỉ gọi `send(confirmed=true)` sau khi user trả lời "Có" | Chặn network call nếu `confirmed=False` |
| arXiv/company policy | `company_policy/`, `tests/` | Mock và query policy, filter area, tách `untrusted_text` | Prompt injection được cô lập vào `untrusted_text` |
| UI | `app.py`, `tests/test_app_ui.py`, `transcripts/*.transcript.json` (`"interface": "streamlit"`) | Streamlit chat dùng lại `run_model_tool_loop` của `chat.py`, nên chạy giống CLI. Mỗi lượt hiện tool call, args, kết quả (item có link, digest markdown, JSON), có nút trả lời nhanh khi `clarify` hỏi yes/no hoặc choice, ghi transcript cùng schema với `chat.py`. Mở ra ngoài qua Cloudflare Tunnel. 4 test offline (provider giả) pass. | Link tunnel là public: ai có link cũng tiêu credit API của nhóm, nên chỉ bật trong buổi showdown. `send` vẫn phụ thuộc `confirmed=true` và rule trong prompt. Lỗi provider hoặc thiếu key hiện lên UI thay vì làm sập app. |
| Tool unit tests (`tests/`) | `pytest tests/` (126 passed, 0 skipped, 0 failed) | 100% test xanh cho toàn bộ core tools + 2 tools mới | Mock offline bằng `fake_http`, không tốn credit API |
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

**Which fixes belonged in `system_prompt.md`?**
Các rule về **hành vi và cách xử lý hội thoại**, áp dụng cho mọi tool:
- Thiếu thông tin thì hỏi lại, không đoán (R10, R11).
- Xác nhận trước khi gửi; không dùng `send` để trả lời (R08, R12, R14).
- Ngoài phạm vi thì không gọi tool (R08, R14).
- Làm theo câu chữ của user: bỏ nguồn nào thì không quay lại nguồn đó (M06), hỏi `yes_no` chứ không hỏi nội dung (R12).
- Định nghĩa rõ ranh giới phạm vi, kèm một câu trả lời mẫu (v4). Rule chỉ liệt kê ví dụ ("such as math, code…") thì model tự đoán ranh giới: câu toán dễ bị từ chối, nhưng câu toán khác hoặc câu code lại được trả lời.

v1 sửa 4/7 lỗi v0 chỉ bằng prompt. Phần lớn lỗi baseline đến từ chính các chỉ dẫn xấu trong prompt starter.

**Which fixes belonged in `tools.yaml`?**
Các rule về **chọn tool nào và điền args thế nào**, gắn với từng tool:
- Khi nào dùng / không dùng tool nào, có chỉ sang tool đúng (ví dụ `hn_search` vs `social_search`, `citations` vs `papers`).
- Quy ước args: `topic="news"` cho tin tức (R13), `query` chỉ chứa chủ đề (R03), `timeframe`, handle không `@`, `search_type`.

v2 chỉ đổi `tools.yaml` mà sửa được R13 và thêm 4 tool mới không làm routing giảm. v5 cũng là fix thuộc `tools.yaml`: mô tả arg `sort` phải nói rõ "mới nhất" phải nói về chính cuộc tìm HN, nếu không model mang từ đó từ lượt khác sang.

Bài học: rule hội thoại đặt trong mô tả tool **chưa chắc được theo**. Từ v2, `tools.yaml` đã ghi "yes_no … before send" và "do NOT call this tool again" khi user bỏ Twitter, nhưng R12 và M06 chỉ pass khi rule được đưa lên system prompt ở v3. Một thay đổi prompt cũng có thể gây regression ở chỗ khác: M06 pass ở v0 nhưng fail ở v1, v2. Vì vậy mỗi lần sửa đều chạy lại toàn bộ eval.

**Which failure needed manual review instead of automatic grading?**
- **G04:** grader so khớp chuỗi `paper="Attention Is All You Need"`, model truyền `1706.03762`. Tool nhận cả hai dạng và trả về đúng paper, nên về chức năng thì không sai. Grader chấm fail; chỉ người đọc mới biết đây là chấp nhận được. Ngược lại, G04 pass ở v4 cũng không có nghĩa là đã sửa: chạy lại 3 lần thì 1 lần vẫn truyền id.
- **Câu ngoài phạm vi (v3 → v4):** R08, R14, G05 có `"behavior": "refuse"` nhưng grader chỉ kiểm tra "không gọi tool". v3 trả lời luôn câu x²=−1 và câu viết code mà eval vẫn chấm 1.00. Phải đọc câu trả lời mới thấy agent từ chối không nhất quán.
- **Live chat lượt 1 (B4):** model hỏi lại "tài khoản nào?" bằng text thay vì gọi `clarify`. Chạy lại để kiểm tra:
  - Eval (R10) × 5 lần: 5/5 gọi `clarify(response_type="text")`.
  - Cùng câu, chế độ chat (`tool_choice` auto) × 5 lần: **5/5 trả lời bằng text**, không gọi tool.

  Nguyên nhân: `run_eval.py` (dòng 293) đặt `tool_choice="required"` cho mọi case expected có tool, nên trong eval model **bắt buộc** phải gọi một tool. Chat và UI để model tự quyết. Như vậy R10 pass trong eval không chứng minh model sẽ gọi `clarify` khi chat thật. Với user thì kết quả gần như nhau (vẫn được hỏi lại), nhưng UI không hiện nút trả lời nhanh và transcript không ghi trạng thái `waiting_for_user`.
- **Live chat lượt 4 (B4):** `hn_search(query="Rust")` đúng tool, nhưng model thêm `sort="recent"`. Chạy lại:
  - Eval (G01) × 5 và chat không có lịch sử × 5: 10/10 `sort="popular"`.
  - Chat **có lịch sử** 3 lượt đầu (lượt 1 nói "5 tweet **mới nhất**") × 5: **3/5 `sort="recent"`**.

  Model mang chữ "mới nhất" từ lượt trước sang câu hỏi mới. Eval single-turn không bắt được lỗi này. **Đã sửa ở v5** (mô tả `sort` trong `tools.yaml`): 5/5 `popular`.
- **Bug tool phát hiện từ lượt 4:** với `sort="recent"`, `hn_search` gọi Algolia `search_by_date`, và endpoint này trả về 5 bài mới nhất **không chứa "Rust"**: Algolia tìm cả trong URL/nội dung và có sửa lỗi chính tả. Eval chỉ kiểm tra args, unit test dùng `fake_http`, nên cả hai đều không bắt được. **Đã sửa:** thêm `restrictSearchableAttributes=title&typoTolerance=false`, 15/15 bài đúng chủ đề, kèm unit test hồi quy.

**What would you improve next?**
1. Eval case cho `clarify` nên chạy với `tool_choice` auto (giống chat thật), hoặc thêm rule prompt: "khi hỏi lại user, luôn dùng tool `clarify`, không hỏi bằng text".
2. Đưa tình huống của v5 thành eval case multi-turn: lượt trước nói "mới nhất" về tweet, lượt sau hỏi HN, expected `sort="popular"`.
3. Unit test với HTTP giả không bắt được lỗi chất lượng kết quả (bug `search_by_date`). Nên có vài smoke test gọi API thật, chạy tay trước khi demo.
4. Thêm eval case cho `wiki` và `github_repo`.
5. Cho grader chấp nhận nhiều giá trị đúng (tiêu đề hoặc arXiv id cho `citations`).
6. Chạy thử v3 trên model local nhỏ (B7).

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
