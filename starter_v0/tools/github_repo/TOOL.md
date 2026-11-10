---
name: github_repo
track: extension
kind: live_api
requires_env: []
inputs: [repo]
outputs: [repo, stars, forks, description, last_push, latest_release, url]
side_effect: false
---
# github_repo

Lấy thông tin và thống kê hoạt động của một GitHub repository.
Dùng khi: hỏi số sao, release mới nhất, repo còn được cập nhật không.
Không dùng khi: cần đọc nội dung README hay xem code chi tiết (dùng fetch).

