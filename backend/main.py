import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load backend/.env if present, otherwise fall back to the project-root .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from models import AlertCreate, SyncNotionRequest, UserPreferences
from services import alert_store
from services.ai_service import generate_todos
from services.market_service import get_market_data
from services.news_service import get_news
from services.notifier import send_notification
from services.notion_service import NotionError, fetch_todos, sync_todos
from services.prediction_service import get_prediction
from services.scheduler import evaluate_once, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = start_scheduler()
    yield
    task.cancel()


app = FastAPI(title="Momentum", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục chứa React UI đã build (do Dockerfile copy vào ./static). Dev không có → serve API.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SERVE_SPA = os.path.isdir(STATIC_DIR)


@app.get("/")
def root():
    if SERVE_SPA:
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    return {"message": "Momentum API", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# AgentBase runtime contract: GET /health phải trả 200 khi sẵn sàng
@app.get("/health")
def health_runtime():
    return {"status": "ok"}


@app.post("/api/todos/generate")
async def generate(preferences: UserPreferences):
    try:
        news_task = asyncio.create_task(get_news(preferences.interests))
        market_task = asyncio.create_task(get_market_data())

        news_data, market_data = await asyncio.gather(news_task, market_task)

        todos = await generate_todos(news_data, market_data, preferences)

        return {
            "todos": todos,
            "generated_at": datetime.now().isoformat(),
            "data_sources": ["VnExpress", "CafeF", "CoinGecko", "Yahoo Finance", "Open Exchange Rates"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/todos/sync-notion")
async def sync_notion(req: SyncNotionRequest):
    try:
        return await sync_todos([t.model_dump() for t in req.todos])
    except NotionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/todos/from-notion")
async def todos_from_notion():
    try:
        return await fetch_todos()
    except NotionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predict/{category}")
async def predict(category: str):
    try:
        return await get_prediction(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-data")
async def market_endpoint():
    return await get_market_data()


# ---------------------- Alerts (cảnh báo giá / nhắc giờ) ----------------------

import re

_VNG_EMAIL = re.compile(r"^[a-zA-Z0-9._%+-]+@vng\.com\.vn$")


def _validate_alert(data: AlertCreate):
    if not data.notify_email or not _VNG_EMAIL.match(data.notify_email):
        raise HTTPException(
            status_code=422,
            detail="Cần email VNG hợp lệ (dạng abc@vng.com.vn) để @mention.",
        )
    if data.kind == "price":
        if data.asset_type is None or data.target_value is None or data.direction is None:
            raise HTTPException(
                status_code=422,
                detail="Cảnh báo giá cần asset_type, target_value và direction.",
            )
    elif data.kind == "time":
        if not data.remind_at:
            raise HTTPException(status_code=422, detail="Nhắc giờ cần remind_at (ISO datetime).")


@app.post("/api/alerts")
async def create_alert(data: AlertCreate):
    _validate_alert(data)
    return await alert_store.add_alert(data)


@app.get("/api/alerts")
async def list_alerts():
    return await alert_store.load_alerts()


@app.delete("/api/alerts/{alert_id}")
async def remove_alert(alert_id: str):
    ok = await alert_store.delete_alert(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy alert.")
    return {"deleted": True}


@app.post("/api/alerts/check-now")
async def check_now():
    fired = await evaluate_once()
    return {"fired": fired}


@app.post("/api/alerts/test-notification")
async def test_notification(body: dict):
    channel = body.get("channel", "teams")
    message = body.get("message", "🔔 Test notification từ Momentum")

    class _Stub:
        label = "Test notification"
        kind = "price"
        target_value = None

    ok = await send_notification(channel, message, _Stub())
    return {"ok": ok}


# Serve React UI đã build (production). Mount SAU tất cả route /api & /health
# để các route đó được match trước; phần còn lại ("/", "/assets/*") do SPA xử lý.
if SERVE_SPA:
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
