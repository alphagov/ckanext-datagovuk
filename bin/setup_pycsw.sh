#!/usr/bin/env sh

echo "===== Running PYCSW setup ====="

# Wait for PostgreSQL
while ! pg_isready -h $CKAN_DB_HOST -U ckan; do
  sleep 1;
done

# only run the setup script if the records table has not been created
if !(psql $CKAN_SQLALCHEMY_URL -c "select exists (SELECT * FROM information_schema.tables where table_name = 'records');" | tr -d '\n' | grep -q "exists -------- t"); then 
  ckan ckan-pycsw setup -p $CKAN_CONFIG/pycsw.cfg

  echo "Drop ix_records_abstract if exists and create pycsw abstract index to allow for larger records"
  psql $CKAN_SQLALCHEMY_URL -c "DROP INDEX IF EXISTS ix_records_abstract;CREATE INDEX ix_records_abstract ON records((md5(abstract)));"
fi
