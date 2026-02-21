#!/bin/bash

# Re-Hydrate Script for The Intaker (M4 Setup)
# Usage: ./rehydrate.sh

echo "💧 Starting Re-Hydration Process..."

# 1. Setup Backend
echo "📦 Setting up Backend (Voice Bridge)..."
cd services/voice-bridge
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   - Created virtual environment"
fi

source venv/bin/activate
echo "   - Installing Python dependencies..."
pip install -r requirements.txt

# Return to root
cd ../../

# 2. Setup Frontend
echo "🎨 Setting up Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "   - Installing Node modules (this may take a minute)..."
    npm install
fi

echo "✅ Re-Hydration Complete!"
echo "---------------------------------------------------"
echo "To run the app:"
echo "1. Backend:  cd services/voice-bridge && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "2. Frontend: cd frontend && npm run dev"
echo "---------------------------------------------------"
