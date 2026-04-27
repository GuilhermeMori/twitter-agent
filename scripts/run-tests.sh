#!/bin/bash

# Script to run the full test suite locally before pushing to CI/CD
# This helps catch issues early and speeds up development

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Running Full Test Suite${NC}\n"

# Check if we're in the project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 passed${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Backend Tests
print_section "1️⃣  Backend Linting"

cd backend

echo "Running flake8..."
flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
check_success "flake8 (critical errors)"

flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
check_success "flake8 (style warnings)"

echo -e "\nRunning black..."
black --check src/ tests/
check_success "black"

echo -e "\nRunning mypy..."
mypy src/ --ignore-missing-imports
check_success "mypy"

print_section "2️⃣  Backend Unit Tests"

pytest tests/ \
    --ignore=tests/integration/ \
    --ignore=tests/e2e/ \
    -v \
    --tb=short
check_success "Unit tests"

print_section "3️⃣  Backend Property-Based Tests"

HYPOTHESIS_PROFILE=ci pytest tests/ \
    -k "properties" \
    -v \
    --tb=short
check_success "Property-based tests"

print_section "4️⃣  Backend Integration Tests"

pytest tests/integration/ \
    -v \
    --tb=short
check_success "Integration tests"

print_section "5️⃣  Backend Coverage Check"

pytest tests/ \
    --ignore=tests/e2e/ \
    -v \
    --tb=short \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=80
check_success "Coverage check (80% threshold)"

echo -e "\n${GREEN}📊 Coverage report generated: backend/htmlcov/index.html${NC}"

cd ..

# Frontend Tests
print_section "6️⃣  Frontend Linting"

cd frontend

echo "Running ESLint..."
npm run lint
check_success "ESLint"

echo -e "\nRunning TypeScript type check..."
npm run type-check
check_success "TypeScript"

cd ..

# Summary
print_section "✨ Test Suite Complete"

echo -e "${GREEN}All tests passed! ✅${NC}"
echo -e "${GREEN}You're ready to push to CI/CD 🚀${NC}\n"

echo -e "Next steps:"
echo -e "  1. Review coverage report: ${YELLOW}backend/htmlcov/index.html${NC}"
echo -e "  2. Commit your changes: ${YELLOW}git add . && git commit -m 'Your message'${NC}"
echo -e "  3. Push to GitHub: ${YELLOW}git push${NC}\n"
