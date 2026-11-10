---
name: dedupe
track: core
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, item_count, duplicate_count]
side_effect: false
---
# dedupe

Removes repeated research items by URL while preserving the first occurrence and input order. It does not fetch, rank, or rewrite items.
