#!/bin/bash

# =============================================================================
# THE INTAKER - SAN FRANCISCO SHOWCASE LAUNCHER
# =============================================================================
# This script prepares the environment and launches the frontend in Kiosk mode.

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}    THE INTAKER - SAN FRANCISCO PROTOTYPE LAUNCHER   ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Check Dependencies
echo -e "${YELLOW}[1/4] Checking dependencies...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}Error: node_modules not found. Running npm install...${NC}"
    cd frontend && npm install && cd ..
fi

if [ ! -d "frontend/dist" ]; then
    echo -e "${RED}Error: Production build (dist) not found. Building now...${NC}"
    cd frontend && npm run build && cd ..
fi

# 2. Start Preview Server
echo -e "${YELLOW}[2/4] Starting local preview server...${NC}"
cd frontend
# Run vite preview in background
npm run preview > /dev/null 2>&1 &
PREVIEW_PID=$!

# 3. Wait for server (Port 4173 is default for vite preview)
echo -e "${YELLOW}[3/4] Waiting for server to initialize...${NC}"
MAX_RETRIES=10
COUNT=0
while ! curl -s http://localhost:4173 > /dev/null; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}Error: Server failed to start.${NC}"
        kill $PREVIEW_PID
        exit 1
    fi
done

echo -e "${GREEN}Success: Server is live at http://localhost:4173${NC}"

# 4. Launch Google Chrome in Kiosk Mode
echo -e "${YELLOW}[4/4] Launching Chrome in Showcase Mode...${NC}"
# Note: On macOS, we use 'open' or call the binary directly
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --kiosk "http://localhost:4173" --no-first-run --no-default-browser-check &

echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}    DEMO ACTIVE. Press Ctrl+C in this terminal to stop.${NC}"
echo -e "${BLUE}====================================================${NC}"

# Wait for Ctrl+C
trap "kill $PREVIEW_PID; echo -e '\n${YELLOW}Demo stopped.${NC}'; exit" INT
wait
