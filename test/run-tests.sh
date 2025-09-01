#!/bin/bash

# Local Test Runner for WhatsApp Business Odoo Module
# This script allows you to run tests locally before pushing to CI/CD

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="$PROJECT_ROOT/test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_status $BLUE "=========================================="
    print_status $BLUE "$1"
    print_status $BLUE "=========================================="
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -t, --test TYPE     Run specific test type (syntax|install|full)"
    echo "  -c, --clean         Clean up test environment before running"
    echo "  -v, --verbose       Verbose output"
    echo "  --no-cache          Build Docker images without cache"
    echo ""
    echo "Examples:"
    echo "  $0                  Run all tests"
    echo "  $0 -t syntax        Run syntax checks only"
    echo "  $0 -t install       Run installation test only"
    echo "  $0 -c               Clean and run all tests"
}

# Parse command line arguments
TEST_TYPE="full"
CLEAN=false
VERBOSE=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -t|--test)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to clean up test environment
cleanup_test_env() {
    print_header "Cleaning up test environment"
    
    # Stop and remove containers
    docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v 2>/dev/null || true
    
    # Remove test image
    docker image rm whatsapp-notify-test:latest 2>/dev/null || true
    
    # Clean test directories
    if [ -d "$TEST_DIR" ]; then
        print_status $YELLOW "Cleaning test directories..."
        rm -rf "$TEST_DIR"/{logs,results,filestore}/*
    fi
    
    print_status $GREEN "Cleanup completed"
}

# Function to setup test environment
setup_test_env() {
    print_header "Setting up test environment"
    
    # Create test directories
    mkdir -p "$TEST_DIR"/{logs,results,filestore}
    chmod 755 "$TEST_DIR"/{logs,results,filestore}
    
    print_status $GREEN "Test directories created"
}

# Function to run syntax checks
run_syntax_checks() {
    print_header "Running syntax and lint checks"
    
    local errors=0
    
    # Check if required tools are installed
    if ! command -v python3 &> /dev/null; then
        print_status $RED "Error: Python3 is required but not installed"
        return 1
    fi
    
    # Python syntax check
    print_status $YELLOW "Checking Python syntax..."
    if find "$PROJECT_ROOT/odoo_module" -name "*.py" -exec python3 -m py_compile {} \; 2>/dev/null; then
        print_status $GREEN "✓ Python syntax check passed"
    else
        print_status $RED "✗ Python syntax check failed"
        errors=$((errors + 1))
    fi
    
    # XML syntax check (if xmllint is available)
    if command -v xmllint &> /dev/null; then
        print_status $YELLOW "Checking XML syntax..."
        if find "$PROJECT_ROOT/odoo_module" -name "*.xml" -exec xmllint --noout {} \; 2>/dev/null; then
            print_status $GREEN "✓ XML syntax check passed"
        else
            print_status $RED "✗ XML syntax check failed"
            errors=$((errors + 1))
        fi
    else
        print_status $YELLOW "⚠ xmllint not found, skipping XML syntax check"
    fi
    
    # Check module structure
    print_status $YELLOW "Checking module structure..."
    local required_files=(
        "odoo_module/__manifest__.py"
        "odoo_module/__init__.py"
        "odoo_module/models/__init__.py"
        "odoo_module/views/menu.xml"
        "odoo_module/security/ir.model.access.csv"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            print_status $RED "✗ Missing required file: $file"
            errors=$((errors + 1))
        else
            print_status $GREEN "✓ Found: $file"
        fi
    done
    
    if [ $errors -eq 0 ]; then
        print_status $GREEN "All syntax checks passed!"
        return 0
    else
        print_status $RED "$errors syntax check(s) failed!"
        return 1
    fi
}

# Function to run installation test
run_installation_test() {
    print_header "Running Odoo module installation test"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_status $RED "Error: Docker is required but not installed"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_status $RED "Error: Docker Compose is required but not installed"
        return 1
    fi
    
    # Build options
    local build_args=""
    if [ "$NO_CACHE" = true ]; then
        build_args="--no-cache"
    fi
    
    # Build test image
    print_status $YELLOW "Building test Docker image..."
    if [ "$VERBOSE" = true ]; then
        docker build $build_args -f "$PROJECT_ROOT/Dockerfile.test" -t whatsapp-notify-test:latest "$PROJECT_ROOT"
    else
        docker build $build_args -f "$PROJECT_ROOT/Dockerfile.test" -t whatsapp-notify-test:latest "$PROJECT_ROOT" > /dev/null
    fi
    
    # Run installation test
    print_status $YELLOW "Running installation test..."
    
    cd "$PROJECT_ROOT"
    if [ "$VERBOSE" = true ]; then
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    else
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit > /dev/null 2>&1
    fi
    
    # Check results
    if [ -f "$TEST_DIR/results/test-status.txt" ]; then
        local status=$(cat "$TEST_DIR/results/test-status.txt")
        if [ "$status" = "SUCCESS" ]; then
            print_status $GREEN "✓ Installation test passed!"
            return 0
        else
            print_status $RED "✗ Installation test failed!"
            if [ -f "$TEST_DIR/results/installation-test.log" ]; then
                print_status $YELLOW "Last 20 lines of test log:"
                tail -20 "$TEST_DIR/results/installation-test.log"
            fi
            return 1
        fi
    else
        print_status $RED "✗ Installation test failed - no status file found"
        return 1
    fi
}

# Function to run full test suite
run_full_tests() {
    print_header "Running full test suite"
    
    local failed_tests=0
    
    # Run syntax checks
    if ! run_syntax_checks; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Run installation test
    if ! run_installation_test; then
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test summary
    print_header "Test Summary"
    if [ $failed_tests -eq 0 ]; then
        print_status $GREEN "🎉 All tests passed successfully!"
        return 0
    else
        print_status $RED "💥 $failed_tests test suite(s) failed!"
        return 1
    fi
}

# Main execution
main() {
    print_header "WhatsApp Business Odoo Module Test Runner"
    
    # Clean up if requested
    if [ "$CLEAN" = true ]; then
        cleanup_test_env
    fi
    
    # Setup test environment
    setup_test_env
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run tests based on type
    case $TEST_TYPE in
        syntax)
            run_syntax_checks
            ;;
        install)
            run_installation_test
            ;;
        full)
            run_full_tests
            ;;
        *)
            print_status $RED "Unknown test type: $TEST_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    # Cleanup Docker containers
    print_status $YELLOW "Cleaning up Docker containers..."
    docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
    
    exit $exit_code
}

# Trap to ensure cleanup on script exit
trap 'docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v 2>/dev/null || true' EXIT

# Run main function
main "$@"