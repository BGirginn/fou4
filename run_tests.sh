#!/bin/bash

# Kali Tool - Test Runner Script
# Runs the test suite with various options

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╦╔═╔═╗╦  ╦  ═╦═╔═╗╔═╗╦  "
echo "╠╩╗╠═╣║  ║   ║ ║ ║║ ║║  "
echo "╩ ╩╩ ╩╩═╝╩   ╩ ╚═╝╚═╝╩═╝"
echo -e "${NC}"
echo -e "${GREEN}Test Suite Runner${NC}\n"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Parse arguments
MODE=${1:-"all"}

case $MODE in
    "all")
        echo -e "${BLUE}Running all tests...${NC}\n"
        pytest -v
        ;;
    
    "unit")
        echo -e "${BLUE}Running unit tests...${NC}\n"
        pytest tests/test_utils.py tests/test_parsing.py -v
        ;;
    
    "integration")
        echo -e "${BLUE}Running integration tests...${NC}\n"
        pytest tests/test_integration.py -v
        ;;
    
    "coverage")
        echo -e "${BLUE}Running tests with coverage...${NC}\n"
        pytest --cov=. --cov-report=term --cov-report=html -v
        echo -e "\n${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;
    
    "quick")
        echo -e "${BLUE}Running quick tests (no slow tests)...${NC}\n"
        pytest -v -m "not slow"
        ;;
    
    "failed")
        echo -e "${BLUE}Running last failed tests...${NC}\n"
        pytest --lf -v
        ;;
    
    "debug")
        echo -e "${BLUE}Running tests with debugging...${NC}\n"
        pytest -v -s -l --tb=long
        ;;
    
    "parser")
        echo -e "${BLUE}Running parser tests...${NC}\n"
        pytest tests/test_parsing.py -v
        ;;
    
    "utils")
        echo -e "${BLUE}Running utility tests...${NC}\n"
        pytest tests/test_utils.py -v
        ;;
    
    "clean")
        echo -e "${YELLOW}Cleaning test artifacts...${NC}"
        rm -rf .pytest_cache
        rm -rf htmlcov
        rm -rf .coverage
        rm -f test_*.db
        rm -rf __pycache__
        rm -rf tests/__pycache__
        echo -e "${GREEN}Cleanup complete${NC}"
        ;;
    
    "help"|"-h"|"--help")
        echo "Usage: ./run_tests.sh [MODE]"
        echo ""
        echo "Modes:"
        echo "  all          Run all tests (default)"
        echo "  unit         Run only unit tests"
        echo "  integration  Run only integration tests"
        echo "  coverage     Run tests with coverage report"
        echo "  quick        Run quick tests (skip slow tests)"
        echo "  failed       Run only last failed tests"
        echo "  debug        Run with debugging output"
        echo "  parser       Run only parser tests"
        echo "  utils        Run only utility tests"
        echo "  clean        Clean test artifacts"
        echo "  help         Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh quick"
        ;;
    
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Exit status
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Tests completed successfully${NC}"
else
    echo -e "\n${RED}✗ Tests failed${NC}"
    exit 1
fi

