---
name: github_repo
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [repo]
outputs: [stars, forks, description, last_push, latest_release, url]
side_effect: false
---
# github_repo

Owner: TV3.

Returns stars, forks, last push and latest release for one GitHub repository.
`repo` is `owner/name`; a full GitHub URL is normalized. Use it for questions
about a repo's popularity or activity. To read the README or page content, use
`fetch`.

Optional env: `GITHUB_TOKEN` raises the rate limit from 60 to 5000 requests per hour.

Status: skeleton (returns a NotImplementedError dict).
