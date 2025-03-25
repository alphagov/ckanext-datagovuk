# Dockerfile and initdb-postgis.sh taken from https://github.com/postgis/docker-postgis/blob/master/13-3.5/Dockerfile in order to build arm64 image
FROM postgres:13-bullseye

LABEL maintainer="PostGIS Project - https://postgis.net" \
      org.opencontainers.image.description="PostGIS 3.5.2+dfsg-1.pgdg110+1 spatial database extension with PostgreSQL 13 bullseye" \
      org.opencontainers.image.source="https://github.com/postgis/docker-postgis"

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.5.2+dfsg-1.pgdg110+1

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           # ca-certificates: for accessing remote raster files;
           #   fix: https://github.com/postgis/docker-postgis/issues/307
           ca-certificates \
           \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d
COPY docker/postgis-base/initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh

ENTRYPOINT ["/docker-entrypoint-initdb.d/10_postgis.sh"]
