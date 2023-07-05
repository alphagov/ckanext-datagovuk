#!/usr/bin/env sh

echo "===== Running CKAN setup ====="

# Wait for PostgreSQL
while ! pg_isready -h $CKAN_DB_HOST -U ckan; do
  sleep 1;
done

ckan db init

if [ ! -z $CREATE_CKAN_ADMIN ]; then
    if (ckan user show ckan_admin | grep -q "User: None"); then
        echo "===== adding sysadmin user ====="
        ckan user add $CKAN_SYSADMIN_NAME email=$CKAN_SYSADMIN_EMAIL password=$CKAN_SYSADMIN_PASSWORD
        ckan sysadmin add $CKAN_SYSADMIN_NAME
    else
        echo "===== $CKAN_SYSADMIN_NAME already exists ====="
    fi
fi

if [ ! -z $SETUP_DGU_TEST_DATA ]; then
    echo "===== removing old DGU test data ====="
    ckan datagovuk remove-dgu-test-data

    echo "===== creating DGU test data ====="
    ckan datagovuk create-dgu-test-data
fi

ckan config-tool "$CKAN_INI" "ckan.i18n_directory=$CKAN_VENV/src/ckanext-datagovuk/ckanext/datagovuk"

exec "$@"
