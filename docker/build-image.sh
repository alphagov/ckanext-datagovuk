#!/bin/bash

set -eux

if [ ${BUILD_CI} ]; then
  if [ "${APP}" = "ckan" ]; then
    VERSION="${VERSION}-base"
  fi
  DOCKER_TAG="${VERSION}"
else
  DOCKER_TAG="${GITHUB_SHA}"
fi

if [ "${ARCH}" = "amd64" ]; then
  docker build . -t ghcr.io/alphagov/${APP}:${DOCKER_TAG} -f docker/${APP}/${VERSION}.Dockerfile
else
  docker buildx build --platform linux/${ARCH} . -t ghcr.io/alphagov/${APP}:${DOCKER_TAG} -f docker/${APP}/${VERSION}.Dockerfile
fi

if [[ -n ${DRY_RUN:-} ]]; then
  echo "Dry run; not pushing to registry"
else
  docker push ghcr.io/alphagov/${APP}:${DOCKER_TAG}
fi
