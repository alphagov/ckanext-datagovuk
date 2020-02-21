#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='ckan'
ckan_harvest_sha='7b251f0e3b26e9567025b833228676b8801979d0'

ckan_dcat_fork='ckan'
ckan_dcat_sha='8c55890e7bf9644460ae71470f37abbd9295c9fa'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='c35e1249cfb3c7b2f1286f433fd51c6fe8f05b72'

ckan_s3_resources_fork='alphagov'
ckan_s3_resources_sha='81eb36fb51da5e216e9405a7ad64c4096881ca85'

ckan_fork='ckan'
ckan_sha='ckan-2.7.4'

pycsw_tag='2.4.0'

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

$pip install -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw.git/$pycsw_tag/requirements.txt)
$pip install -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_tag#egg=pycsw"

pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")"
(cd $pycsw_src && /usr/bin/env python setup.py build)
$pip install -e .
