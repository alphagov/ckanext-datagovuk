#!/usr/bin/env bash

# Default git fork
CKAN_FORK=ckan
CKAN_SHA=9f2094b26721b28918d45d58fea16176df7a1ce1
DCAT_FORK=ckan
DCAT_SHA=618928be5a211babafc45103a72b6aab4642e964

SPATIAL_FORK=alphagov
SPATIAL_SHA=c4938431346b50209d7bcf89a1a0154698b9f9f2
HARVEST_FORK=ckan
HARVEST_SHA=9fb44f79809a1c04dfeb0e1ca2540c5ff3cacef4
SRC_DIR=2.10
FIND_SHA=v3.2.6

echo -e "Please ensure that the ${SRC_DIR} docker/src directory is empty before running this command. This command will not populate the directories required for this project to run effectively unless said directories are already empty or don't exist.\n"

mkdir -p docker/src/$SRC_DIR
pushd docker/src/$SRC_DIR
(git clone https://github.com/$CKAN_FORK/ckan && cd ckan && git checkout $CKAN_SHA)

(git clone https://github.com/$HARVEST_FORK/ckanext-harvest && cd ckanext-harvest && git checkout $HARVEST_SHA)
(git clone https://github.com/$SPATIAL_FORK/ckanext-spatial && cd ckanext-spatial && git checkout $SPATIAL_SHA)
(git clone https://github.com/$DCAT_FORK/ckanext-dcat && cd ckanext-dcat && git checkout $DCAT_SHA)
git clone https://github.com/geopython/pycsw.git --branch 2.4.0 

git clone https://github.com/alphagov/ckan-mock-harvest-sources.git
# appending this should quietly override any prior settings of the variable
echo $'\nmap $host $mock_absolute_root_url { default "http://static-mock-harvest-source:11088/"; }' >> ckan-mock-harvest-sources/static/vars.conf

git clone https://github.com/alphagov/datagovuk_find.git --branch $FIND_SHA --single-branch
popd
