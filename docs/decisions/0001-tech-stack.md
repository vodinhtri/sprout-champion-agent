# ADR 0001: Tech Stack

## Status

**Proposed / Undecided**

## Context

Cần xây dựng agent cho dự án Sprout Champion (ZaloPay Game-FE). Repo mới khởi tạo, chưa có runtime hay dependency. Cần chọn stack phù hợp với:

- Yêu cầu tích hợp LLM và tools/MCP
- Khả năng maintain của team Game-FE
- Môi trường deploy dự kiến (chưa xác định)

## Options considered

| Option | Ưu điểm | Nhược điểm |
|--------|---------|------------|
| **TypeScript + Cursor SDK** | Tích hợp tốt với Cursor IDE, type-safe | Phụ thuộc ecosystem Cursor |
| **Python** | Ecosystem AI/ML phong phú, nhiều thư viện agent | Có thể khác stack FE hiện tại |
| **Node.js + LangChain / LangGraph** | JavaScript ecosystem, nhiều ví dụ agent | Thêm dependency, learning curve |
| **Go** | Performance, deploy đơn giản | Ít thư viện agent sẵn có hơn |

## Decision

**Chưa quyết định.** Repo giữ ở trạng thái tech-agnostic cho đến khi team đánh giá yêu cầu cụ thể.

## Consequences

- Không thêm `package.json`, `pyproject.toml`, `go.mod` cho đến khi ADR được cập nhật.
- Cấu trúc thư mục (`src/`, `config/`, `prompts/`) đã sẵn sàng để scaffold khi có quyết định.

## Next steps

1. Thu thập yêu cầu agent (use cases, tools cần tích hợp, môi trường chạy).
2. So sánh options với team.
3. Cập nhật ADR này với **Status: Accepted** và stack đã chọn.
4. Scaffold runtime trong `src/` và cập nhật README.
