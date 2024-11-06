FROM ghcr.io/alphagov/ckan:2.10.4-f-base

USER root

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
    pip install $pipopt -U -e . 

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
