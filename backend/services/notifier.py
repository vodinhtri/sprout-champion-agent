"""Gửi thông báo. Dispatch theo channel — đợt local chỉ implement Teams.

Teams: Incoming Webhook (env TEAMS_WEBHOOK_URL).
Zalo: stub — khi làm thật gọi thẳng Zalo OA API (KHÔNG dùng OpenClaw vì
OpenClaw chỉ request/response, không push chủ động được).
"""

import os
from datetime import datetime
from typing import Optional

import httpx

from services.alert_engine import to_vn_display

ASSET_LABELS = {
    "gold_vnd": "Vàng SJC",
    "gold_usd": "Vàng thế giới",
    "crypto": "Crypto",
    "exchange_rate": "Tỷ giá",
}

TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL", "")
TEAMS_MENTION_UPN = os.environ.get("TEAMS_MENTION_UPN", "")    # email/UPN người được tag
TEAMS_MENTION_NAME = os.environ.get("TEAMS_MENTION_NAME", "")  # tên hiển thị (mặc định lấy phần trước @)
ZALO_OA_ACCESS_TOKEN = os.environ.get("ZALO_OA_ACCESS_TOKEN", "")
ZALO_RECIPIENT_ID = os.environ.get("ZALO_RECIPIENT_ID", "")


def build_message(alert, value: Optional[float] = None) -> str:
    label = alert.label or "Cảnh báo"
    if alert.kind == "time":
        return f"⏰ {label}\nĐã đến giờ nhắc bạn."
    if value is None:
        return f"🔔 {label}"
    return (
        f"🔔 {label}\n"
        f"Giá hiện tại: {value:,.0f} {alert.currency}"
        + (f" (mục tiêu {alert.target_value:,.0f})" if alert.target_value is not None else "")
    )


def _facts(alert, value: Optional[float]) -> list:
    """FactSet hiển thị gọn theo loại alert."""
    facts = []
    if getattr(alert, "kind", "price") == "time":
        when = to_vn_display(getattr(alert, "remind_at", None) or "")
        facts.append({"title": "⏰ Thời điểm (GMT+7)", "value": when})
        return facts

    atype = getattr(alert, "asset_type", None)
    atype = atype.value if hasattr(atype, "value") else atype
    currency = getattr(alert, "currency", "") or ""
    arrow = "≤" if getattr(alert, "direction", None) == "below" else "≥"
    target = getattr(alert, "target_value", None)

    if atype:
        facts.append({"title": "Tài sản", "value": ASSET_LABELS.get(atype, atype)})
    if value is not None:
        facts.append({"title": "💰 Giá hiện tại", "value": f"{value:,.0f} {currency}".strip()})
    if target is not None:
        facts.append({"title": "🎯 Mục tiêu", "value": f"Khi {arrow} {target:,.0f} {currency}".strip()})
    return facts


