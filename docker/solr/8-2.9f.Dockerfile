FROM ckan/ckan-solr:2.9-solr8-spatial

# Enviroment
ENV SOLR_CORE ckan

# Giving ownership to Solr
USER root

# replace the ckan-2.10 schema with the 2.9 schema to make it compatible with CSW
RUN sed -z 's/<schema name="ckan-2.10" version="1.6">/<schema name="ckan" version="2.9">/' -i /opt/solr/server/solr/configsets/ckan/conf/managed-schema

# Add harvest field to schema
RUN sed -z 's/<field name="urls" type="text" indexed="true" stored="false" multiValued="true"\/>/<field name="urls" type="text" indexed="true" stored="false" multiValued="true"\/>\n    <field name="harvest" type="text" indexed="true" stored="true" multiValued="true"\/>/' -i /opt/solr/server/solr/configsets/ckan/conf/managed-schema

# Set to restricted User
USER $SOLR_USER:$SOLR_USER
