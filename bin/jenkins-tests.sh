#!/usr/bin/env sh

set -ex

venv/bin/pip install -r venv/src/ckan/dev-requirements.txt
venv/bin/pip install -r dev-requirements.txt

DB_NAME="ckanext_dgu_$(date -u -Ins | tr -dc 0-9)"

createdb $DB_NAME

# echo "\n[app:main]\nsqlalchemy.url = postgresql:///$DB_NAME\nsolr_url = http://localhost:8983/solr/$DB_NAME\n" >> test-jenkins.ini

ckan config-tool test-jenkins.ini \
  "sqlalchemy.url = postgresql:///$DB_NAME" \
  "solr_url = http://localhost:8983/solr/$DB_NAME"

ckan config-tool test.ini \
  "sqlalchemy.url = postgresql:///$DB_NAME" \
  "solr_url = http://localhost:8983/solr/$DB_NAME"

curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=$DB_NAME&configSet=ckan28"

venv/bin/python setup.py develop

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

ckan -c test-jenkins.ini db init
ckan -c test-jenkins.ini harvester initdb

export TEST_CKAN_INI=test-jenkins.ini
bin/run-tests.sh

# deliberately only drop DBs if tests pass. otherwise leave DBs
# as it may help in diagnosing failure
dropdb $DB_NAME
curl "http://localhost:8983/solr/admin/cores?action=UNLOAD&core=$DB_NAME&deleteIndex=true&deleteDataDir=true&deleteInstanceDir=true"
