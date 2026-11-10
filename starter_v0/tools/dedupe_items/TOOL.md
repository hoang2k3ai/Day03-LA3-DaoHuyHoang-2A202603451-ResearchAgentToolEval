---
name: dedupe_items
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [items]
outputs: [items, item_count, removed]
side_effect: false
---
# dedupe_items

Removes repeated items from a list of search results (same URL after dropping utm_ params, or same
normalized title). Use it after lookup or social_search returns overlapping results, before format.
