#!/bin/bash

# Run Odoo Tests Script
# This script starts Odoo and waits for it to be ready for testing

set -e

echo "========================================"
echo "Starting Odoo Test Environment"
echo "========================================"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h ${HOST:-postgres} -p ${DB_PORT:-5432} -U ${USER:-odoo}; do
    echo "PostgreSQL is not ready - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

# Create log directory
mkdir -p /var/log/odoo

# Start Odoo with test configuration
echo "Starting Odoo server..."
exec odoo \
    --config=/etc/odoo/odoo.conf \
    --database=${POSTGRES_DB:-odoo_test} \
    --init=whatsapp_business \
    --test-enable \
    --test-tags=whatsapp_business \
    --stop-after-init \
    --log-level=info \
    --logfile=/var/log/odoo/odoo.log