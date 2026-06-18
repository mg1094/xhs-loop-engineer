#!/bin/bash
# Start both backend (FastAPI) and frontend (Vue/Vite) in one command.
# Usage: ./start.sh

set -e

echo "🚀 Starting XHS Loop Engineer..."

# Trap to kill both processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}
trap cleanup INT TERM

# Start backend
echo "📦 Starting backend on http://localhost:8000"
uv run uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "🎨 Starting frontend on http://localhost:5173"
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both services running"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

wait
