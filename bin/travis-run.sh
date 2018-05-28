#!/bin/sh -e

echo "NO_START=0\nJETTY_HOST=127.0.0.1\nJETTY_PORT=8983\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart
sleep 10
nosetests --nologcapture --with-pylons=subdir/test.ini --with-coverage --cover-package=ckanext.datagovuk --cover-inclusive --cover-erase --cover-tests ckanext/datagovuk/tests