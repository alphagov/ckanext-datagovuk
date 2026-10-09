ARG ENV=prod

FROM ghcr.io/alphagov/ckan:2.10.11--base AS prod

USER root

COPY . $SRC_DIR/ckanext-datagovuk/
COPY ckan.ini $CKAN_INI

COPY gunicorn_config.py $CKAN_CONFIG/gunicorn_config.py
RUN cp -v $SRC_DIR/ckanext-datagovuk/bin/setup_ckan.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh
ENV PROMETHEUS_MULTIPROC_DIR='/tmp'
ENV PROMETHEUS_METRICS_PORT=8080

ENTRYPOINT ["/ckan-entrypoint.sh"]

WORKDIR $SRC_DIR/ckanext-datagovuk/

RUN echo "pip install ckanext-datagovuk..." && \
    pip install $pipopt -U cython pycryptodome==3.20 && \
    pip install $pipopt -U prometheus-flask-exporter==0.20.3 && \
    # install ckanext-datagovuk
    # setuptools pkg_resources has been removed in setuptools 81 so pin it to 80 to avoid runtime errors, 
    #   see https://github.com/pypa/setuptools/commit/8ba2f3829a8aae66165d9745bf838982dafb3f96
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U setuptools==80 && \
    pip install $pipopt -U -e .

# set ckan as owner to allow updates of the config file and ability to create temp files
RUN chown ckan:ckan-sys ${CKAN_INI}
RUN chown -R ckan:ckan-sys /var/lib/ckan/

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$SRC_DIR/ckan/"
USER ckan

FROM prod AS dev

USER root

RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        git \
        gunicorn \
        wget \
        curl \
        vim \
        less \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

FROM ${ENV} AS final