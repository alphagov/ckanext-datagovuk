#! /bin/bash

pip=${1-'/usr/bin/env pip'}

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-harvest/c21c1627992cbcf0043b7b6873ff899f6f66767f/pip-requirements.txt)
$pip install -U 'git+https://github.com/ckan/ckanext-harvest.git@c21c1627992cbcf0043b7b6873ff899f6f66767f#egg=ckanext-harvest'

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-dcat/v0.0.8/requirements.txt)
$pip install -U 'git+https://github.com/ckan/ckanext-dcat.git@v0.0.8#egg=ckanext-dcat'

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckanext-spatial/2acf66b110ba534750cab754a50566505ba88d83/pip-requirements.txt)
$pip install -U 'git+https://github.com/ckan/ckanext-spatial.git@2acf66b110ba534750cab754a50566505ba88d83#egg=ckanext-spatial'

$pip install -U $(curl -s https://raw.githubusercontent.com/alphagov/ckanext-s3-resources/50341b3960a6be3aba5a1558e80dd9a8c7c70c2c/requirements.txt)
$pip install -U 'git+https://github.com/alphagov/ckanext-s3-resources@50341b3960a6be3aba5a1558e80dd9a8c7c70c2c#egg=ckanext-s3-resources'

$pip install -U $(curl -s https://raw.githubusercontent.com/ckan/ckan/ckan-2.7.4/requirement-setuptools.txt)
$pip install -r https://raw.githubusercontent.com/ckan/ckan/ckan-2.7.4/requirements.txt
$pip install -Ue 'git+https://github.com/ckan/ckan.git@ckan-2.7.4#egg=ckan'

$pip install -r requirements.txt
