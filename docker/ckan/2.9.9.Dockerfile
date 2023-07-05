FROM ghcr.io/alphagov/ckan:2.9.9-base

ENTRYPOINT ["/ckan-entrypoint.sh"]

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U -e . 

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
