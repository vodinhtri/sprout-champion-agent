import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from models import UserPreferences
from services.ai_service import generate_todos
from services.market_service import get_market_data
from services.news_service import get_news

app = FastAPI(title="AI Todo Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "AI Todo Generator API", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


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


@app.get("/api/market-data")
async def market_endpoint():
    return await get_market_data()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
