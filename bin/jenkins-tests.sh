#!/usr/bin/env sh
venv/bin/pip install -r venv/src/ckan/dev-requirements.txt
dropdb ckan_test; createdb ckan_test
venv/bin/python setup.py develop
paster --plugin=ckan db init -c test-jenkins.ini
nosetests -v --nologcapture --with-pylons=test-jenkins.ini --with-coverage --cover-package=ckanext.datagovuk --cover-inclusive --cover-erase --cover-tests --ckan ckanext.datagovuk
