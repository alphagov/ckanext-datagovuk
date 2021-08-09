#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='alphagov'
ckan_harvest_sha='6ac2103d5420ecad7eb7cd8a32cdb96a95c7d821'

ckan_dcat_sha='6b7ec505f303fb18e0eebcebf67130d36b3dca82'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='7636ed76a168f59ab8ad1e02b435e2ed1fd5732c'

# ckan 2.9.3
ckan_sha='65a035890428ae581648696871a3021b7ca0f2f4'

pycsw_tag='2.4.0'

pipopt='--exists-action=b'

$pip install $pipopt -U numpy==1.16.4

$pip uninstall $pipopt -y enum34

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/alphagov/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install $pipopt -r https://raw.githubusercontent.com/alphagov/ckan/$ckan_sha/requirements.txt
$pip install $pipopt -Ue "git+https://github.com/alphagov/ckan.git@$ckan_sha#egg=ckan"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install $pipopt -U "git+https://github.com/ckan/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install $pipopt -r requirements.txt

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw.git/$pycsw_tag/requirements.txt)
$pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_tag#egg=pycsw"

pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")"
(cd $pycsw_src && /usr/bin/env python setup.py build)
$pip install $pipopt -e .
