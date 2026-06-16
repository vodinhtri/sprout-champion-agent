# 🤖 Momentum

> Thay vì tự nhập todo, AI đọc tin tức & thị trường rồi tự tạo danh sách việc cần làm cho bạn.

## Ý tưởng

- Giá vàng đang giảm mạnh → **Mua vàng nếu sắp cưới, không mua đầu tư**
- Bitcoin vừa pump +5% → **Có nên chốt lời không?**
- Tin tức cướp giật tăng → **Ra đường cẩn thận, tránh đi tối**
- Cổ phiếu XYZ đang về đáy → **Xem xét vào hàng**

## Tech Stack

- **Backend**: Python · FastAPI · Claude AI (Haiku) · yfinance · CoinGecko · VnExpress RSS · CafeF RSS
- **Frontend**: React · Vite · Tailwind CSS · Framer Motion

## Setup nhanh

### 1. Lấy Anthropic API Key

Đăng ký tại [console.anthropic.com](https://console.anthropic.com) → lấy API key.

### 2. Tạo file `.env`

```bash
cp backend/.env.example backend/.env
# Mở backend/.env và điền API key vào
```

### 3. Chạy app

```bash
chmod +x start.sh
./start.sh
```

App sẽ chạy tại **http://localhost:5173**

---

### Chạy thủ công (nếu cần)

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

## Nguồn dữ liệu

| Nguồn | Dữ liệu |
|-------|---------|
| VnExpress RSS | Tin tức thời sự, kinh doanh, thế giới |
| CafeF RSS | Chứng khoán Việt Nam |
| CoinGecko API | Crypto: BTC, ETH, SOL, BNB |
| Yahoo Finance | Vàng (GLD ETF), cổ phiếu quốc tế |
| Open Exchange Rates | USD/VND và các tỷ giá khác |

## 🔔 Cảnh báo giá & nhắc giờ (Teams)

Đặt mốc giá (vàng SJC VND, BTC/ETH/SOL/BNB, USD/VND, vàng thế giới USD) hoặc thời điểm nhắc → khi điều kiện thỏa, agent gửi thông báo qua **Microsoft Teams**.

- Nhấn 🔔 trên header để mở panel, tạo/xoá cảnh báo, hoặc "Kiểm tra ngay".
- Backend chạy 1 vòng lặp nền (`POLL_INTERVAL_SECONDS`, mặc định 60s) đánh giá các cảnh báo `active`; mỗi cảnh báo chỉ bắn 1 lần (chuyển `triggered`) để không spam.
- Cấu hình trong `.env`:
  - `TEAMS_WEBHOOK_URL` — Incoming Webhook của Teams (bắt buộc để nhận thông báo thật).
  - `POLL_INTERVAL_SECONDS` — chu kỳ kiểm tra.
  - `GOLD_VND_SELL` / `GOLD_VND_BUY` — đặt giá vàng SJC thủ công (nguồn SJC/PNJ công khai hay bị chặn; bỏ trống dùng fallback ~140tr).
- Cảnh báo lưu tại `backend/data/alerts.json` (sống qua restart).

API: `POST/GET /api/alerts`, `DELETE /api/alerts/{id}`, `POST /api/alerts/check-now`, `POST /api/alerts/test-notification`.

> Zalo: hiện chỉ stub. Push Zalo cần gọi thẳng Zalo OA API (OpenClaw chỉ là bot hội thoại, không push chủ động).

### Cấu hình Power Automate flow (Teams)

Dùng template chuẩn **"Post to a channel when a webhook request is received"** — flow này có vòng `For each` lặp qua `triggerOutputs()?['body']?['attachments']` rồi đăng từng card. Vì vậy backend phải gửi định dạng đầy đủ `{type:message, attachments:[card]}` → đặt **`TEAMS_PAYLOAD_MODE=message`** (mặc định cho flow loại này).

- **Trigger**: "When a Teams webhook request is received" → copy **HTTP POST URL ĐẦY ĐỦ** (gồm `&sig=...`) vào `TEAMS_WEBHOOK_URL`. Thiếu `sig` → 401.
- **Action** (trong For each): đăng card từ `attachments` — không cần sửa, template tự forward.
- Card + @mention do **backend dựng sẵn** trong `notifier.py` (`_teams_payload`), gồm `msteams.entities` tag `TEAMS_MENTION_UPN`.

> Nếu bạn tự dựng flow với action "Post card" bind thẳng body, có thể dùng `TEAMS_PAYLOAD_MODE=card` (gửi AdaptiveCard trần) hoặc `fields` (flow tự dựng card từ `{title,text,mentionUpn,mentionName}`).

## Cách dùng

1. Chọn **lĩnh vực quan tâm** (⚙️ góc phải header)
2. Nhấn **✨ Tạo Todo** → AI phân tích dữ liệu thực
3. Click vào card để đánh dấu **done** ✅
4. Lọc theo danh mục bằng các nút filter
