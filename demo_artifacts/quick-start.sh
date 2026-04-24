#!/bin/bash
#
# Find Evil Agent - Playwright Demo Quick Start
#
# This script helps you set up and run the automated demo recording
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Find Evil Agent - Playwright Demo Recording${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check if service is running
check_service() {
    local url=$1
    local name=$2

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        echo -e "${GREEN}✅ $name is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $name is NOT running${NC}"
        return 1
    fi
}

# Step 1: Check dependencies
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check Playwright browsers
if ! npx playwright --version &> /dev/null; then
    echo "Installing Playwright browsers..."
    npx playwright install chromium
else
    echo -e "${GREEN}✅ Playwright browsers installed${NC}"
fi

echo ""

# Step 2: Check services
echo -e "${YELLOW}🔍 Checking required services...${NC}"

SERVICES_OK=true

# React UI
if ! check_service "http://localhost:15173" "React UI (port 15173)"; then
    echo -e "${YELLOW}   Start with: cd ../frontend && npm run dev${NC}"
    SERVICES_OK=false
fi

# Backend API
if ! check_service "http://localhost:18000" "Backend API (port 18000)"; then
    echo -e "${YELLOW}   Start with: cd .. && docker-compose up${NC}"
    SERVICES_OK=false
fi

# Ollama (optional)
if check_service "http://192.168.12.124:11434/api/tags" "Ollama Service"; then
    :
else
    echo -e "${YELLOW}   ⚠️  Ollama not accessible (optional - may be on different network)${NC}"
fi

echo ""

# Step 3: Check if services are ready
if [ "$SERVICES_OK" = false ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ⚠️  REQUIRED SERVICES NOT RUNNING${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Please start the required services before running the demo:"
    echo ""
    echo "Terminal 1 - Backend:"
    echo "  cd .. && docker-compose up"
    echo ""
    echo "Terminal 2 - React UI:"
    echo "  cd ../frontend && npm run dev"
    echo ""
    echo "Then run this script again:"
    echo "  ./quick-start.sh"
    echo ""
    exit 1
fi

# Step 4: Create directories
echo -e "${YELLOW}📁 Creating output directories...${NC}"
mkdir -p screenshots
mkdir -p test-results
echo -e "${GREEN}✅ Directories ready${NC}"
echo ""

# Step 5: Ready to run
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ALL SYSTEMS READY${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Choose an option:${NC}"
echo ""
echo "  1) Record demo (full walkthrough with video + screenshots)"
echo "  2) Quick test (fast, no video)"
echo "  3) Debug mode (step through tests)"
echo "  4) View previous report"
echo "  5) Cancel"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🎬 Starting demo recording...${NC}"
        echo ""
        npm run record-demo
        ;;
    2)
        echo ""
        echo -e "${BLUE}⚡ Running fast tests...${NC}"
        echo ""
        npm test -- --project=fast-testing
        ;;
    3)
        echo ""
        echo -e "${BLUE}🐛 Starting debug mode...${NC}"
        echo ""
        npm run test:debug
        ;;
    4)
        echo ""
        echo -e "${BLUE}📊 Opening test report...${NC}"
        echo ""
        npm run show-report
        ;;
    5)
        echo ""
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

# Step 6: Show results
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ DEMO RECORDING COMPLETE${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📁 Output files:${NC}"
echo ""
ls -lh screenshots/*.png 2>/dev/null | awk '{print "   📸 " $9 " (" $5 ")"}'
echo ""
ls -lh test-results/*/video.webm 2>/dev/null | awk '{print "   📹 " $9 " (" $5 ")"}'
echo ""
echo -e "${BLUE}📊 View full report:${NC}"
echo "   npm run show-report"
echo ""
echo -e "${BLUE}🎬 Convert video to GIF:${NC}"
echo "   See PLAYWRIGHT_AUTOMATION.md for instructions"
echo ""
echo -e "${GREEN}✅ Ready for DevPost submission!${NC}"
echo ""
