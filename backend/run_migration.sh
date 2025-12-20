#!/bin/bash
# Run database migrations for image pull sources

set -e

DB_FILE="${DATABASE_URL:-wildlife_camera.db}"
DB_FILE="${DB_FILE#sqlite:///./}"

echo "Running migration: 002_add_image_pull_sources.sql"
echo "Database: $DB_FILE"

if [ ! -f "$DB_FILE" ]; then
    echo "Warning: Database file $DB_FILE does not exist. It will be created."
fi

sqlite3 "$DB_FILE" < migrations/002_add_image_pull_sources.sql

echo "✓ Migration completed successfully"
echo ""
echo "To verify, you can run:"
echo "  sqlite3 $DB_FILE '.schema image_pull_sources'"
