# Sprout Champion Agent — Technical Interview Q&A

> AI agent phỏng vấn kỹ thuật (FE/BE/System Design) trên GreenNode AgentBase.

Agent đóng vai **người phỏng vấn**: đặt câu hỏi từ ngân hàng, đánh giá câu trả lời (1–5), cho feedback, và tổng kết session.

**Stack:** Python 3.12 · LangChain + Memory · GreenNode AgentBase SDK

---

## Cấu trúc

| Path | Mô tả |
|------|-------|
| [`main.py`](main.py) | Entrypoint — `POST /invocations`, `GET /health` |
| [`src/interview_tools.py`](src/interview_tools.py) | Tools: `list_topics`, `get_question` |
| [`prompts/interviewer_system.md`](prompts/interviewer_system.md) | System prompt + rubric đánh giá |
| [`config/questions/`](config/questions/) | Ngân hàng 18 câu (frontend, backend, system_design) |
| [`scripts/setup_platform.sh`](scripts/setup_platform.sh) | Tạo Memory + LLM key trên platform |
| [`scripts/deploy.sh`](scripts/deploy.sh) | Build, push, deploy runtime |
| [`scripts/test_local.sh`](scripts/test_local.sh) | Test curl multi-turn |

---

## Setup

### 1. Dependencies

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. IAM credentials

Tạo [IAM Service Account](https://iam.console.vngcloud.vn/service-accounts), rồi điền vào `.greennode.json`:

```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "agent_identity": ""
}
```

### 3. Platform resources (Memory + LLM)

```bash
cp .env.example .env
bash scripts/setup_platform.sh
```

Script tự tạo AgentBase Memory (`MEMORY_ID`) và LLM API key (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).

### 4. Chạy local

```bash
source venv/bin/activate
python main.py
```

**Lưu ý:** Agent dùng memory — client **bắt buộc** gửi headers:

- `X-GreenNode-AgentBase-Session-Id`
- `X-GreenNode-AgentBase-User-Id`

```bash
# Terminal khác
bash scripts/test_local.sh
```

Hoặc thủ công:

```bash
curl -X POST http://127.0.0.1:8080/invocations \
  -H "Content-Type: application/json" \
  -H "X-GreenNode-AgentBase-Session-Id: session-1" \
  -H "X-GreenNode-AgentBase-User-Id: candidate-1" \
  -d '{"message": "Tôi muốn phỏng vấn React, level mid"}'
```

### 5. Deploy AgentBase

```bash
bash scripts/deploy.sh sprout-interview-agent
```

---

## Chat UI (trình duyệt)

Mở endpoint trên trình duyệt để dùng giao diện chat:

```
https://endpoint-6136f094-59a6-41a8-8c88-dd4e2e3498af.agentbase-runtime.aiplatform.vngcloud.vn/
```

- Mỗi lần **Gửi** = một `POST /invocations`
- Session được lưu trong `localStorage` (cùng tab = cùng buổi phỏng vấn)
- `Ctrl+Shift+N` = bắt đầu session mới

## Luồng phỏng vấn

1. Chào hỏi → hỏi topic + level (junior/mid/senior)
2. `get_question(topic, difficulty)` — lấy câu từ ngân hàng
3. Ứng viên trả lời
4. Chấm điểm + feedback theo rubric
5. Hỏi tiếp hoặc tổng kết session

**Topics:** `frontend`, `backend`, `system_design`

---

## English

Technical interviewer agent for mock interviews (frontend, backend, system design). Built with LangChain + AgentBase Memory, deployed as a Docker container on GreenNode AgentBase Runtime (port 8080).

See setup steps above. Console: https://aiplatform.console.vngcloud.vn/agent-runtime?tab=runtime
