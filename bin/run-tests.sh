#!/usr/bin/env sh

pytest --ckan-ini=test.ini tests --cov=ckanext.datagovuk --cov-report=term-missing --disable-pytest-warnings -v
