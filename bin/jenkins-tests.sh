#!/usr/bin/env sh
venv/bin/pip install -r venv/src/ckan/dev-requirements.txt
dropdb ckan_test; createdb ckan_test
venv/bin/python setup.py develop
nosetests --nologcapture --with-pylons=test-jenkins.ini --with-coverage --cover-package=ckanext.datagovuk --cover-inclusive --cover-erase --cover-tests
