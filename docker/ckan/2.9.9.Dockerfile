FROM ghcr.io/alphagov/ckan:2.9.9-base

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

ENTRYPOINT ["/ckan-entrypoint.sh"]

USER ckan
EXPOSE 5000

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -r requirements.txt && \
    pip install $pipopt -e . && \

    # need these dependencies for harvester run-test to target harvest sources
    pip install $pipopt -U factory-boy==2.12.0 mock==2.0.0 pytest==4.6.5

RUN ckan config-tool $CKAN_INI "ckan.i18n_directory=$CKAN_VENV/src/ckanext-datagovuk/ckanext/datagovuk"

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR $CKAN_VENV/src/ckan/
