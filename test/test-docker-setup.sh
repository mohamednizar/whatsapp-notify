#!/bin/bash

# Quick Docker setup test
# This script tests that our Docker configuration can start containers properly

set -e

echo "========================================"
echo "Testing Docker Setup"
echo "========================================"

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker stop postgres-test 2>/dev/null || true
docker rm postgres-test 2>/dev/null || true
docker network rm odoo-test-network 2>/dev/null || true

# Create network
echo "Creating Docker network..."
docker network create odoo-test-network

# Start PostgreSQL
echo "Starting PostgreSQL container..."
docker run -d \
  --name postgres-test \
  --network odoo-test-network \
  --network-alias postgres \
  -e POSTGRES_DB=odoo_test \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo \
  -e LC_ALL=C.UTF-8 \
  -e LANG=C.UTF-8 \
  postgres:15

# Test PostgreSQL startup
echo "Testing PostgreSQL startup..."
timeout=30
count=0
while [ $count -lt $timeout ]; do
  if docker exec postgres-test pg_isready -U odoo -d odoo_test -h localhost; then
    echo "✅ PostgreSQL is ready!"
    break
  fi
  echo "PostgreSQL not ready yet... waiting (attempt $((count+1))/$timeout)"
  sleep 2
  count=$((count+1))
done

if [ $count -eq $timeout ]; then
  echo "❌ PostgreSQL failed to start within timeout"
  docker logs postgres-test
  exit 1
fi

# Test database connection
echo "Testing database connection..."
if docker exec postgres-test psql -U odoo -d odoo_test -c "SELECT 1;" > /dev/null 2>&1; then
  echo "✅ Database connection successful"
else
  echo "❌ Database connection failed"
  exit 1
fi

# Test network connectivity by trying to connect from a test container
echo "Testing network connectivity with PostgreSQL client..."
docker run --rm --network odoo-test-network postgres:15 sh -c "
  echo 'Testing pg_isready to postgres host...'
  if pg_isready -h postgres -p 5432 -U odoo; then
    echo '✅ Network connectivity to postgres:5432 successful'
  else
    echo '❌ Network connectivity to postgres:5432 failed'
    exit 1
  fi
"

echo "✅ All Docker setup tests passed!"

# Clean up
echo "Cleaning up..."
docker stop postgres-test
docker rm postgres-test
docker network rm odoo-test-network

echo "🎉 Docker setup test completed successfully!"