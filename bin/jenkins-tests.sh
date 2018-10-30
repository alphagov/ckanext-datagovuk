#!/usr/bin/env sh
venv/bin/pip install -r venv/src/ckan/dev-requirements.txt
venv/bin/pip install -r dev-requirements.txt
dropdb ckan_test; createdb ckan_test
venv/bin/python setup.py develop
paster --plugin=ckan db init -c test-jenkins.ini

export TEST_CKAN_INI=test-jenkins.ini
bin/run-tests.sh
