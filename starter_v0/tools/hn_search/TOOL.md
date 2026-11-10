---
name: hn_search
track: bonus
kind: live_api
provider: Algolia Hacker News API
requires_env: []
inputs: [query, sort, limit]
outputs: [query, sort, items]
side_effect: false
requires_confirmation: false
---

# Tool: hn_search

Tìm thảo luận, bài đăng và ý kiến cộng đồng trên Hacker News (HN).
Dùng khi người dùng hỏi dân dev, cộng đồng tech, hoặc Hacker News đang bàn gì về một chủ đề.
Không dùng khi hỏi về bài đăng trên Twitter/X (dùng social_search).
