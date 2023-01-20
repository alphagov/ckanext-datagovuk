#!/usr/bin/env bash
VERSION=2.9.7

if [[ ! -z $1 && $1 == '2.9.3' ]]; then
    VERSION=2.9.3
fi

if [[ (! -z $2 && $2 == 'full') || (! -z $1 && $1 == 'full') ]]; then
    echo "=== Full DGU stack"
    FULL_ARGS="-f docker/docker-compose-$VERSION-full.yml"
else
    echo "=== CKAN stack"
fi

docker-compose -f docker/docker-compose-$VERSION.yml $FULL_ARGS up
