#!/bin/bash

# Module Installation Test Script
# This script tests the WhatsApp Business module installation

set -e

echo "========================================"
echo "WhatsApp Business Module Installation Test"
echo "========================================"

# Configuration
ODOO_URL=${ODOO_URL:-"http://odoo-test:8069"}
TEST_DB=${POSTGRES_DB:-"odoo_test"}
RESULTS_DIR="/opt/test-results"
LOG_FILE="$RESULTS_DIR/installation-test.log"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if Odoo is ready
wait_for_odoo() {
    log "Waiting for Odoo to be ready..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$ODOO_URL/web/health" > /dev/null 2>&1; then
            log "Odoo is ready!"
            return 0
        fi
        log "Attempt $attempt/$max_attempts: Odoo not ready, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log "ERROR: Odoo did not become ready within timeout"
    return 1
}

# Function to test module installation via Odoo CLI
test_module_installation() {
    log "Starting module installation test..."
    
    # Wait for PostgreSQL
    log "Waiting for PostgreSQL..."
    until pg_isready -h ${HOST:-postgres} -p ${DB_PORT:-5432} -U ${USER:-odoo}; do
        log "PostgreSQL is not ready - sleeping"
        sleep 2
    done
    
    # Try to install the module
    log "Installing WhatsApp Business module..."
    
    local install_output
    install_output=$(odoo \
        --config=/etc/odoo/odoo.conf \
        --database="$TEST_DB" \
        --init=whatsapp_business \
        --stop-after-init \
        --log-level=info \
        --no-http 2>&1) || {
        log "ERROR: Module installation failed"
        log "Installation output:"
        echo "$install_output" | tee -a "$LOG_FILE"
        return 1
    }
    
    log "Module installation completed successfully"
    log "Installation output:"
    echo "$install_output" | tee -a "$LOG_FILE"
    
    return 0
}

# Function to test module upgrade
test_module_upgrade() {
    log "Testing module upgrade..."
    
    local upgrade_output
    upgrade_output=$(odoo \
        --config=/etc/odoo/odoo.conf \
        --database="$TEST_DB" \
        --update=whatsapp_business \
        --stop-after-init \
        --log-level=info \
        --no-http 2>&1) || {
        log "ERROR: Module upgrade failed"
        log "Upgrade output:"
        echo "$upgrade_output" | tee -a "$LOG_FILE"
        return 1
    }
    
    log "Module upgrade completed successfully"
    log "Upgrade output:"
    echo "$upgrade_output" | tee -a "$LOG_FILE"
    
    return 0
}

# Function to validate module structure
validate_module_structure() {
    log "Validating module structure..."
    
    local module_path="/mnt/extra-addons/whatsapp_business"
    local required_files=(
        "__manifest__.py"
        "__init__.py"
        "models/__init__.py"
        "views/menu.xml"
        "security/ir.model.access.csv"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$module_path/$file" ]]; then
            log "ERROR: Required file missing: $file"
            return 1
        fi
        log "✓ Found required file: $file"
    done
    
    log "Module structure validation passed"
    return 0
}

# Function to check for XML syntax errors
validate_xml_syntax() {
    log "Validating XML syntax..."
    
    local module_path="/mnt/extra-addons/whatsapp_business"
    local xml_files
    xml_files=$(find "$module_path" -name "*.xml" -type f)
    
    for xml_file in $xml_files; do
        if ! xmllint --noout "$xml_file" 2>/dev/null; then
            log "ERROR: XML syntax error in file: $xml_file"
            return 1
        fi
        log "✓ XML syntax valid: $(basename "$xml_file")"
    done
    
    log "XML syntax validation passed"
    return 0
}

# Function to check Python syntax
validate_python_syntax() {
    log "Validating Python syntax..."
    
    local module_path="/mnt/extra-addons/whatsapp_business"
    local python_files
    python_files=$(find "$module_path" -name "*.py" -type f)
    
    for py_file in $python_files; do
        if ! python3 -m py_compile "$py_file" 2>/dev/null; then
            log "ERROR: Python syntax error in file: $py_file"
            return 1
        fi
        log "✓ Python syntax valid: $(basename "$py_file")"
    done
    
    log "Python syntax validation passed"
    return 0
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    log "Starting comprehensive test suite..."
    
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Module structure validation
    log "=== Test 1: Module Structure Validation ==="
    if validate_module_structure; then
        log "✅ PASS: Module structure validation"
        tests_passed=$((tests_passed + 1))
    else
        log "❌ FAIL: Module structure validation"
        tests_failed=$((tests_failed + 1))
    fi
    
    # Test 2: XML syntax validation
    log "=== Test 2: XML Syntax Validation ==="
    if validate_xml_syntax; then
        log "✅ PASS: XML syntax validation"
        tests_passed=$((tests_passed + 1))
    else
        log "❌ FAIL: XML syntax validation"
        tests_failed=$((tests_failed + 1))
    fi
    
    # Test 3: Python syntax validation
    log "=== Test 3: Python Syntax Validation ==="
    if validate_python_syntax; then
        log "✅ PASS: Python syntax validation"
        tests_passed=$((tests_passed + 1))
    else
        log "❌ FAIL: Python syntax validation"
        tests_failed=$((tests_failed + 1))
    fi
    
    # Test 4: Module installation
    log "=== Test 4: Module Installation ==="
    if test_module_installation; then
        log "✅ PASS: Module installation"
        tests_passed=$((tests_passed + 1))
    else
        log "❌ FAIL: Module installation"
        tests_failed=$((tests_failed + 1))
        # If installation fails, skip upgrade test
        log "Skipping upgrade test due to installation failure"
        return 1
    fi
    
    # Test 5: Module upgrade
    log "=== Test 5: Module Upgrade ==="
    if test_module_upgrade; then
        log "✅ PASS: Module upgrade"
        tests_passed=$((tests_passed + 1))
    else
        log "❌ FAIL: Module upgrade"
        tests_failed=$((tests_failed + 1))
    fi
    
    # Test summary
    log "========================================"
    log "TEST SUMMARY"
    log "========================================"
    log "Tests passed: $tests_passed"
    log "Tests failed: $tests_failed"
    log "Total tests: $((tests_passed + tests_failed))"
    
    if [ $tests_failed -eq 0 ]; then
        log "🎉 ALL TESTS PASSED!"
        echo "SUCCESS" > "$RESULTS_DIR/test-status.txt"
        return 0
    else
        log "💥 SOME TESTS FAILED!"
        echo "FAILED" > "$RESULTS_DIR/test-status.txt"
        return 1
    fi
}

# Main execution
main() {
    log "Starting WhatsApp Business module test suite..."
    
    # Install required tools if not present
    if ! command -v xmllint &> /dev/null; then
        log "Installing xmllint..."
        apt-get update && apt-get install -y libxml2-utils
    fi
    
    # Run comprehensive tests
    if run_comprehensive_tests; then
        log "🎉 Test suite completed successfully!"
        exit 0
    else
        log "💥 Test suite failed!"
        exit 1
    fi
}

# Execute main function
main "$@"