# AI Todo Generator — backend (FastAPI + price-alert scheduler)
# AgentBase runtime contract: listen :8080, expose GET /health
FROM python:3.12-slim

WORKDIR /app

# Cài deps trước để tận dụng cache layer
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Mã nguồn backend
COPY backend/ ./

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
