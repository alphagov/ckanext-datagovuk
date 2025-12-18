FROM ghcr.io/alphagov/ckan:2.10.7--base

USER root

COPY . $CKAN_VENV/src/ckanext-datagovuk/
COPY production.ini $CKAN_CONFIG/production.ini
COPY gunicorn_config.py $CKAN_CONFIG/gunicorn_config.py
RUN cp -v $CKAN_VENV/src/ckanext-datagovuk/bin/setup_ckan.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh
RUN chown -R ckan:ckan $CKAN_VENV

USER ckan

ENV PROMETHEUS_MULTIPROC_DIR='/tmp'
ENV PROMETHEUS_METRICS_PORT=8080

ENTRYPOINT ["/ckan-entrypoint.sh"]

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

RUN echo "pip install ckanext-datagovuk..." && \

    # install ckanext-datagovuk
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U -e .

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
