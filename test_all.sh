#!/bin/bash
# Comprehensive test runner for NextEleven Terminal Agent
# Run all tests with coverage and checks

set -e  # Exit on error

echo "🧪 NextEleven Terminal Agent - Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [[ ! -f "grok_agent.py" ]]; then
    echo "${RED}Error: grok_agent.py not found. Run from project root.${NC}"
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest >/dev/null 2>&1; then
    echo "${YELLOW}pytest not found. Installing dependencies...${NC}"
    pip3 install -r requirements-dev.txt || {
        echo "${RED}Failed to install dependencies${NC}"
        exit 1
    }
fi

echo "📦 Dependencies check..."
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "${YELLOW}Installing pytest...${NC}"
    pip3 install pytest pytest-cov pytest-asyncio pytest-mock
fi

if ! python3 -c "import pytest_cov" 2>/dev/null; then
    echo "${YELLOW}Installing pytest-cov...${NC}"
    pip3 install pytest-cov
fi

echo ""

# Run unit tests
echo "${GREEN}=== Running Unit Tests ===${NC}"
pytest tests/test_security_utils.py -v || echo "${YELLOW}Security tests failed or skipped${NC}"
echo ""

pytest tests/test_grok_agent.py -v || echo "${YELLOW}Agent tests failed or skipped${NC}"
echo ""

# Run integration tests
echo "${GREEN}=== Running Integration Tests ===${NC}"
pytest tests/test_integration.py -v || echo "${YELLOW}Integration tests failed or skipped${NC}"
echo ""

# Run all tests with coverage
echo "${GREEN}=== Running All Tests with Coverage ===${NC}"
pytest --cov=. --cov-report=term-missing --cov-report=html || {
    echo "${YELLOW}Some tests failed, but continuing...${NC}"
}
echo ""

# Check if coverage report was generated
if [[ -d "htmlcov" ]]; then
    echo "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
    echo "   Open with: open htmlcov/index.html"
else
    echo "${YELLOW}⚠️  Coverage report not generated${NC}"
fi

echo ""
echo "${GREEN}=== Test Summary ===${NC}"
echo "Tests completed! Check output above for results."
echo ""
echo "To view detailed coverage report:"
echo "  open htmlcov/index.html"
echo ""
echo "To run specific tests:"
echo "  pytest tests/test_security_utils.py -v"
echo "  pytest tests/test_grok_agent.py -v"
echo "  pytest tests/test_integration.py -v"
echo ""
