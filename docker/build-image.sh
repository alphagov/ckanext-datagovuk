#!/bin/bash

set -eux

build () {
  if [ "${ARCH}" = "amd64" ]; then
    docker build . -t "ghcr.io/alphagov/${APP}:${1}" -f "docker/${APP}/${2}.Dockerfile"
  else
    docker buildx build --platform "linux/${ARCH}" . -t "ghcr.io/alphagov/${APP}:${1}" -f "docker/${APP}/${2}.Dockerfile"
  fi
}

if [[ ${BUILD_BASE:-} = "true" ]]; then
  if [ "${APP}" = "ckan" ]; then
    build "${VERSION}-core" "${VERSION}-core"
    build "${VERSION}-base" "${VERSION}-base"
  else
    DOCKER_TAG="${VERSION}"
  fi
else
  if [[ -n ${GH_REF:-} ]]; then  
    DOCKER_TAG="${GH_REF}"
  else
    DOCKER_TAG="${GITHUB_SHA}"
  fi
fi

if [[ -n ${DOCKER_TAG:-} ]]; then
  build "${DOCKER_TAG}" "${VERSION}"
fi

if [[ -n ${DRY_RUN:-} ]]; then
  echo "Dry run; not pushing to registry"
else
  if [[ -n ${DOCKER_TAG:-} ]]; then
    docker push "ghcr.io/alphagov/${APP}:${DOCKER_TAG}"
  else
    docker push "ghcr.io/alphagov/${APP}:${VERSION}-core"
    docker push "ghcr.io/alphagov/${APP}:${VERSION}-base"
  fi
fi
