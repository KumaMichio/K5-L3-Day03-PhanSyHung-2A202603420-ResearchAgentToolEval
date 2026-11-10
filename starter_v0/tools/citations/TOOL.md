---
name: citations
track: bonus
kind: live_api
provider: OpenAlex API
requires_env: []
inputs: [paper]
outputs: [items]
side_effect: false
---
# citations

Owner: TV4.

Returns the citation count, year and venue of one paper from OpenAlex.
`paper` is a title or an arXiv id. Use it when the user asks how often a
specific paper is cited. To find papers on a topic, use `papers`.

Status: skeleton (returns a NotImplementedError dict).
