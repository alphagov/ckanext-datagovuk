FROM ckan/ckan-solr:2.10

# Enviroment
ENV SOLR_CORE ckan

# Giving ownership to Solr
USER root

# Add harvest field to schema

RUN sed -z 's/<field name="urls" type="text" indexed="true" stored="false" multiValued="true"\/>/<field name="urls" type="text" indexed="true" stored="false" multiValued="true"\/>\n    <field name="harvest" type="text" indexed="true" stored="true" multiValued="true"\/>/' -i /opt/solr/server/solr/configsets/ckan/conf/managed-schema

# Set to restricted User
USER $SOLR_USER:$SOLR_USER
