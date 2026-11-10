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

Returns `{"tool", "query", "lang", "items": [{"title", "summary", "url"}]}`. `lang` is `en` or `vi`; anything else falls back to `en`. No page found -> `items: []`.

Status: implemented. Tests: `tests/test_tool_wiki.py` (offline, mocked HTTP).
