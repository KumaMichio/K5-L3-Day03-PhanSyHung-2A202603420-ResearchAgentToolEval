---
name: hn_search
track: extension
kind: live_api
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hn_search

Tìm kiếm các bài thảo luận trên Hacker News (Algolia API).
Dùng khi: hỏi dân dev, cộng đồng tech, Hacker News đang bàn luận gì.
Không dùng khi: hỏi bài đăng trên X/Twitter (dùng social_search).

