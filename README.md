# Momentum

> Thay vì tự nhập todo, AI đọc tin tức & thị trường rồi tự tạo danh sách việc cần làm cho bạn.

## Ý tưởng

- Giá vàng đang giảm mạnh → **Mua vàng nếu sắp cưới, không mua đầu tư**
- Bitcoin vừa pump +5% → **Có nên chốt lời không?**
- Tin tức cướp giật tăng → **Ra đường cẩn thận, tránh đi tối**
- Cổ phiếu XYZ đang về đáy → **Xem xét vào hàng**

## Tính năng

| Tính năng | Mô tả |
|-----------|--------|
| **Todo AI** | Gộp tin RSS + dữ liệu thị trường thực, LLM sinh 6–8 todo có priority, rationale và link nguồn |
| **Lĩnh vực quan tâm** | Chọn finance, news, world, tech, sports, entertainment, lifestyle, work — AI chỉ phân tích những gì bạn chọn |
| **Dự đoán xu hướng** | Biểu đồ 7 ngày theo category: finance dùng BTC thật (CoinGecko); các category khác dùng chỉ số tổng hợp tất định |
| **Notion sync** | Đồng bộ todo lên Notion database (tạo/cập nhật row, map Status); hoặc **Lấy todo từ Notion** để hiển thị |
| **Cảnh báo giá & nhắc giờ** | Đặt mốc giá (vàng SJC, BTC/ETH/SOL/BNB, USD/VND, vàng thế giới) hoặc thời điểm nhắc → thông báo qua **Microsoft Teams** |
| **Deploy AgentBase** | Docker image phục vụ cả React UI + FastAPI trên port `8080`, contract `GET /health` |

## Tech stack

| Layer | Công nghệ |
|-------|-----------|
| Backend | Python 3.12 · FastAPI · httpx · feedparser · yfinance |
| LLM | OpenAI-compatible API (`LLM_API_KEY` + `LLM_BASE_URL` + `LLM_MODEL`) — khuyến nghị **GreenNode AI Platform** |
| Frontend | React · Vite · Tailwind CSS · Framer Motion · Axios |
| Thông báo | Microsoft Teams Incoming Webhook (Power Automate) |
| Lưu trữ | Notion API · `backend/data/alerts.json` (cảnh báo local) |

## Cấu trúc project

```
sprout-champion-agent/
├── backend/
│   ├── main.py              # FastAPI app, routes, scheduler lifespan
│   ├── models.py            # Pydantic models
│   ├── services/
│   │   ├── ai_service.py    # Gọi LLM sinh todo
│   │   ├── news_service.py  # RSS VnExpress, CafeF
│   │   ├── market_service.py# CoinGecko, Yahoo Finance, tỷ giá, vàng SJC
│   │   ├── prediction_service.py
│   │   ├── notion_service.py
│   │   ├── alert_engine.py  # Logic kích hoạt cảnh báo
│   │   ├── alert_store.py   # JSON persistence
│   │   ├── notifier.py      # Teams Adaptive Card
│   │   └── scheduler.py     # Vòng lặp poll cảnh báo
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/      # Header, TodoCard, AlertsPanel, PredictPanel, ...
├── Dockerfile               # Multi-stage: build React → serve qua FastAPI
├── start.sh                 # Dev: backend :8000 + frontend :5173
└── .env                     # Biến môi trường (không commit)
```

## Setup nhanh

### Yêu cầu

- Python 3.11+
- Node.js 20+ (hoặc 21 qua nvm — `start.sh` thử `nvm use 21`)
- API key LLM (OpenAI-compatible)

### 1. Cấu hình LLM

App gọi endpoint `chat/completions` qua biến:

- `LLM_API_KEY` — API key
- `LLM_BASE_URL` — base URL (ví dụ GreenNode AIP: `https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`)
- `LLM_MODEL` — tên model (ví dụ `openai/gpt-4o-mini`)

Trên GreenNode AgentBase, dùng skill `/agentbase-llm` để tạo key và cấu hình.

### 2. Tạo file `.env`

Tạo `.env` ở **thư mục gốc project** (backend cũng đọc `backend/.env` nếu có):

```bash
# Bắt buộc — sinh todo
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
LLM_MODEL=openai/gpt-4o-mini

# Tuỳ chọn — Notion sync
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=...

# Tuỳ chọn — cảnh báo Teams (xem mục Cảnh báo bên dưới)
TEAMS_WEBHOOK_URL=
TEAMS_PAYLOAD_MODE=message
TEAMS_MENTION_UPN=abc@vng.com.vn
TEAMS_MENTION_NAME=Ten
POLL_INTERVAL_SECONDS=60
GOLD_VND_SELL=
GOLD_VND_BUY=
```

### 3. Chạy app

```bash
chmod +x start.sh
./start.sh
```

- UI: **http://localhost:5173**
- API: **http://localhost:8000**

> `start.sh` kiểm tra `ANTHROPIC_API_KEY` trong `backend/.env` — nếu bạn chỉ dùng `LLM_API_KEY` ở `.env` gốc, chạy thủ công như bên dưới hoặc export biến trước khi gọi script.

### Chạy thủ công

**Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Vite proxy `/api` → `http://127.0.0.1:8000`.

## Nguồn dữ liệu

