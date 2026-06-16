"""Sync các todo do AI sinh ra lên một Notion database.

Đọc schema của database lúc chạy (GET /databases/{id}) nên tự khớp với tên &
kiểu cột của người dùng: cột Title (Job), cột rich_text (Note) và cột
Status/Select (Status). Nhờ vậy không cần hardcode kiểu cột — tránh lỗi 400 khi
cột Status là kiểu `status` thay vì `select`.
"""
import os
from typing import Any, Optional

import httpx

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionError(Exception):
    """Lỗi cấu hình hoặc lỗi phía Notion — map sang HTTP 400 ở tầng route."""


def _config() -> tuple[str, str]:
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")
    if not token or not db_id:
        raise NotionError("Thiếu NOTION_TOKEN hoặc NOTION_DATABASE_ID trong .env")
    return token, db_id


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _text(s: Optional[str], limit: int = 1900) -> str:
    # Notion giới hạn 2000 ký tự / text block; cắt cho an toàn.
    return (s or "").strip()[:limit]


def _status_value(prop: dict, done: bool) -> Optional[dict]:
    """Chọn option cho cột Status/Select theo trạng thái hoàn thành của todo.

    - done=True  → option kiểu hoàn thành ("Done" / "Complete" / "Hoàn thành").
    - done=False → option kiểu chưa làm ("Not started" / "To do").
    Cột kiểu `status` chỉ nhận option đã tồn tại nên luôn chọn từ danh sách hiện có;
    cột `select` chưa có option thì tự tạo theo tên mặc định.
    """
    ptype = prop["type"]  # "status" | "select"
    options = prop.get(ptype, {}).get("options", [])
    names = [o["name"] for o in options]

    if done:
        keywords = ("done", "complete", "finish", "hoàn", "xong")
        default_name = "Done"
        fallback = names[-1] if names else default_name
    else:
        keywords = ("not started", "to do", "todo", "chưa", "mới", "backlog", "open")
        default_name = "To do"
        fallback = names[0] if names else default_name

    if not options:
        # Chỉ select mới tạo được option mới; status thì không set được.
        return {"select": {"name": default_name}} if ptype == "select" else None

    chosen = next((n for n in names if any(k in n.lower() for k in keywords)), fallback)
    return {ptype: {"name": chosen}}


def _build_properties(schema: dict, todo: dict, done: bool) -> dict:
    """Map 1 todo → properties của Notion dựa trên schema thật của database."""
    props: dict[str, Any] = {}
    for name, meta in schema.items():
        ptype = meta["type"]
        lname = name.lower()

        if ptype == "title":  # cột Job
            props[name] = {
                "title": [{"text": {"content": _text(todo.get("title"), 200) or "(no title)"}}]
            }

        elif ptype == "rich_text" and ("note" in lname or "ghi" in lname):  # cột Note
            parts = []
            if todo.get("action"):
                parts.append(f"👉 {todo['action']}")
            if todo.get("rationale"):
                parts.append(f"💡 {todo['rationale']}")
            if todo.get("data_point"):
                parts.append(f"📊 {todo['data_point']}")
            note = "\n".join(parts) or _text(todo.get("description"))
            props[name] = {"rich_text": [{"text": {"content": _text(note)}}]}

        elif ptype in ("status", "select") and (
            "status" in lname or "trạng" in lname or "tình" in lname
        ):  # cột Status
            value = _status_value(meta, done)
            if value:
                props[name] = value

        elif ptype == "url" and "link" in lname:  # cột Link (không đụng url khác của user)
            props[name] = {"url": (todo.get("link") or None)}

    return props


