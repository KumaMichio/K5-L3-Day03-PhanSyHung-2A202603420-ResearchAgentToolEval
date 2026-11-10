---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [query, lang]
outputs: [items]
side_effect: false
---
# wiki

Owner: TV3.

Looks up a concept, organization, or person on Wikipedia and returns the page
summary. Use it for definitions and background ("X là gì", "ai là X"). Do not
use it for recent news; that is `lookup` with `topic=news`.

Status: skeleton (returns a NotImplementedError dict).
