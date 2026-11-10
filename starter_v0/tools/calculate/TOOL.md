---
name: calculate
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [expression]
outputs: [result]
side_effect: false
---
# calculate

Evaluates a plain arithmetic expression (+ - * / % **, parentheses). It never runs
names, function calls or attributes, so it is safe to pass model-written text.
Use it for percentages, totals and unit conversions in a digest.
