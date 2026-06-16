"""Vòng lặp nền theo dõi giá & nhắc giờ.

Dùng asyncio thuần (không APScheduler): app local 1 worker, công việc đã async
cùng event loop, chỉ 1 job. Mỗi vòng lấy market data 1 lần dùng chung cho mọi
alert; alert đã fire bị flip status='triggered' để không spam.
"""

import asyncio
import os
from datetime import datetime
from typing import List

from models import Alert
from services import alert_store
from services.alert_engine import is_price_triggered, is_time_due, resolve_price
from services.market_service import get_market_data
from services.notifier import build_message, send_notification

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))


async def evaluate_once() -> List[Alert]:
    """Một vòng kiểm tra. Trả list alert vừa fire."""
    alerts = await alert_store.load_alerts()
    active = [a for a in alerts if a.status == "active"]
    if not active:
        return []

    market = await get_market_data()
    now_iso = datetime.now().isoformat()
    fired: List[Alert] = []

    for alert in active:
        triggered = False
        value = None

        if alert.kind == "time":
            triggered = is_time_due(alert)
        else:
            value = resolve_price(alert, market)
            if value is None:
                await alert_store.update_alert(alert.id, last_checked_at=now_iso)
                continue
            triggered = is_price_triggered(alert, value)

        fields = {"last_checked_at": now_iso}
        if value is not None:
            fields["last_value"] = value

        if triggered:
            msg = build_message(alert, value)
            await send_notification(alert.channel, msg, alert, value)
            fields["status"] = "triggered"
            fields["last_triggered_at"] = now_iso
            updated = await alert_store.update_alert(alert.id, **fields)
            if updated:
                fired.append(updated)
        else:
            await alert_store.update_alert(alert.id, **fields)

    return fired


async def _poll_loop():
    print(f"[scheduler] start, interval={POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            fired = await evaluate_once()
            if fired:
                print(f"[scheduler] fired {len(fired)} alert(s)")
        except Exception as e:
            print(f"[scheduler] error: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def start_scheduler() -> asyncio.Task:
    return asyncio.create_task(_poll_loop())
