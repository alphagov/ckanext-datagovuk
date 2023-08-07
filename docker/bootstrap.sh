#!/usr/bin/env bash

# Default git fork
CKAN_FORK=ckan
CKAN_SHA=70bec6611003b96ec7a02abb9605afdfb0964ad9
DCAT_FORK=ckan
DCAT_SHA=618928be5a211babafc45103a72b6aab4642e964
SPATIAL_FORK=ckan
SPATIAL_SHA=17d5a341cf8f40b35b25df91a18ce72c31195ba3
HARVEST_FORK=ckan
HARVEST_SHA=cb0a7034410f217b2274585cb61783582832c8d5
SRC_DIR=2.10

if [[ ! -z $1 && $1 == '2.9.3' ]]; then
    HARVEST_FORK=alphagov
    HARVEST_SHA=283ac0498fd22056fb8572d49b25cd8492b7178f
    SPATIAL_FORK=alphagov
    SPATIAL_SHA=d64fd925700990a352ef23ed180c47dbc7277138
    CKAN_SHA=885f9e0b668e3496a8f2c0c0a9f1cb59bf810e16
    CKAN_FORK=alphagov
    SRC_DIR=2.9.3
    DCAT_FORK=ckan
    DCAT_SHA=d64fd925700990a352ef23ed180c47dbc7277138
fi

echo -e "Please ensure that the ${SRC_DIR} docker/src directory is empty before running this command. This command will not populate the directories required for this project to run effectively unless said directories are already empty or don't exist.\n"

mkdir -p docker/src/$SRC_DIR
pushd docker/src/$SRC_DIR
(git clone https://github.com/$CKAN_FORK/ckan && cd ckan && git checkout $CKAN_SHA)

(git clone https://github.com/$HARVEST_FORK/ckanext-harvest && cd ckanext-harvest && git checkout $HARVEST_SHA)
(git clone https://github.com/$SPATIAL_FORK/ckanext-spatialk && cd ckanext-spatial && git checkout $SPATIAL_SHA)
(git clone https://github.com/$DCAT_FORK/ckanext-dcat && cd ckanext-dcat && git checkout $DCAT_SHA)
git clone https://github.com/geopython/pycsw.git --branch 2.4.0 

git clone https://github.com/alphagov/ckan-mock-harvest-sources.git
# appending this should quietly override any prior settings of the variable
echo $'\nmap $host $mock_absolute_root_url { default "http://static-mock-harvest-source:11088/"; }' >> ckan-mock-harvest-sources/static/vars.conf

if [[ (! -z $2 && $2 == 'full') || (! -z $1 && $1 == 'full') ]]; then
    git clone https://github.com/alphagov/datagovuk_publish.git
    git clone https://github.com/alphagov/datagovuk_find.git
fi
popd
