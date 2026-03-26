#!/bin/bash

# Stop Backend and Frontend Services

echo "🛑 Stopping Nutrition Bot Services..."

# Kill processes on port 5001 (Backend)
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Stopping backend (port 5001)..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    echo "✓ Backend stopped"
else
    echo "Backend not running on port 5001"
fi

# Kill processes on port 3000 (Frontend)
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Stopping frontend (port 3000)..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo "✓ Frontend stopped"
else
    echo "Frontend not running on port 3000"
fi

echo ""
echo "✓ All services stopped"
