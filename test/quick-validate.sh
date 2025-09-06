#!/bin/bash

# Quick validation script for the WhatsApp Business Odoo module
# This script performs basic checks without external dependencies

set -e

echo "========================================"
echo "WhatsApp Business Module Quick Validation"
echo "========================================"

# Check module structure
echo "Checking module structure..."

required_files=(
    "odoo_module/__manifest__.py"
    "odoo_module/__init__.py"
    "odoo_module/models/__init__.py"
    "odoo_module/views/menu.xml"
    "odoo_module/security/ir.model.access.csv"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        missing_files=$((missing_files + 1))
    else
        echo "✅ Found: $file"
    fi
done

# Check Python syntax
echo ""
echo "Checking Python syntax..."
python_errors=0

for py_file in $(find odoo_module -name "*.py" -type f); do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        echo "✅ $py_file"
    else
        echo "❌ Syntax error in: $py_file"
        python_errors=$((python_errors + 1))
    fi
done

# Check __manifest__.py
echo ""
echo "Validating __manifest__.py..."
if python3 -c "
import ast
try:
    with open('odoo_module/__manifest__.py', 'r') as f:
        content = f.read()
    manifest = ast.literal_eval(content)
    required_keys = ['name', 'version', 'depends', 'data']
    missing_keys = [key for key in required_keys if key not in manifest]
    if missing_keys:
        print(f'Missing manifest keys: {missing_keys}')
        sys.exit(1)
    else:
        print('✅ Manifest structure is valid')
        print(f'   Name: {manifest.get(\"name\", \"N/A\")}')
        print(f'   Version: {manifest.get(\"version\", \"N/A\")}')
        print(f'   Dependencies: {manifest.get(\"depends\", [])}')
except Exception as e:
    print(f'❌ Manifest validation failed: {e}')
    sys.exit(1)
"; then
    manifest_valid=true
else
    manifest_valid=false
fi

# Summary
echo ""
echo "========================================"
echo "VALIDATION SUMMARY"
echo "========================================"
echo "Missing files: $missing_files"
echo "Python syntax errors: $python_errors"
echo "Manifest valid: $manifest_valid"

total_errors=$((missing_files + python_errors))
if [ "$manifest_valid" = false ]; then
    total_errors=$((total_errors + 1))
fi

if [ $total_errors -eq 0 ]; then
    echo "🎉 All basic validations passed!"
    exit 0
else
    echo "💥 Found $total_errors validation errors!"
    exit 1
fi