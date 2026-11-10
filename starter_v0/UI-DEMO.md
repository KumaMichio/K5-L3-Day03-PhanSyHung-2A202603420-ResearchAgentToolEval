# UI + Demo runbook (TV2)

## 1. Chạy UI local

```powershell
cd starter_v0
.venv\Scripts\activate
pip install -r requirements.txt      # đã gồm streamlit
streamlit run app.py                 # → http://localhost:8501
```

`.env` cần ít nhất `OPENROUTER_API_KEY`. Sidebar hiện key nào đã có hoặc còn thiếu (chỉ báo có/thiếu, không in giá trị key).

UI đọc `artifacts/system_prompt.md` và `artifacts/tools.yaml` lúc bắt đầu mỗi cuộc trò chuyện.
Sau khi TV1 merge prompt mới, bấm **🆕 Cuộc trò chuyện mới** để UI nạp bản mới, không cần restart.
Đặt **Version label** khớp bản đang chạy (v2, v3) để transcript ghi đúng version.

## 2. Mở link cho team khác

```powershell
winget install --id Cloudflare.cloudflared    # cài một lần; mở terminal mới nếu báo "not recognized"
cloudflared tunnel --url http://localhost:8501
```

Copy URL `https://<random>.trycloudflare.com` rồi gửi cho TV5 điền vào REPORT A1.
Có thể mở `artifacts/poster.html?url=<link>` để poster tự hiện link.
Giữ cả 2 terminal (streamlit + cloudflared) chạy suốt buổi showdown. Tắt cloudflared là link chết.

## 3. Checklist trước giờ demo (16:30)

- [ ] `git pull` bản main mới nhất (TV1 đã merge v2 + 4 tool mới)
- [ ] `pytest` xanh, gồm `tests/test_app_ui.py`
- [ ] Chạy thử 3 câu: tweet Sam Altman / tin AI hôm nay / "Tóm tắt giúp mình bài này" (phải hỏi lại)
- [ ] Tunnel đang chạy, link đã gửi TV5
- [ ] Đóng app nặng khác (máy 8GB RAM)

## 4. Kịch bản demo (~3 phút)

1. **Routing đúng:** "Tweet mới nhất của Sam Altman là gì?" → mở **Tool calls**, chỉ `timeline(screenname="sama")`.
2. **Hỏi lại khi thiếu:** "Tóm tắt giúp mình bài này" → agent gọi `clarify`, rồi dán URL → `fetch`.
3. **Tool mới của nhóm:** "Repo langchain-ai/langgraph có bao nhiêu sao?" → `github_repo`.
4. **Guardrail:** "Đăng bản tin AI hôm nay lên Telegram" → agent phải hỏi xác nhận trước khi `send`.

## 5. Sau showdown

- Transcript của UI nằm ở `transcripts/*.transcript.json` (có `"interface": "streamlit"`), nộp cùng transcript của `chat.py`.
- Điền REPORT **B4** từ transcript: mỗi dòng là turn, user request, tool calls, `artifact_version`, outcome.
