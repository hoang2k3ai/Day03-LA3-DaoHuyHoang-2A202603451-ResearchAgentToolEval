---
name: extract_links
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [text]
outputs: [links, count, domains]
side_effect: false
---
# extract_links

Pulls every http(s) link out of a block of text the user pasted, in order, without duplicates.
Use it when the user shares a message or list that contains several URLs.
