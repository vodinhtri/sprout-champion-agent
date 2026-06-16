import asyncio
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

    stocks = await loop.run_in_executor(
        None, _fetch_stocks, ["AAPL", "NVDA", "MSFT", "TSLA"]
    )
    gold = await loop.run_in_executor(None, _fetch_gold)

    crypto, rates = await asyncio.gather(crypto_task, rate_task)

    return {
        "crypto": crypto,
        "stocks": stocks,
        "gold": gold,
        "exchange_rates": rates,
    }
