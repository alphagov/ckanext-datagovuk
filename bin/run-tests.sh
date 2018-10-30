#!/usr/bin/env sh

if [ -z "$1" ]; then
  test_name="ckanext.datagovuk"
  coverage=" --with-coverage --cover-package=ckanext.datagovuk --cover-inclusive --cover-erase --cover-tests"
else
  test_name=$1
  coverage=""
fi

nosetests -v --nologcapture --with-pylons=${TEST_CKAN_INI:-test.ini} --with-randomly --ckan $coverage $test_name
