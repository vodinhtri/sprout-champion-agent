import json
import os
from typing import List, Dict, Any

import httpx
from models import UserPreferences

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-4o-mini")

SYSTEM_PROMPT = """Bạn là một AI thông minh chuyên phân tích dữ liệu thực tế (tin tức thời sự, thị trường tài chính, crypto, tỷ giá) và tạo ra danh sách Todo thực tiễn, cá nhân hóa cho người dùng Việt Nam.

Dựa vào dữ liệu được cung cấp, tạo ra 6-8 todo items HÀNH ĐỘNG ĐƯỢC và THỰC TẾ.

Mỗi todo phải:
1. **title**: Tiêu đề ngắn, bắt đầu bằng động từ hành động (Mua / Tránh / Xem / Kiểm tra / Chuẩn bị...)
2. **description**: 1-2 câu mô tả tình huống dựa trên data thực
3. **action**: Hành động cụ thể người dùng cần làm (câu lệnh rõ ràng)
4. **rationale**: Lý do ngắn gọn vì sao làm ngay hôm nay (nêu số liệu cụ thể)
5. **priority**: "urgent" (cần làm ngay) | "normal" (nên làm) | "info" (để biết)
6. **category**: "finance" | "news" | "lifestyle" | "work" | "entertainment"
7. **data_point**: Con số/chỉ số nổi bật nhất (ví dụ: "BTC +5.2%", "Vàng -1.1%", "USD: 25,400đ")

Phong cách: thực tế, đôi khi hài hước như người bạn hay đọc báo, không lan man. Ưu tiên sắp xếp: urgent > normal > info.

Chỉ trả về JSON array thuần túy, không có markdown hay text ngoài JSON."""


async def generate_todos(
    news_data: List[Dict],
    market_data: Dict[str, Any],
    preferences: UserPreferences,
) -> List[Dict]:
    btc = market_data["crypto"].get("bitcoin", {})
    eth = market_data["crypto"].get("ethereum", {})
    sol = market_data["crypto"].get("solana", {})
    gold = market_data["gold"]
    rates = market_data["exchange_rates"]
    stocks = market_data["stocks"]

    market_ctx = f"""
=== DỮ LIỆU THỊ TRƯỜNG ===
CRYPTO (24h):
- Bitcoin: ${btc.get('usd', 'N/A'):,} ({btc.get('usd_24h_change', 0):+.1f}%)
- Ethereum: ${eth.get('usd', 'N/A'):,} ({eth.get('usd_24h_change', 0):+.1f}%)
- Solana: ${sol.get('usd', 'N/A')} ({sol.get('usd_24h_change', 0):+.1f}%)

VÀNG: ~${gold['price_usd']:,}/oz | Thay đổi: {gold['change_pct']:+.1f}% | Xu hướng: {'📈 TĂNG' if gold['trend'] == 'up' else '📉 GIẢM'}

TỶ GIÁ: USD/VND = {rates.get('USD_VND', 25400):,}đ | USD/EUR = {rates.get('USD_EUR', 0.92)}

CỔ PHIẾU QUỐC TẾ:
{chr(10).join(f"- {k}: ${v['price']} ({v['change_pct']:+.1f}%)" for k, v in stocks.items())}"""

    news_ctx = "\n".join(
        f"- [{item['source']}] {item['title']}"
        + (f": {item['summary'][:120]}" if item.get("summary") else "")
        for item in news_data[:18]
    )

    prompt = f"""Người dùng quan tâm đến: {', '.join(preferences.interests)}

{market_ctx}

=== TIN TỨC MỚI NHẤT ===
{news_ctx}

Tạo Todo list JSON dựa trên dữ liệu trên. Chỉ trả về JSON array."""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.8,
                },
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()

        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.split("```")[0].strip()

        todos = json.loads(text)

        for i, todo in enumerate(todos):
            if "id" not in todo or not todo["id"]:
                todo["id"] = f"todo-{i+1}"

        return todos

    except Exception as e:
        print(f"[ai] Generation error: {e}")
        return [
            {
                "id": "fallback-1",
                "title": "Kiểm tra kết nối API",
                "description": "Hệ thống đang tải dữ liệu. Có thể do rate limit hoặc mạng.",
                "action": "Thử nhấn 'Tạo mới' lại sau vài giây",
                "rationale": "API timeout hoặc rate limit tạm thời",
                "priority": "info",
                "category": "work",
                "data_point": "Error: retry",
            }
        ]
