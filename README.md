# 🤖 AI Todo Generator

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

## Cách dùng

1. Chọn **lĩnh vực quan tâm** (⚙️ góc phải header)
2. Nhấn **✨ Tạo Todo** → AI phân tích dữ liệu thực
3. Click vào card để đánh dấu **done** ✅
4. Lọc theo danh mục bằng các nút filter