def _title_of(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return _plain_text(prop.get("title"))
    return ""


def _normalize_title(title: Optional[str]) -> str:
    return (title or "").strip().lower()


async def _existing_pages(client: httpx.AsyncClient, token: str, db_id: str) -> dict:
    """Map {title-chuẩn-hoá -> page_id} của các row hiện có để sync không tạo trùng."""
    mapping: dict[str, str] = {}
    cursor: Optional[str] = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = await client.post(
            f"{NOTION_API}/databases/{db_id}/query", headers=_headers(token), json=body
        )
        if resp.status_code != 200:
            detail = resp.json().get("message", resp.text)
            raise NotionError(f"Không đọc được database Notion: {detail}")
        data = resp.json()
        for page in data.get("results", []):
            key = _normalize_title(_title_of(page))
            if key and key not in mapping:
                mapping[key] = page["id"]
        if data.get("has_more"):
            cursor = data.get("next_cursor")
        else:
            break
    return mapping


async def sync_todos(todos: list[dict]) -> dict:
    """Sync todo lên database.

    Todo trùng title (không phân biệt hoa/thường) → UPDATE row sẵn có, cập nhật cả
    cột Status theo trạng thái done. Todo chưa có → tạo mới. Nhờ vậy bấm sync nhiều
    lần không sinh row trùng.
    """
    token, db_id = _config()

    async with httpx.AsyncClient(timeout=20) as client:
        # 1) Đọc schema — đồng thời validate token + đã share integration chưa.
        schema_resp = await client.get(
            f"{NOTION_API}/databases/{db_id}", headers=_headers(token)
        )
        if schema_resp.status_code != 200:
            detail = schema_resp.json().get("message", schema_resp.text)
            raise NotionError(f"Không đọc được database Notion: {detail}")
        schema = schema_resp.json().get("properties", {})

        # 1b) Bảo đảm có cột URL (tên "Link"); chưa có thì tạo mới qua API.
        #     Best-effort: nếu integration không có quyền sửa schema thì bỏ qua link.
        if not any(m.get("type") == "url" for m in schema.values()):
            patch = await client.patch(
                f"{NOTION_API}/databases/{db_id}",
                headers=_headers(token),
                json={"properties": {"Link": {"url": {}}}},
            )
            if patch.status_code == 200:
                schema = patch.json().get("properties", schema)

        # 2) Lập map title -> page_id để tránh tạo trùng.
        existing = await _existing_pages(client, token, db_id)

        # 3) Đã có thì update, chưa có thì tạo mới.
        created = updated = 0
        errors: list[dict] = []
        for todo in todos:
            done = bool(todo.get("done"))
            props = _build_properties(schema, todo, done)
            key = _normalize_title(todo.get("title"))
            page_id = existing.get(key)

            if page_id:
                resp = await client.patch(
                    f"{NOTION_API}/pages/{page_id}",
                    headers=_headers(token),
                    json={"properties": props},
                )
                if resp.status_code == 200:
                    updated += 1
                else:
                    errors.append(
                        {"title": todo.get("title"), "error": resp.json().get("message", resp.text)}
                    )
            else:
                resp = await client.post(
                    f"{NOTION_API}/pages",
                    headers=_headers(token),
                    json={"parent": {"database_id": db_id}, "properties": props},
                )
                if resp.status_code in (200, 201):
                    created += 1
                    if key:  # batch có todo trùng title phía sau → update, không tạo lần 2
                        existing[key] = resp.json().get("id")
                else:
                    errors.append(
                        {"title": todo.get("title"), "error": resp.json().get("message", resp.text)}
                    )

    return {
        "synced": created + updated,
        "created": created,
        "updated": updated,
        "failed": len(errors),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Đọc ngược: Notion database -> danh sách todo để hiển thị trên UI
# ---------------------------------------------------------------------------

def _plain_text(rich: Optional[list]) -> str:
    return "".join(part.get("plain_text", "") for part in (rich or []))


def _parse_note(note: str) -> tuple[str, str, str, str]:
    """Tách lại cột Note (đã ghép khi sync) về action / rationale / data_point.

    Định dạng lúc sync: "👉 action", "💡 rationale", "📊 data_point" theo dòng.
    Nếu row được tạo tay không có prefix → dồn toàn bộ vào action cho dễ đọc.
    """
    action = rationale = data_point = ""
    extra: list[str] = []
    for raw in (note or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("👉"):
            action = s.lstrip("👉").strip()
        elif s.startswith("💡"):
            rationale = s.lstrip("💡").strip()
        elif s.startswith("📊"):
            data_point = s.lstrip("📊").strip()
        else:
            extra.append(s)
    extra_text = "\n".join(extra)
    if not (action or rationale or data_point) and extra_text:
        action, extra_text = extra_text, ""
    return action, rationale, data_point, extra_text


def _page_to_todo(page: dict) -> dict:
    props = page.get("properties", {})
    title = note = status = ""
    link = None
    for name, p in props.items():
        ptype = p["type"]
        lname = name.lower()
        if ptype == "title":
            title = _plain_text(p.get("title"))
        elif ptype == "rich_text" and ("note" in lname or "ghi" in lname):
            note = _plain_text(p.get("rich_text"))
        elif ptype in ("status", "select"):
            sel = p.get(ptype)
            status = sel.get("name", "") if sel else ""
        elif ptype == "url" and "link" in lname:
            link = p.get("url") or None

    action, rationale, data_point, extra = _parse_note(note)
    return {
        "id": page.get("id", ""),
        "title": title or "(không tiêu đề)",
        "description": extra,
        "action": action,
        "rationale": rationale,
        "priority": "normal",
        "category": "work",
        # Không có data_point thực thì hiển thị Status ở chip góc phải.
        "data_point": data_point or status or None,
        "status": status,
        "link": link,
    }


async def fetch_todos() -> dict:
    """Query database và trả các row dưới dạng todo để UI render."""
    token, db_id = _config()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{NOTION_API}/databases/{db_id}/query",
            headers=_headers(token),
            json={"page_size": 100},
        )
        if resp.status_code != 200:
            detail = resp.json().get("message", resp.text)
            raise NotionError(f"Không đọc được database Notion: {detail}")
        results = resp.json().get("results", [])

    # Bỏ các row trống (không tiêu đề & không nội dung) để khỏi hiện card rỗng.
    todos = [
        t
        for t in (_page_to_todo(p) for p in results)
        if t["title"] != "(không tiêu đề)" or t["action"] or t["rationale"]
    ]
    return {"todos": todos, "count": len(todos)}
