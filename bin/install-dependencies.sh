#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='alphagov'
ckan_harvest_sha='283ac0498fd22056fb8572d49b25cd8492b7178f'

ckan_dcat_sha='6b7ec505f303fb18e0eebcebf67130d36b3dca82'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='d8dd6bd910f08c1f5408487cf2a455fc8ac0a91b'

# ckan 2.9.1
ckan_sha='bb272bfc7167b35cbff8ce48ed815dd4e23597ba'

pycsw_tag='2.4.0'

pipopt='--exists-action=b'

$pip install $pipopt -U numpy==1.16.4

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install $pipopt -U "git+https://github.com/ckan/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/ckan/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install $pipopt -r https://raw.githubusercontent.com/ckan/ckan/$ckan_sha/requirements.txt
$pip install $pipopt -Ue "git+https://github.com/ckan/ckan.git@$ckan_sha#egg=ckan"

$pip install $pipopt -r requirements.txt

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw.git/$pycsw_tag/requirements.txt)
$pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_tag#egg=pycsw"

pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")"
(cd $pycsw_src && /usr/bin/env python setup.py build)
$pip install $pipopt -e .