def _build_card(alert, message: str, value: Optional[float]) -> dict:
    label = getattr(alert, "label", None) or "Cảnh báo"
    is_time = getattr(alert, "kind", "price") == "time"
    accent = "good" if is_time else "warning"
    now = datetime.now().strftime("%H:%M %d/%m/%Y")

    header = {
        "type": "Container",
        "style": accent,
        "bleed": True,
        "items": [
            {
                "type": "ColumnSet",
                "columns": [
                    {"type": "Column", "width": "auto", "verticalContentAlignment": "Center",
                     "items": [{"type": "TextBlock", "text": "⏰" if is_time else "🔔", "size": "ExtraLarge"}]},
                    {"type": "Column", "width": "stretch", "verticalContentAlignment": "Center",
                     "items": [
                         {"type": "TextBlock", "text": "NHẮC NHỞ" if is_time else "CẢNH BÁO GIÁ",
                          "size": "Small", "weight": "Bolder", "isSubtle": True, "spacing": "None"},
                         {"type": "TextBlock", "text": label, "size": "Large", "weight": "Bolder", "wrap": True, "spacing": "None"},
                     ]},
                ],
            }
        ],
    }

    body = [header]

    facts = _facts(alert, value)
    if facts:
        body.append({"type": "FactSet", "facts": facts, "spacing": "Medium"})

    # dòng trạng thái thân thiện (FactSet đã hiển thị số liệu)
    status = "⏰ Đã đến giờ nhắc bạn!" if is_time else "✅ Giá đã chạm mốc bạn đặt!"
    body.append({"type": "TextBlock", "text": status, "wrap": True, "weight": "Bolder",
                 "color": ("good" if is_time else "attention"), "spacing": "Small"})

    # ghi chú của người dùng (nếu có)
    note = getattr(alert, "note", None)
    if note:
        body.append({
            "type": "Container",
            "style": "emphasis",
            "spacing": "Medium",
            "items": [
                {"type": "TextBlock", "text": "📝 Ghi chú", "weight": "Bolder", "size": "Small", "isSubtle": True, "spacing": "None"},
                {"type": "TextBlock", "text": note, "wrap": True, "spacing": "None"},
            ],
        })

    content = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": body,
    }

    # @mention — ưu tiên email gắn theo alert, fallback env
    upn = getattr(alert, "notify_email", None) or TEAMS_MENTION_UPN
    if upn:
        name = upn.split("@")[0]
        at_token = f"<at>{name}</at>"
        body.append({"type": "TextBlock", "text": f"👤 {at_token}", "wrap": True, "spacing": "Medium"})
        content["msteams"] = {
            "entities": [
                {"type": "mention", "text": at_token, "mentioned": {"id": upn, "name": name}}
            ]
        }

    body.append({
        "type": "TextBlock",
        "text": f"🤖 AI Todo Generator · {now}",
        "size": "Small", "isSubtle": True, "wrap": True, "spacing": "Medium",
    })
    return content


def _teams_payload(message: str, alert, value: Optional[float] = None) -> dict:
    """Payload cho Power Automate webhook.

    TEAMS_PAYLOAD_MODE:
    - "message" (mặc định cho template forward attachments): {type:message,attachments:[card]}.
    - "card": chỉ nội dung AdaptiveCard trần.
    - "fields": JSON đơn giản {title,text,mentionUpn,mentionName} cho flow tự dựng card.
    """
    mode = os.environ.get("TEAMS_PAYLOAD_MODE", "message")
    mention_name = TEAMS_MENTION_NAME or (TEAMS_MENTION_UPN.split("@")[0] if TEAMS_MENTION_UPN else "")

    if mode == "fields":
        return {
            "title": f"🔔 {getattr(alert, 'label', None) or 'Cảnh báo'}",
            "text": message,
            "mentionUpn": TEAMS_MENTION_UPN,
            "mentionName": mention_name,
        }

    content = _build_card(alert, message, value)
    if mode == "card":
        return content
    return {
        "type": "message",
        "attachments": [
            {"contentType": "application/vnd.microsoft.card.adaptive", "content": content}
        ],
    }


async def _send_teams(message: str, alert, value: Optional[float] = None) -> bool:
    if not TEAMS_WEBHOOK_URL:
        print("[notifier] TEAMS_WEBHOOK_URL chưa cấu hình — bỏ qua gửi Teams")
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(TEAMS_WEBHOOK_URL, json=_teams_payload(message, alert, value))
            ok = r.status_code in (200, 202)
            if not ok:
                print(f"[notifier] Teams trả {r.status_code}: {r.text[:300]}")
            return ok
    except Exception as e:
        print(f"[notifier] Teams error: {e}")
        return False


async def _send_zalo(message: str, alert) -> bool:
    # Stub đợt này. Khi làm thật:
    # POST https://openapi.zalo.me/v3.0/oa/message
    #   headers={"access_token": ZALO_OA_ACCESS_TOKEN, "Content-Type": "application/json"}
    #   json={"recipient": {"user_id": ZALO_RECIPIENT_ID}, "message": {"text": message}}
    #   success khi resp.json().get("error", 0) == 0
    print(f"[notifier] (stub) Zalo: {message}")
    return False


async def send_notification(channel: str, message: str, alert, value: Optional[float] = None) -> bool:
    if channel == "teams":
        return await _send_teams(message, alert, value)
    if channel == "zalo":
        return await _send_zalo(message, alert)
    print(f"[notifier] channel không hỗ trợ: {channel}")
    return False
