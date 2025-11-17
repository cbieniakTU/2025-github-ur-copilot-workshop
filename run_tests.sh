#!/bin/bash
# Test runner script for Pomodoro Timer App
#
# Usage:
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh unit              # Run only unit tests  
#   ./run_tests.sh integration       # Run only integration tests
#   ./run_tests.sh coverage          # Run tests with HTML coverage report
#   ./run_tests.sh quick             # Run tests without coverage

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Default pytest options
PYTEST_OPTS="-v --tb=short"

case "${1:-all}" in
    "unit")
        echo -e "${GREEN}Running unit tests only...${NC}"
        python -m pytest tests/test_app.py $PYTEST_OPTS --cov=app --cov-report=term-missing
        ;;
    "integration")
        echo -e "${GREEN}Running integration tests only...${NC}"
        python -m pytest tests/test_integration.py $PYTEST_OPTS
        ;;
    "coverage")
        echo -e "${GREEN}Running all tests with HTML coverage report...${NC}"
        python -m pytest tests/ $PYTEST_OPTS --cov=app --cov-report=html --cov-report=term-missing
        echo -e "${BLUE}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo -e "${GREEN}Running tests without coverage...${NC}"
        python -m pytest tests/ $PYTEST_OPTS
        ;;
    "all"|"")
        echo -e "${GREEN}Running all tests with coverage...${NC}"
        python -m pytest tests/ $PYTEST_OPTS --cov=app --cov-report=term-missing
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [unit|integration|coverage|quick|all|help]"
        echo ""
        echo "Options:"
        echo "  unit         Run only unit tests (test_app.py)"
        echo "  integration  Run only integration tests (test_integration.py)"
        echo "  coverage     Run all tests with HTML coverage report"
        echo "  quick        Run all tests without coverage reporting"
        echo "  all          Run all tests with coverage (default)"
        echo "  help         Show this help message"
        exit 0
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Use '$0 help' to see available options"
        exit 1
        ;;
esac

echo -e "${GREEN}Tests completed!${NC}"