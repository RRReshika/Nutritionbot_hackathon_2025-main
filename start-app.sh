#!/bin/bash

# Start Backend and Frontend Together
# This script starts both the Flask backend and Next.js frontend

echo "🚀 Starting Nutrition Bot Full Stack Application..."
echo ""

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend directory exists
if [ ! -d "-/vrm-next-app/backend" ]; then
    echo -e "${YELLOW}Error: Backend directory not found!${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "-/vrm-next-app" ]; then
    echo -e "${YELLOW}Error: Frontend directory not found!${NC}"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill any existing processes on ports
echo -e "${BLUE}Checking for existing processes...${NC}"
if check_port 5001; then
    echo -e "${YELLOW}Port 5001 is in use. Killing existing process...${NC}"
    lsof -ti:5001 | xargs kill -9 2>/dev/null
fi

if check_port 3000; then
    echo -e "${YELLOW}Port 3000 is in use. Killing existing process...${NC}"
    lsof -ti:3000 | xargs kill -9 2>/dev/null
fi

echo ""

# Start backend in background
echo -e "${GREEN}Starting Backend (Flask) on port 5001...${NC}"
cd -/vrm-next-app/backend

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${BLUE}Virtual environment activated${NC}"
fi

# Start Flask backend
nohup python app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}Starting Frontend (Next.js) on port 3000...${NC}"
cd ../..
cd -/vrm-next-app
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Application is starting!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Application URL:${NC} http://localhost:3000"
echo -e "${BLUE}Backend API (internal):${NC}  http://localhost:5001"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f -/vrm-next-app/backend/backend.log"
echo -e "  Frontend: tail -f -/vrm-next-app/frontend.log"
echo ""
echo -e "${YELLOW}To stop both services:${NC}"
echo -e "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop watching logs${NC}"
echo ""

# Follow logs
tail -f -/vrm-next-app/backend/backend.log -/vrm-next-app/frontend.log
