#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Usage: $0 path.to.my.test.module [OptionalTestClass.and_or_function]"
  exit
elif [ -z "$2" ]; then
  test_name="$1"
else
  test_name="$1:$2"
fi

target_name=$(sed -r 's/tests?[._]//g' <<< $1)

nosetests -v --with-pylons=test.ini --debug=$target_name $test_name
