import asyncio
import os
import httpx
import yfinance as yf
from typing import Dict, Any


async def get_crypto_data() -> Dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum,solana,binancecoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
            )
            return resp.json()
    except Exception as e:
        print(f"[market] Crypto error: {e}")
        return {
            "bitcoin": {"usd": 65000, "usd_24h_change": 2.1},
            "ethereum": {"usd": 3400, "usd_24h_change": -1.2},
        }


def _fetch_stocks(tickers: list) -> Dict:
    result = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if len(hist) >= 2:
                last = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                chg = (last - prev) / prev * 100
                result[ticker] = {
                    "price": round(last, 2),
                    "change_pct": round(chg, 2),
                    "trend": "up" if chg > 0 else "down",
                }
        except Exception as e:
            print(f"[market] Stock error {ticker}: {e}")
    return result


def _fetch_gold() -> Dict:
    try:
        hist = yf.Ticker("GLD").history(period="5d")
        if len(hist) >= 2:
            last = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            chg = (last - prev) / prev * 100
            # GLD ≈ 1/10 oz gold → rough price per oz
            return {
                "price_usd": round(last * 10, 2),
                "change_pct": round(chg, 2),
                "trend": "up" if chg > 0 else "down",
            }
    except Exception as e:
        print(f"[market] Gold error: {e}")
    return {"price_usd": 3200, "change_pct": -0.4, "trend": "down"}


async def get_gold_vnd() -> Dict:
    """Giá vàng SJC (VND/lượng). Thử PNJ JSON trước, fallback sang giá tĩnh.

    Trả về {'sell_vnd', 'buy_vnd', 'unit': 'luong', 'source'}.
    Luôn defensive — không bao giờ raise để scheduler loop không crash.

    Ưu tiên override thủ công qua env GOLD_VND_SELL (các nguồn SJC/PNJ công khai
    hay bị chặn Cloudflare hoặc đổi endpoint), rồi mới thử PNJ JSON, cuối cùng fallback.
    """
    override = os.environ.get("GOLD_VND_SELL")
    if override:
        try:
            sell_vnd = int(float(override))
            buy_vnd = int(float(os.environ.get("GOLD_VND_BUY", sell_vnd)))
            return {"sell_vnd": sell_vnd, "buy_vnd": buy_vnd, "unit": "luong", "source": "env"}
        except Exception as e:
            print(f"[market] GOLD_VND_SELL không hợp lệ: {e}")
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                "https://edge-api.pnj.io/ecom-frontend/v1/get-gia-vang",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            payload = resp.json()
            rows = payload.get("data") or payload.get("locations") or []
            for row in rows:
                name = str(row.get("tensp") or row.get("name") or "").lower()
                if "sjc" in name:
                    sell = row.get("giaban") or row.get("sell") or row.get("gia_ban")
                    buy = row.get("giamua") or row.get("buy") or row.get("gia_mua")
                    if sell:
                        # API trả nghìn đồng/chỉ hoặc đồng/lượng tuỳ field; chuẩn hoá về VND/lượng
                        sell_vnd = int(float(sell))
                        buy_vnd = int(float(buy)) if buy else sell_vnd
                        if sell_vnd < 1_000_000:  # đơn vị nghìn đồng → ra đồng
                            sell_vnd *= 1000
                            buy_vnd *= 1000
                        return {
                            "sell_vnd": sell_vnd,
                            "buy_vnd": buy_vnd,
                            "unit": "luong",
                            "source": "PNJ",
                        }
    except Exception as e:
        print(f"[market] Gold VND error: {e}")
    return {"sell_vnd": 140_000_000, "buy_vnd": 138_000_000, "unit": "luong", "source": "fallback"}


async def get_exchange_rate() -> Dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://open.er-api.com/v6/latest/USD")
            rates = resp.json().get("rates", {})
            return {
                "USD_VND": round(rates.get("VND", 25400)),
                "USD_EUR": round(rates.get("EUR", 0.92), 4),
                "USD_JPY": round(rates.get("JPY", 149), 2),
            }
    except Exception as e:
        print(f"[market] Exchange rate error: {e}")
        return {"USD_VND": 25400, "USD_EUR": 0.92, "USD_JPY": 149}


async def get_market_data() -> Dict[str, Any]:
    loop = asyncio.get_event_loop()

    crypto_task = asyncio.create_task(get_crypto_data())
    rate_task = asyncio.create_task(get_exchange_rate())
    gold_vnd_task = asyncio.create_task(get_gold_vnd())

    stocks = await loop.run_in_executor(
        None, _fetch_stocks, ["AAPL", "NVDA", "MSFT", "TSLA"]
    )
    gold = await loop.run_in_executor(None, _fetch_gold)

    crypto, rates, gold_vnd = await asyncio.gather(
        crypto_task, rate_task, gold_vnd_task
    )

    return {
        "crypto": crypto,
        "stocks": stocks,
        "gold": gold,
        "gold_vnd": gold_vnd,
        "exchange_rates": rates,
    }
