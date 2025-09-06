# Testing Infrastructure Documentation

## Overview

This repository includes comprehensive Docker-based testing infrastructure to ensure the WhatsApp Business Odoo module is properly validated before deployment.

## Quick Validation

For fast local validation:

```bash
# Run basic syntax and structure checks
./test/quick-validate.sh
```

## Full Testing Suite

### Prerequisites

- Docker and Docker Compose
- Python 3.x

### Local Testing

```bash
# Run all tests (recommended before committing)
./test/run-tests.sh

# Run specific test types
./test/run-tests.sh -t syntax    # Syntax checks only
./test/run-tests.sh -t install   # Installation tests only

# Clean environment and run tests  
./test/run-tests.sh -c

# Verbose output for debugging
./test/run-tests.sh -v
```

### Using Docker Compose Directly

```bash
# Run full test suite in Docker
docker-compose -f docker-compose.test.yml up --build

# Check results
cat test/results/test-status.txt
```

## Automated CI/CD

The GitHub Actions workflow automatically runs:

1. **Syntax validation** - Python and XML syntax checks
2. **Module installation tests** - Fresh Odoo installation with the module
3. **Upgrade tests** - Module upgrade validation
4. **Integration tests** - Full Docker Compose test suite
5. **Security scanning** - Vulnerability assessment

### Triggering CI/CD

Tests run automatically on:
- Push to `main`, `develop`, or `copilot/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

## Test Results

Results are available in:
- `test/results/test-status.txt` - Overall status (SUCCESS/FAILED)
- `test/results/installation-test.log` - Detailed test output
- `test/logs/odoo.log` - Odoo server logs

## Troubleshooting

### Common Issues

1. **Docker Permission Issues**
   ```bash
   sudo chmod 755 test/{logs,results,filestore}
   ```

2. **Module Installation Failures**
   ```bash
   # Check detailed logs
   cat test/results/installation-test.log
   ```

3. **Build Cache Issues**
   ```bash
   ./test/run-tests.sh --no-cache
   ```

## Adding New Tests

1. Create test script in `test/scripts/`
2. Update `test/scripts/install-module-test.sh` to include your test
3. Test locally: `./test/run-tests.sh`
4. Commit and push

## Security

- Test environment is isolated and temporary
- No production data or secrets used
- Containers run with minimal privileges

For detailed testing documentation, see `test/README.md`.

---

This infrastructure ensures code quality and prevents deployment of broken modules. Always run tests before committing changes! 🚀