#!/usr/bin/env sh
nosetests -v --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.datagovuk --cover-inclusive --cover-erase --cover-tests --ckan ckanext.datagovuk
