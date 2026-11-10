---
name: resolve_time_range
track: bonus
kind: local_knowledge
provider: none
requires_env: []
inputs: [phrase]
outputs: [start, end, label, timezone]
side_effect: false
---
# resolve_time_range

Converts a Vietnamese time phrase (hôm nay, hôm qua, tuần này, tuần trước, tháng này, năm nay)
into an explicit date range in Vietnam time. Use it before answering "trong khoảng nào"
questions or when a user asks for news from a given period.
