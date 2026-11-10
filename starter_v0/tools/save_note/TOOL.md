---
name: save_note
track: bonus
kind: action
provider: local filesystem
requires_env: []
inputs: [title, content, confirmed]
outputs: [status, path]
side_effect: local_file_write
requires_confirmation: true
---
# save_note

Saves a markdown note into artifacts/notes/. It writes only when `confirmed` is true; otherwise it
returns needs_confirmation and the agent must ask the user first. It never overwrites an existing note.
