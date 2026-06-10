# Sprout Champion Agent

> Repo phát triển agent cho dự án **Sprout Champion**.

**Trạng thái:** Early stage — công nghệ / stack chưa được chọn.

---

## Tiếng Việt

### Giới thiệu

Đây là repository khởi tạo cho dự án agent liên quan đến game Sprout Champion. Repo hiện chỉ chứa cấu trúc thư mục, tài liệu và file mẫu — chưa có runtime hay dependency cụ thể.

### Cấu trúc thư mục

| Thư mục / File | Mô tả |
|----------------|-------|
| [`docs/`](docs/) | Tài liệu kiến trúc và quyết định kỹ thuật (ADR) |
| [`config/`](config/) | File cấu hình agent (sẽ bổ sung khi chọn stack) |
| [`prompts/`](prompts/) | System prompt và prompt template |
| [`.cursor/skills/`](.cursor/skills/) | GreenNode AgentBase skills (Cursor format) |
| [`src/`](src/) | Source code runtime (sẽ bổ sung khi chọn stack) |
| [`AGENTS.md`](AGENTS.md) | Hướng dẫn cho AI/agent khi làm việc trong repo |
| [`.env.example`](.env.example) | Biến môi trường mẫu |

### Bắt đầu nhanh

```bash
# 1. Clone repo
git clone https://github.com/vodinhtri/sprout-champion-agent.git
cd sprout-champion-agent

# 2. Tạo file môi trường local
cp .env.example .env
# Chỉnh sửa .env với giá trị phù hợp (không commit file .env)

# 3. Đọc tài liệu
# - docs/architecture.md
# - docs/decisions/0001-tech-stack.md
```

### Roadmap (dự kiến)

1. **Chọn tech stack** — cập nhật ADR trong `docs/decisions/`
2. **Scaffold runtime** — thêm dependency và code trong `src/`
3. **Tích hợp tools / MCP** — kết nối agent với công cụ bên ngoài
4. **CI/CD** — thêm pipeline sau khi stack ổn định

### Liên hệ

Maintainer: _TBD_

---

## English

### Overview

This is the starter repository for an agent project related to the Sprout Champion game. It currently contains folder structure, documentation, and sample files only — no runtime or specific dependencies yet.

### Directory structure

| Directory / File | Description |
|----------------|-------------|
| [`docs/`](docs/) | Architecture docs and Architecture Decision Records (ADR) |
| [`config/`](config/) | Agent configuration files (to be added when stack is chosen) |
| [`prompts/`](prompts/) | System prompts and prompt templates |
| [`.cursor/skills/`](.cursor/skills/) | GreenNode AgentBase skills (Cursor format) |
| [`src/`](src/) | Runtime source code (to be added when stack is chosen) |
| [`AGENTS.md`](AGENTS.md) | Guidelines for AI/agents working in this repo |
| [`.env.example`](.env.example) | Sample environment variables |

### Quick start

```bash
# 1. Clone the repo
git clone https://github.com/vodinhtri/sprout-champion-agent.git
cd sprout-champion-agent

# 2. Create local env file
cp .env.example .env
# Edit .env with appropriate values (never commit .env)

# 3. Read the docs
# - docs/architecture.md
# - docs/decisions/0001-tech-stack.md
```

### Roadmap (planned)

1. **Choose tech stack** — update ADR in `docs/decisions/`
2. **Scaffold runtime** — add dependencies and code under `src/`
3. **Integrate tools / MCP** — connect the agent to external tools
4. **CI/CD** — add pipeline once the stack is stable

### Contact

Maintainer: _TBD_
