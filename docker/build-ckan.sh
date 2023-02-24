#!/bin/bash

set -eux

docker build . -t ghcr.io/alphagov/ckan:2.9.7 -f Dockerfile

if [[ -n ${DRY_RUN:-} ]]; then
  echo "Dry run; not pushing to registry"
else
  docker push ghcr.io/alphagov/ckan:2.9.7
fi
