#!/usr/bin/env sh

echo "===== Running CKAN setup ====="

# Wait for PostgreSQL
while ! pg_isready -h $CKAN_DB_HOST -U ckan; do
  echo "Waiting 1 second for postgres to be ready"
  sleep 1;
done
echo "Postgres is ready"

if [ ${CKAN_DB_INIT:-} = "true" ]; then
    ckan db init
fi

ckan db upgrade

if [ ! -z $CREATE_CKAN_ADMIN ]; then
    if (ckan user show ckan_admin | grep -q "User: None"); then
        echo "===== adding sysadmin user ====="
        ckan user add $CKAN_SYSADMIN_NAME email=$CKAN_SYSADMIN_EMAIL password=$CKAN_SYSADMIN_PASSWORD
        ckan sysadmin add $CKAN_SYSADMIN_NAME
    else
        echo "===== $CKAN_SYSADMIN_NAME already exists ====="
    fi
fi

while [ $(curl -s -o /dev/null -I -w '%{http_code}' "$CKAN_SOLR_URL/admin/ping") != "200" ]; do
  echo "Waiting 1 second for Solr to be ready"
  sleep 1;
done
echo "Solr ready"

if [ ! -z $SETUP_DGU_TEST_DATA ]; then
    echo "===== removing old DGU test data ====="
    ckan datagovuk remove-dgu-test-data

    echo "===== creating DGU test data ====="
    ckan datagovuk create-dgu-test-data
fi

exec "$@"
