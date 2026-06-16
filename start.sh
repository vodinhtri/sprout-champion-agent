#!/bin/bash
# Momentum — Quick Start

echo "🤖 Momentum — Starting..."

# Load nvm if available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
nvm use 21 2>/dev/null || true

# Check ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
  if [ -f backend/.env ]; then
    export $(grep -v '^#' backend/.env | xargs)
  fi
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "⚠️  Thiếu ANTHROPIC_API_KEY!"
  echo "   Tạo file backend/.env và thêm: ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

echo "✅ API key found"

# Start backend
echo "🚀 Starting backend on :8000..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 2

# Start frontend
echo "🚀 Starting frontend on :5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ App ready at: http://localhost:5173"
echo "   Backend API:   http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT INT
wait
