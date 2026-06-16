# Momentum — full app (React UI + FastAPI backend) cho AgentBase runtime
# Contract: listen :8080, expose GET /health

# --- Stage 1: build React frontend ---
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend + static UI ---
FROM python:3.12-slim
WORKDIR /app

# Cài deps trước để tận dụng cache layer
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Mã nguồn backend
COPY backend/ ./

# UI đã build → ./static (FastAPI serve qua StaticFiles)
COPY --from=frontend /fe/dist ./static

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
