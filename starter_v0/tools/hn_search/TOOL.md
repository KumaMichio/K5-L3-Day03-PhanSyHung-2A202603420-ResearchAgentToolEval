---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hn_search

Owner: TV4.

Searches Hacker News stories through the Algolia API. `sort=popular` ranks by
points, `sort=recent` by date. Use it for "what are developers / the tech
community saying about X". For posts on X/Twitter, use `social_search`.

Status: skeleton (returns a NotImplementedError dict).
