-- this needs to be run after postgis.sh script has run, hence postgis_ suffix

CREATE DATABASE pycsw TEMPLATE template_postgis OWNER ckan ENCODING 'utf-8';
