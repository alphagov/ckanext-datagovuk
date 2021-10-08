#! /bin/bash

pip=${1-'/usr/bin/env pip'}

ckan_harvest_fork='alphagov'
ckan_harvest_sha='d34667413128d6c24168663dea773d1b1c0439da'

ckan_dcat_fork='alphagov'
ckan_dcat_sha='be3b809fa7431c8d81508c01853e81ce6a5dfd84'

ckan_spatial_fork='alphagov'
ckan_spatial_sha='3f423de1e9e4e6975725712626d904887779b408'

# ckan 2.9.3 - with dgu fixes
ckan_sha='bc7ed57aba16f755adb39a9b38d04d543a4f4be1'
ckan_fork='alphagov'

pycsw_tag='2.4.0'

pipopt='--exists-action=b --force-reinstall'

$pip install $pipopt -U numpy==1.16.4 wheel==0.37.0

$pip uninstall -y enum34

# needed for harvester run-test to target harvest sources
$pip install $pipopt -U factory-boy==2.12.0 mock==2.0.0 pytest==4.6.5

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt)
$pip install $pipopt -r https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt
$pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat"

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw.git/$pycsw_tag/requirements.txt)
$pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_tag#egg=pycsw"

pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")"
(cd $pycsw_src && /usr/bin/env python setup.py build)
$pip install $pipopt -e .

$pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt)
$pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

$pip install $pipopt -r requirements.txt