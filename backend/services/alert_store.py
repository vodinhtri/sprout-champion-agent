"""Lưu trữ alert dưới dạng JSON file (local-first).

Dùng cho cảnh báo giá / nhắc nhở giờ. File nằm cạnh package backend
(`backend/data/alerts.json`), đường dẫn tính từ vị trí module nên hoạt động
bất kể uvicorn được khởi động từ thư mục nào.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from models import Alert, AlertCreate
from services.alert_engine import to_vn_display

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_FILE = os.path.join(_DATA_DIR, "alerts.json")
_lock = asyncio.Lock()


def _read_raw() -> List[dict]:
    if not os.path.exists(_FILE):
        return []
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[alert_store] Read error: {e}")
        return []


def _write_raw(items: List[dict]) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp = _FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _FILE)


def _auto_label(data: AlertCreate) -> str:
    if data.kind == "time":
        return f"Nhắc lúc {to_vn_display(data.remind_at or '')}".strip()

    asset_name = {
        "gold_vnd": "Vàng SJC",
        "gold_usd": "Vàng thế giới",
        "crypto": (data.symbol or "crypto").upper(),
        "exchange_rate": data.symbol or "tỷ giá",
    }.get(data.asset_type.value if data.asset_type else "", data.symbol or "tài sản")

    arrow = "≤" if data.direction == "below" else "≥"
    target = f"{data.target_value:,.0f}" if data.target_value is not None else "?"
    return f"{asset_name} {arrow} {target} {data.currency}"


async def load_alerts() -> List[Alert]:
    async with _lock:
        return [Alert(**item) for item in _read_raw()]


async def get_alert(alert_id: str) -> Optional[Alert]:
    for a in await load_alerts():
        if a.id == alert_id:
            return a
    return None


async def add_alert(data: AlertCreate) -> Alert:
    alert = Alert(
        **data.model_dump(),
        id=uuid.uuid4().hex,
        status="active",
        created_at=datetime.now().isoformat(),
    )
    if not alert.label:
        alert.label = _auto_label(data)
    async with _lock:
        items = _read_raw()
        items.append(alert.model_dump())
        _write_raw(items)
    return alert


async def update_alert(alert_id: str, **fields) -> Optional[Alert]:
    async with _lock:
        items = _read_raw()
        updated = None
        for item in items:
            if item.get("id") == alert_id:
                item.update(fields)
                updated = Alert(**item)
                break
        if updated:
            _write_raw(items)
        return updated


async def delete_alert(alert_id: str) -> bool:
    async with _lock:
        items = _read_raw()
        new_items = [i for i in items if i.get("id") != alert_id]
        if len(new_items) == len(items):
            return False
        _write_raw(new_items)
        return True
