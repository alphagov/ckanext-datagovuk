#!/bin/bash

set -eux

if [ "${ARCH}" = "amd64" ]; then
  docker build . -t ghcr.io/alphagov/${APP}:${VERSION} -f docker/${APP}/Dockerfile
else
  docker buildx build --platform linux/${ARCH} . -t ghcr.io/alphagov/${APP}:${VERSION} -f docker/${APP}/Dockerfile
fi

if [[ -n ${DRY_RUN:-} ]]; then
  echo "Dry run; not pushing to registry"
else
  docker push ghcr.io/alphagov/${APP}:${VERSION}
fi
