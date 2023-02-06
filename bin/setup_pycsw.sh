#!/usr/bin/env sh

echo "===== Running PYCSW setup ====="

# Wait for PostgreSQL
while ! pg_isready -h $CKAN_DB_HOST -U ckan; do
  sleep 1;
done

ckan ckan-pycsw setup -p $CKAN_CONFIG/pycsw.cfg

echo "Update pycsw abstract index to allow for larger records"
PGPASSWORD=ckan psql pycsw -h $CKAN_DB_HOST -U ckan -c "DROP INDEX ix_records_abstract;CREATE INDEX ix_records_abstract ON records((md5(abstract)));"