| Nguồn | Dữ liệu |
|-------|---------|
| VnExpress RSS | Tin mới, kinh doanh, thế giới, số hóa, thể thao, giải trí, sức khỏe |
| CafeF RSS | Chứng khoán Việt Nam |
| CoinGecko API | Crypto: BTC, ETH, SOL, BNB (+ 24h change) |
| Yahoo Finance | Vàng (GLD ETF → USD/oz), cổ phiếu quốc tế |
| Open Exchange Rates | USD/VND và các tỷ giá khác |
| Env / PNJ (fallback) | Giá vàng SJC VND/lượng (`GOLD_VND_SELL`, `GOLD_VND_BUY`) |

## Notion

1. Tạo **Internal Integration** trên [notion.so/my-integrations](https://www.notion.so/my-integrations) → copy token → `NOTION_TOKEN`.
2. Share database với integration → copy Database ID → `NOTION_DATABASE_ID`.
3. Database cần cột **Title** (tên job), **rich_text** (note), **Status** hoặc **Select** (trạng thái). App đọc schema lúc sync và map tự động.
4. Trên UI: **Sync lên Notion** sau khi có todo; **Lấy todo từ Notion** ở màn hình welcome.

## Cảnh báo giá & nhắc giờ (Teams)

Đặt mốc giá hoặc thời điểm nhắc → khi điều kiện thỏa, agent gửi thông báo qua **Microsoft Teams**.

- Nhấn 🔔 trên header → tạo/xoá cảnh báo, **Kiểm tra ngay**, **Test notification**.
- Loại cảnh báo:
  - **Theo giá**: vàng SJC (VND), BTC/ETH/SOL/BNB (USD), USD/VND, vàng thế giới (USD/oz) — điều kiện `above` / `below`.
  - **Nhắc giờ**: `remind_at` (ISO, hiển thị GMT+7).
- Backend chạy scheduler nền (`POLL_INTERVAL_SECONDS`, mặc định 60s); mỗi cảnh báo chỉ bắn một lần (`triggered`).
- Cần email `@vng.com.vn` để @mention trong card Teams.
- Cảnh báo lưu tại `backend/data/alerts.json` (sống qua restart).

**Biến môi trường:**

| Biến | Mô tả |
|------|--------|
| `TEAMS_WEBHOOK_URL` | URL webhook Teams / Power Automate (bắt buộc để nhận thông báo thật) |
| `TEAMS_PAYLOAD_MODE` | `message` (mặc định, khớp flow For each attachments) · `card` · `fields` |
| `TEAMS_MENTION_UPN` | Email/UPN người được tag |
| `TEAMS_MENTION_NAME` | Tên hiển thị trong mention |
| `POLL_INTERVAL_SECONDS` | Chu kỳ kiểm tra (giây) |
| `GOLD_VND_SELL` / `GOLD_VND_BUY` | Giá vàng SJC thủ công (nguồn công khai hay bị chặn) |

> **Zalo**: hiện chỉ stub. Push Zalo cần gọi Zalo OA API trực tiếp.

### Cấu hình Power Automate flow (Teams)

Dùng template **"Post to a channel when a webhook request is received"** — flow có vòng `For each` qua `attachments`. Backend gửi `{type: message, attachments: [card]}` → đặt **`TEAMS_PAYLOAD_MODE=message`**.

- **Trigger**: copy URL đầy đủ (gồm `&sig=...`) vào `TEAMS_WEBHOOK_URL`. Thiếu `sig` → 401.
- Card + @mention do backend dựng trong `notifier.py` (`msteams.entities` + `TEAMS_MENTION_UPN`).

Nếu flow bind thẳng body vào action "Post card", dùng `TEAMS_PAYLOAD_MODE=card` hoặc `fields`.

## API

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/health` | Health check (AgentBase runtime contract) |
| `GET` | `/api/health` | Health + timestamp |
| `POST` | `/api/todos/generate` | Sinh todo từ `interests[]` |
| `POST` | `/api/todos/sync-notion` | Đồng bộ todo lên Notion |
| `GET` | `/api/todos/from-notion` | Lấy todo từ Notion |
| `GET` | `/api/predict/{category}` | Dự đoán xu hướng theo category |
| `GET` | `/api/market-data` | Snapshot thị trường |
| `POST` | `/api/alerts` | Tạo cảnh báo |
| `GET` | `/api/alerts` | Liệt kê cảnh báo |
| `DELETE` | `/api/alerts/{id}` | Xoá cảnh báo |
| `POST` | `/api/alerts/check-now` | Kiểm tra ngay (không chờ poll) |
| `POST` | `/api/alerts/test-notification` | Gửi thông báo test |

## Deploy (Docker / AgentBase)

Image build React + FastAPI, listen **port 8080**, expose `GET /health`.

```bash
docker build -t momentum .
docker run -p 8080:8080 --env-file .env momentum
```

Truy cập UI tại `http://localhost:8080` (static files do FastAPI serve từ `backend/static`).

Trên **GreenNode AgentBase**, dùng skill `/agentbase-deploy` để push image và tạo Custom Agent runtime (VPC hoặc PUBLIC).

## Cách dùng

1. Chọn **lĩnh vực quan tâm** (⚙️ góc phải header)
2. Nhấn **✨ Tạo Todo** → AI phân tích dữ liệu thực
3. Click card để đánh dấu **done** ✅
4. Lọc theo danh mục bằng các nút filter
5. Xem **biểu đồ dự đoán** theo category đang lọc
6. **📝 Sync lên Notion** hoặc **📥 Lấy todo từ Notion** (nếu đã cấu hình)
7. **🔔** để đặt cảnh báo giá / nhắc giờ qua Teams

## License

Private — Sprout Champion / VNG internal use.
