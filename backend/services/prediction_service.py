"""Dự đoán xu hướng theo từng category cho Momentum.

- Category "finance": dùng dữ liệu lịch sử THẬT của Bitcoin (CoinGecko market_chart).
- Các category khác: chỉ số xu hướng tổng hợp, sinh tất định theo tên category
  (cùng category luôn ra cùng biểu đồ, không nhảy mỗi lần refresh) — có nhãn "ước lượng".

Forecast = hồi quy tuyến tính trên các điểm gần nhất + dải tin cậy nở dần theo độ
biến động. Mọi thứ defensive: lỗi mạng → fallback chỉ số tổng hợp, không raise.
"""
import hashlib
import random
import time
from typing import Dict, List, Optional, Tuple

import httpx

HORIZON = 7          # số ngày dự báo
HISTORY_LEN = 14     # số điểm lịch sử
_TTL = 300           # cache 5 phút để khỏi gọi CoinGecko liên tục
_cache: Dict[str, Tuple[float, dict]] = {}


# category -> cấu hình chuỗi số
CATEGORY_CONFIG = {
    "finance":       {"label": "Chỉ số Tài chính (BTC)", "unit": "$", "asset": "bitcoin"},
    "news":          {"label": "Chỉ số Biến động Thời sự",   "vol": 0.08, "drift": -0.010},
    "world":         {"label": "Chỉ số Căng thẳng Toàn cầu", "vol": 0.10, "drift": -0.016},
    "tech":          {"label": "Chỉ số Đột phá Công nghệ",   "vol": 0.07, "drift":  0.012},
    "lifestyle":     {"label": "Chỉ số Sức khỏe & Đời sống", "vol": 0.04, "drift":  0.004},
    "work":          {"label": "Chỉ số Năng suất",           "vol": 0.05, "drift":  0.006},
    "entertainment": {"label": "Chỉ số Giải trí Hot",        "vol": 0.09, "drift":  0.009},
    "sports":        {"label": "Chỉ số Nhiệt Thể thao",      "vol": 0.11, "drift":  0.000},
}

RISK_LABELS = {
    "low": "AN TOÀN",
    "medium": "THẬN TRỌNG",
    "high": "RỦI RO CAO",
    "extreme": "CỰC KỲ NGUY HIỂM",
}


def _seeded_series(seed_str: str, n: int = HISTORY_LEN, base: float = 100.0,
                   vol: float = 0.05, drift: float = 0.0) -> List[float]:
    """Random walk tất định (seed theo tên) — smooth, có drift để tạo xu hướng."""
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    vals, v = [], base
    for _ in range(n):
        v = max(1.0, v * (1 + drift + rng.uniform(-vol, vol)))
        vals.append(round(v, 2))
    return vals


async def _crypto_history(coin_id: str = "bitcoin", days: int = HISTORY_LEN) -> Optional[List[float]]:
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days, "interval": "daily"},
        )
        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        vals = [round(p[1], 2) for p in prices if isinstance(p, list) and len(p) == 2]
        return vals[-HISTORY_LEN:] if len(vals) >= 4 else None


def _forecast(history: List[float], horizon: int = HORIZON):
    """Hồi quy tuyến tính trên các điểm gần nhất → dự báo + dải lo/hi nở dần."""
    n = len(history)
    k = min(7, n)
    recent = history[-k:]
    xs = list(range(k))
    mean_x = sum(xs) / k
    mean_y = sum(recent) / k
    num = sum((xs[i] - mean_x) * (recent[i] - mean_y) for i in range(k))
    den = sum((xs[i] - mean_x) ** 2 for i in range(k)) or 1.0
    slope = num / den

    # Giới hạn ≤3%/ngày để dự báo 7 ngày không vọt quá ~±21% (tránh đường dốc phi lý).
    max_slope = abs(history[-1]) * 0.03
    slope = max(-max_slope, min(max_slope, slope))

    deltas = [recent[i] - recent[i - 1] for i in range(1, k)] or [0.0]
    vol = (sum(d * d for d in deltas) / len(deltas)) ** 0.5

    last = history[-1]
    fc, lo, hi = [], [], []
    for i in range(1, horizon + 1):
        v = last + slope * i
        band = vol * (i ** 0.5) * 1.5 + abs(last) * 0.004
        fc.append(round(v, 2))
        lo.append(round(v - band, 2))
        hi.append(round(v + band, 2))
    return fc, lo, hi, slope, vol


def _risk_and_verdict(change_pct: float, trend: str) -> Tuple[str, str]:
    a = abs(change_pct)
    if a < 3:
        risk = "low"
    elif a < 8:
        risk = "medium"
    elif a < 16:
        risk = "high"
    else:
        risk = "extreme"
    dir_word = "TĂNG" if trend == "up" else ("GIẢM" if trend == "down" else "ĐI NGANG")
    verdict = f"{RISK_LABELS[risk]} — dự báo {dir_word} {a:.1f}% trong {HORIZON} ngày tới"
    return risk, verdict


async def get_prediction(category: str) -> dict:
    cached = _cache.get(category)
    if cached and time.time() - cached[0] < _TTL:
        return cached[1]

    cfg = CATEGORY_CONFIG.get(category, {"label": f"Chỉ số {category}", "vol": 0.06, "drift": 0.0})

    history: Optional[List[float]] = None
    real = False
    if cfg.get("asset"):
        try:
            history = await _crypto_history(cfg["asset"])
            real = history is not None
        except Exception as e:
            print(f"[predict] history error ({category}): {e}")

    if not history:
        history = _seeded_series(
            cfg.get("label", category), base=100.0,
            vol=cfg.get("vol", 0.06), drift=cfg.get("drift", 0.0),
        )
        real = False

    fc, lo, hi, slope, vol = _forecast(history)
    last = history[-1]
    change_pct = round((fc[-1] - last) / last * 100, 2) if last else 0.0
    trend = "up" if change_pct > 1 else ("down" if change_pct < -1 else "flat")
    rel_vol = vol / max(abs(last), 1.0)
    confidence = max(38, min(94, round(92 - rel_vol * 700)))
    risk, verdict = _risk_and_verdict(change_pct, trend)
    arrow = "▲" if trend == "up" else ("▼" if trend == "down" else "▬")

    result = {
        "category": category,
        "label": cfg["label"],
        "unit": cfg.get("unit", ""),
        "real": real,
        "horizon_days": HORIZON,
        "history": history,
        "forecast": fc,
        "band_lo": lo,
        "band_hi": hi,
        "last_value": last,
        "forecast_value": fc[-1],
        "change_pct": change_pct,
        "trend": trend,
        "arrow": arrow,
        "confidence": confidence,
        "risk": risk,
        "verdict": verdict,
    }
    _cache[category] = (time.time(), result)
    return result
