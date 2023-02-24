#!/bin/bash

set -eux

docker build . -t ghcr.io/alphagov/${APP}:${VERSION} -f docker/${APP}/Dockerfile

if [[ -n ${DRY_RUN:-} ]]; then
  echo "Dry run; not pushing to registry"
else
  docker push ghcr.io/alphagov/${APP}:${VERSION}
fi
