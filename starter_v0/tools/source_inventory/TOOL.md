---
name: source_inventory
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [urls]
outputs: [source_count, domain_count, groups]
side_effect: false
---

Gom các URL HTTP(S) đã có theo tên miền để kiểm kê nguồn. Bỏ phần fragment và loại URL trùng. Các nhóm và URL trong mỗi nhóm giữ thứ tự xuất hiện đầu tiên.

`www.example.com` và `example.com` thuộc cùng một nhóm. Các tên miền phụ khác được giữ riêng. Mỗi nhóm chứa `domain` và `urls`. Tool không truy cập mạng và trả `error` cùng vị trí URL khi đầu vào không hợp lệ.
