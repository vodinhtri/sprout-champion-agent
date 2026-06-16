"""Logic đánh giá alert: map alert → giá hiện tại và kiểm tra điều kiện.

Tách khỏi market_service để market_service vẫn là pure data layer.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from models import Alert

VN_TZ = timezone(timedelta(hours=7))


def _parse_iso(s: str) -> Optional[datetime]:
    """Parse ISO string (chấp nhận hậu tố 'Z'); naive coi như UTC."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def to_vn_display(iso: str) -> str:
    """Hiển thị thời điểm theo giờ Việt Nam (GMT+7): 'HH:MM DD/MM/YYYY'."""
    dt = _parse_iso(iso)
    if not dt:
        return iso or "—"
    return dt.astimezone(VN_TZ).strftime("%H:%M %d/%m/%Y")


def resolve_price(alert: Alert, market: Dict[str, Any]) -> Optional[float]:
    """Lấy giá trị hiện tại tương ứng với alert từ market data.

    market là dict trả về bởi get_market_data() (đã bao gồm key 'gold_vnd').
    Trả None nếu không lấy được (vòng kiểm tra sẽ bỏ qua alert đó).
    """
    try:
        atype = alert.asset_type.value if alert.asset_type else None
        if atype == "crypto":
            return market["crypto"].get(alert.symbol, {}).get("usd")
        if atype == "gold_usd":
            return market["gold"].get("price_usd")
        if atype == "gold_vnd":
            return market["gold_vnd"].get("sell_vnd")
        if atype == "exchange_rate":
            return market["exchange_rates"].get(alert.symbol)
    except Exception as e:
        print(f"[alert_engine] resolve_price error: {e}")
    return None


def is_price_triggered(alert: Alert, value: float) -> bool:
    if alert.target_value is None:
        return False
    if alert.direction == "below":
        return value <= alert.target_value
    return value >= alert.target_value


def is_time_due(alert: Alert, now: Optional[datetime] = None) -> bool:
    dt = _parse_iso(alert.remind_at)
    if not dt:
        return False
    now = now or datetime.now(timezone.utc)
    return now >= dt
