FROM ghcr.io/alphagov/ckan:2.9.9-base

# copy source files and copy production.ini & setup_ckan.sh
COPY . $CKAN_VENV/src/ckanext-datagovuk/
RUN cp -v $CKAN_VENV/src/ckanext-datagovuk/production.ini $CKAN_CONFIG/production.ini && \
    cp -v $CKAN_VENV/src/ckanext-datagovuk/bin/setup_ckan.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

# Set CKAN_INI
ENV CKAN_INI $CKAN_CONFIG/production.ini

ENTRYPOINT ["/ckan-entrypoint.sh"]

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U -e . 

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
