#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='alphagov'
ckan_harvest_sha='5671bdf93269c9b80369a0b40a166bce76ea40ee'

ckan_dcat_fork='alphagov'
ckan_dcat_sha='6253f296c6d1200465a3223710d076cd24e37834'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='7bdc8c5ff63c91cd7996cd461505bcba9c39a34d'

ckan_s3_resources_fork='alphagov'
ckan_s3_resources_sha='81eb36fb51da5e216e9405a7ad64c4096881ca85'

ckan_fork='ckan'
ckan_sha='ckan-2.7.4'

$pip install -U pip

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_s3_resources_fork/ckanext-s3-resources/$ckan_s3_resources_sha/requirements.txt)
$pip install -U "git+https://github.com/$ckan_s3_resources_fork/ckanext-s3-resources@$ckan_s3_resources_sha#egg=ckanext-s3-resources"

$pip install -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install -r https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt
$pip install -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan"

$pip install -r requirements.txt
