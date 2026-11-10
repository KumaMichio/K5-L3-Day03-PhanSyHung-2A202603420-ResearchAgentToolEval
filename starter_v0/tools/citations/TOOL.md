---
name: citations
track: bonus
kind: live_api
provider: OpenAlex API
requires_env: []
inputs: [paper]
outputs: [paper, items]
side_effect: false
requires_confirmation: false
---

# Tool: citations

Tra cứu số trích dẫn (citation count), năm xuất bản, nơi công bố (venue), và độ ảnh hưởng của một paper khoa học qua OpenAlex API.
Dùng khi: Hỏi paper cụ thể được trích dẫn bao nhiêu, đăng ở đâu.
Không dùng khi: Tìm paper theo chủ đề (dùng papers).
