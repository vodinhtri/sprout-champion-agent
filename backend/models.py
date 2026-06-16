from enum import Enum
from pydantic import BaseModel
from typing import List, Literal, Optional


class UserPreferences(BaseModel):
    interests: List[str] = ["finance", "news", "tech"]
    name: Optional[str] = "User"


class TodoItem(BaseModel):
    id: str
    title: str
    description: str
    action: str
    rationale: str
    priority: str  # urgent | normal | info
    category: str  # finance | news | lifestyle | work | entertainment
    data_point: Optional[str] = None
    link: Optional[str] = None  # URL nguồn (bài báo / trang coin) → map sang cột Link
    done: bool = False  # trạng thái hoàn thành (đánh dấu trên UI) → map sang cột Status


class SyncNotionRequest(BaseModel):
    todos: List[TodoItem]


class AssetType(str, Enum):
    crypto = "crypto"            # symbol: bitcoin/ethereum/solana/binancecoin (id CoinGecko)
    gold_usd = "gold_usd"        # vàng thế giới USD/oz
    gold_vnd = "gold_vnd"        # vàng SJC, VND/lượng
    exchange_rate = "exchange_rate"  # symbol: USD_VND / USD_EUR / USD_JPY


class AlertCreate(BaseModel):
    kind: Literal["price", "time"] = "price"
    # --- price ---
    asset_type: Optional[AssetType] = None
    symbol: Optional[str] = None         # "bitcoin", "USD_VND", "" cho gold_vnd
    target_value: Optional[float] = None
    direction: Optional[Literal["above", "below"]] = None
    currency: str = "VND"                # "USD" | "VND"
    # --- time ---
    remind_at: Optional[str] = None      # ISO datetime; bắt buộc khi kind == "time"
    # --- chung ---
    channel: Literal["teams", "zalo"] = "teams"
    label: Optional[str] = None          # tự sinh nếu trống
    note: Optional[str] = None           # ghi chú: đang muốn làm gì khi cảnh báo kích hoạt
    notify_email: Optional[str] = None   # email VNG được @mention (id trước @ làm tên hiển thị)


class Alert(AlertCreate):
    id: str
    status: Literal["active", "triggered"] = "active"
    created_at: str
    last_checked_at: Optional[str] = None
    last_triggered_at: Optional[str] = None
    last_value: Optional[float] = None
