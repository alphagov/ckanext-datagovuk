#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install postgresql-$PGVERSION solr-jetty libcommons-fileupload-java

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
echo "CKAN branch: v2.7"
git checkout 2.7
sed -i -e 's/psycopg2==2.4.5/psycopg2==2.7.3.2/g' requirements.txt
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
cd -

echo "Installing ckanext-harvest and its Python dependencies..."
git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
python setup.py develop
pip install -r pip-requirements.txt
cd -

echo "Installing ckanext-spatial and its Python dependencies..."
git clone https://github.com/ckan/ckanext-spatial
cd ckanext-spatial
python setup.py develop
pip install -r pip-requirements.txt
cd -

echo "Updating Solr configuration..."
cd ckan
sed -i -e 's/^solr_url.*/solr_url = http:\/\/127.0.0.1:8983\/solr/' test-core.ini
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
paster --plugin=ckanext-harvest harvester initdb -c test-core.ini
cd -

echo "Installing ckanext-datagovuk and its requirements..."
python setup.py develop
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."

