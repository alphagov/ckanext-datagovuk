FROM ghcr.io/alphagov/ckan:2.9.9-base

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

ENTRYPOINT ["/ckan-entrypoint.sh"]

USER ckan
EXPOSE 5000

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -r requirements.txt && \
    pip install $pipopt -e . 

RUN ckan config-tool $CKAN_INI "ckan.i18n_directory=$CKAN_VENV/src/ckanext-datagovuk/ckanext/datagovuk"

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR $CKAN_VENV/src/ckan/
