#!/usr/bin/env sh

echo "===== Running CKAN setup ====="

# Wait for PostgreSQL
while ! pg_isready -h $CKAN_DB_HOST -U ckan; do
  sleep 1;
done

ckan db init

exec "$@"
