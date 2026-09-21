#!/usr/bin/env sh

pytest --ckan-ini=test.ini ckanext/datagovuk/tests --cov=ckanext.datagovuk --cov-report=term-missing --disable-pytest-warnings -v