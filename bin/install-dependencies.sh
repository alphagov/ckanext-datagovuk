#! /bin/bash

venv/bin/pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckan/2.7/requirement-setuptools.txt)
venv/bin/pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-harvest/c21c1627992cbcf0043b7b6873ff899f6f66767f/pip-requirements.txt)
venv/bin/pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-dcat/master/requirements.txt)
venv/bin/pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-spatial/master/pip-requirements.txt)
venv/bin/pip install -U $(curl -s https://raw.githubusercontent.com/alphagov/ckanext-s3-resources/master/requirements.txt)
venv/bin/pip install -Ue 'git+https://github.com/ckan/ckan.git@ckan-2.7.4#egg=ckan'
venv/bin/pip install -r venv/src/ckan/requirements.txt
venv/bin/pip install -r requirements.txt
