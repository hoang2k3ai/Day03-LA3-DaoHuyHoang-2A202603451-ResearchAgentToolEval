---
name: wiki_summary
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [topic, lang]
outputs: [title, summary, url]
side_effect: false
---
# wiki_summary

Returns the short Wikipedia summary for a topic in vi or en. Use it for "X là gì" definition
questions about people, places, companies or concepts. Do not use it for today's news.
