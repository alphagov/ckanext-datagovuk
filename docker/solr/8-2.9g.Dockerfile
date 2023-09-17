FROM ckan/ckan-solr:2.9-solr8-spatial

# Enviroment
ENV SOLR_CORE ckan

# Giving ownership to Solr
USER root

# used a modified ckan-2.10 schema to work with CKAN 2.9 to make it compatible with CSW
COPY docker/solr/schema.solr8.xml /opt/solr/server/solr/configsets/ckan/conf/managed-schema
RUN mkdir -p /var/solr/data/ckan/conf/ && chown -R $SOLR_USER:$SOLR_USER /var/solr/data/ckan/conf/
COPY docker/solr/schema.solr8.xml /var/solr/data/ckan/conf/managed-schema

# Set to restricted User
USER $SOLR_USER:$SOLR_USER
