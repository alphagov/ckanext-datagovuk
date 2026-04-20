#!/usr/bin/env bash

# Default git fork
CKAN_FORK=alphagov
CKAN_SHA=dc5a8a6e4ab290f619fc52c5a3880376d7b3883c
CKAN_REPO=ckan-fix
DCAT_FORK=ckan
DCAT_SHA=618928be5a211babafc45103a72b6aab4642e964

SPATIAL_FORK=alphagov
SPATIAL_SHA=c4938431346b50209d7bcf89a1a0154698b9f9f2
HARVEST_FORK=ckan
HARVEST_SHA=9fb44f79809a1c04dfeb0e1ca2540c5ff3cacef4
FIND_SHA=v3.8.0


if [[ ! -f "docker/.env" ]]; then
    cp "docker/.env.example" "docker/.env"
    echo "Created docker/.env from .env.example - if needed update it with your settings"
fi

# Check for contents in src dir
if [[ -d "docker/src" ]]; then
    echo "docker/src already exists"
    read -p "Remove and re-clone dependencies? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
    rm -rf "docker/src"
fi

mkdir -p docker/src
pushd docker/src
(git clone https://github.com/$CKAN_FORK/$CKAN_REPO && cd $CKAN_REPO && git checkout $CKAN_SHA)

(git clone https://github.com/$HARVEST_FORK/ckanext-harvest && cd ckanext-harvest && git checkout $HARVEST_SHA)
(git clone https://github.com/$SPATIAL_FORK/ckanext-spatial && cd ckanext-spatial && git checkout $SPATIAL_SHA)
(git clone https://github.com/$DCAT_FORK/ckanext-dcat && cd ckanext-dcat && git checkout $DCAT_SHA)
git clone https://github.com/geopython/pycsw.git --branch 2.4.0 

git clone https://github.com/alphagov/ckan-mock-harvest-sources.git
# appending this should quietly override any prior settings of the variable
echo $'\nmap $host $mock_absolute_root_url { default "http://static-mock-harvest-source:11088/"; }' >> ckan-mock-harvest-sources/static/vars.conf

git clone https://github.com/alphagov/datagovuk_find.git --branch $FIND_SHA --single-branch
popd
