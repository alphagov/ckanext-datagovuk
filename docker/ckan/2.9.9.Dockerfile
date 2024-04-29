FROM ghcr.io/alphagov/ckan:2.9.9-base

USER root

# copy source files and copy production.ini & setup_ckan.sh
COPY . $CKAN_VENV/src/ckanext-datagovuk/
RUN cp -v $CKAN_VENV/src/ckanext-datagovuk/production.ini $CKAN_CONFIG/production.ini && \
    cp -v $CKAN_VENV/src/ckanext-datagovuk/bin/setup_ckan.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh
RUN chown -R ckan:ckan $CKAN_VENV

USER ckan

ENTRYPOINT ["/ckan-entrypoint.sh"]

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U -e . && \

    # pin lxml as 5.1.1 removes required property _ElementStringResult
    # TODO: revisit for CKAN 2.10 upgrade as might not be required
    pip install "lxml<5.1.1"

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
