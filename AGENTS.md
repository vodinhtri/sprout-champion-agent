# Agent Guidelines

Hướng dẫn cho AI agents (Cursor, CI bots, v.v.) khi làm việc trong repo **sprout-champion-agent**.

## Mục tiêu dự án

Xây dựng agent hỗ trợ dự án game **Sprout Champion** thuộc ZaloPay Game-FE. Repo đang ở giai đoạn early stage — stack chưa được chọn.

## Quy ước bắt buộc

1. **Đọc ADR trước khi thêm dependency** — kiểm tra [`docs/decisions/0001-tech-stack.md`](docs/decisions/0001-tech-stack.md). Nếu stack chưa quyết định, không thêm `package.json`, `pyproject.toml`, `go.mod` trừ khi user yêu cầu rõ ràng.
2. **Không commit secret** — không đưa API key, token, `.env` vào Git. Chỉ cập nhật [`.env.example`](.env.example) với tên biến mẫu.
3. **Giữ diff nhỏ** — mỗi thay đổi tập trung vào một mục tiêu; tránh refactor không liên quan.
4. **Tài liệu đi kèm thay đổi lớn** — cập nhật `docs/architecture.md` hoặc thêm ADR mới khi thay đổi kiến trúc.

## Cấu trúc thư mục

| Path | Dùng cho |
|------|----------|
| `src/` | Runtime source code |
| `config/` | File cấu hình agent |
| `prompts/` | System prompt và prompt template |
| `skills/` | Cursor Agent Skills |
| `docs/` | Kiến trúc và quyết định kỹ thuật |

## Tài liệu tham khảo

- [Kiến trúc](docs/architecture.md)
- [ADR: Tech stack](docs/decisions/0001-tech-stack.md)
- [System prompt mẫu](prompts/system.md)

## Khi chọn stack

1. Cập nhật ADR `0001-tech-stack.md` với quyết định và lý do.
2. Scaffold runtime trong `src/` theo convention của stack đã chọn.
3. Cập nhật README (phần Quick start) với lệnh cài đặt và chạy cụ thể.
