# Odoo Module Testing Guide

This directory contains a comprehensive Docker-based testing infrastructure for the WhatsApp Business Odoo module. The testing system ensures the module can be properly installed, upgraded, and functions correctly in a clean Odoo environment.

## 🏗️ Testing Architecture

### Components

1. **Docker Test Environment** (`Dockerfile.test`)
   - Based on official Odoo 17.0 image
   - Includes all necessary dependencies
   - Pre-configured for module testing

2. **Docker Compose Setup** (`docker-compose.test.yml`)
   - PostgreSQL database for testing
   - Odoo test instance
   - Automated test runner

3. **Test Scripts** (`scripts/`)
   - Module installation validation
   - Upgrade testing
   - Syntax and structure checks

4. **CI/CD Pipeline** (`.github/workflows/odoo-ci.yml`)
   - Automated testing on push/PR
   - Multiple test environments
   - Security scanning

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Basic familiarity with Odoo modules

### Running Tests Locally

```bash
# Run all tests
./test/run-tests.sh

# Run specific test type
./test/run-tests.sh -t syntax    # Syntax checks only
./test/run-tests.sh -t install   # Installation test only

# Clean environment and run tests
./test/run-tests.sh -c

# Verbose output
./test/run-tests.sh -v
```

### Using Docker Compose

```bash
# Run full test suite
docker-compose -f docker-compose.test.yml up --build

# Check test results
cat test/results/test-status.txt
cat test/results/installation-test.log
```

## 📋 Test Coverage

### 1. Syntax and Structure Validation

- ✅ Python syntax validation
- ✅ XML syntax validation  
- ✅ Module structure verification
- ✅ Required files presence check

### 2. Module Installation Testing

- ✅ Fresh installation from scratch
- ✅ Database initialization
- ✅ Module dependency resolution
- ✅ Data loading validation

### 3. Module Upgrade Testing

- ✅ Upgrade from previous version
- ✅ Data migration validation
- ✅ View updates verification

### 4. Integration Testing

- ✅ Core functionality validation
- ✅ API endpoint testing
- ✅ Database schema validation

### 5. Security Scanning

- ✅ Vulnerability scanning with Trivy
- ✅ Dependency security check
- ✅ Code security analysis

## 🔧 Configuration Files

### `test/odoo.conf`

Test-specific Odoo configuration:

```ini
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
test_enable = True
init = whatsapp_business
```

### `Dockerfile.test`

Test environment setup:

- Odoo 17.0 base image
- Python dependencies (requests, python-dotenv)
- Module installation and permissions
- Health checks

### `docker-compose.test.yml`

Complete test stack:

- PostgreSQL 15 database
- Odoo test instance
- Test runner service
- Volume mounts for results

## 📊 Test Results

### Location

Test results are stored in:

- `test/results/` - Test output files
- `test/logs/` - Odoo and application logs
- `test/filestore/` - Odoo filestore data

### Files

- `test-status.txt` - Overall test status (SUCCESS/FAILED)
- `installation-test.log` - Detailed test execution log
- `odoo.log` - Odoo server logs

### Reading Results

```bash
# Check overall status
cat test/results/test-status.txt

# View detailed test log
cat test/results/installation-test.log

# Check Odoo logs
tail -f test/logs/odoo.log
```

## 🔄 CI/CD Pipeline

### Workflow Triggers

- Push to `main`, `develop`, or `copilot/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Job Sequence

1. **Lint and Syntax** - Code quality checks
2. **Module Test** - Installation and upgrade tests
3. **Integration Test** - Full Docker Compose test
4. **Security Scan** - Vulnerability assessment
5. **Test Summary** - Overall results

### Artifacts

- Test results and logs uploaded as GitHub artifacts
- Security scan results in GitHub Security tab
- Test summary in job output

## 🐛 Troubleshooting

### Common Issues

#### Module Installation Fails

```bash
# Check detailed logs
cat test/results/installation-test.log

# Look for specific errors
grep -i error test/logs/odoo.log
```

#### Docker Build Issues

```bash
# Rebuild without cache
./test/run-tests.sh --no-cache

# Check Docker logs
docker logs <container_name>
```

#### Permission Issues

```bash
# Fix test directory permissions
chmod 755 test/{logs,results,filestore}

# Make scripts executable
chmod +x test/scripts/*.sh
```

### Debug Mode

Run tests in verbose mode for detailed output:

```bash
./test/run-tests.sh -v
```

## 📝 Adding New Tests

### Structure

```
test/
├── scripts/
│   ├── install-module-test.sh    # Main test script
│   ├── run-tests.sh               # Odoo startup script
│   └── your-new-test.sh           # Add custom tests here
├── data/
│   └── test-data.xml              # Test data for validation
└── config/
    └── test-specific.conf         # Custom test configurations
```

### Test Script Template

```bash
#!/bin/bash

test_your_feature() {
    log "Testing your feature..."
    
    # Your test logic here
    if your_test_condition; then
        log "✅ PASS: Your feature test"
        return 0
    else
        log "❌ FAIL: Your feature test"
        return 1
    fi
}
```

## 🔒 Security Considerations

### Database Security

- Test database is isolated and temporary
- No production data is used
- Database is destroyed after tests

### Container Security

- Non-root user execution
- Minimal attack surface
- Regular base image updates

### Secrets Management

- No secrets in test environment
- Mock configurations for APIs
- Secure credential handling in CI/CD

## 📈 Performance Testing

### Resource Limits

The test environment is configured with:

- Memory: 2GB limit
- CPU: No specific limits (uses available)
- Disk: Temporary volumes only

### Timing Expectations

- Syntax checks: < 30 seconds
- Module installation: 2-5 minutes
- Full test suite: 5-10 minutes

## 🤝 Contributing

### Before Committing

1. Run local tests:
   ```bash
   ./test/run-tests.sh
   ```

2. Ensure all tests pass:
   ```bash
   echo $?  # Should be 0
   ```

3. Check test artifacts:
   ```bash
   ls test/results/
   ```

### Adding Test Cases

1. Create test script in `test/scripts/`
2. Update `install-module-test.sh` to call your test
3. Test locally before committing
4. Update this documentation

## 📞 Support

For issues with the testing infrastructure:

1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Create an issue with:
   - Test output logs
   - Environment details
   - Steps to reproduce

---

This testing infrastructure ensures the WhatsApp Business module maintains high quality and reliability across all deployments. 🚀