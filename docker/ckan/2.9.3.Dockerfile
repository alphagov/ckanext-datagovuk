# See CKAN docs on installation from Docker Compose on usage
FROM governmentdigitalservice/ckan-python:3.6.12 AS base
MAINTAINER Open Knowledge

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        python3-dev \
        python3-pip \
        python3-wheel \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libssl-dev \
        libffi-dev \
        postgresql-client \
        build-essential \
        git-core \
        vim \
        wget \
        curl \
        proj-bin \
        libproj-dev \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    python3.6 -m venv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH}  

# copy production.ini
COPY . $CKAN_VENV/src/ckanext-datagovuk/
RUN cp -v $CKAN_VENV/src/ckanext-datagovuk/production.ini $CKAN_CONFIG/production.ini

# Setup additional env vars
ENV pipopt='--exists-action=b --force-reinstall'
ENV CKAN_INI $CKAN_CONFIG/production.ini

# alphagov 2.9.3

ENV ckan_sha='22613024e9a7303cb85438bd64ca67d168db5436'
ENV ckan_fork='alphagov'

# Setup CKAN - need to install prometheus-flask-exporter as part of CKAN for ckanext-datagovuk assets to be made available

RUN pip install -U pip && \
    pip install $pipopt -U prometheus-flask-exporter==0.20.3 && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt) && \
    pip install --upgrade --no-cache-dir -r https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt && \
    pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan" && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini && \
    cp -v $CKAN_VENV/src/ckanext-datagovuk/bin/setup_ckan.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

FROM base AS prod

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

ENTRYPOINT ["/ckan-entrypoint.sh"]

USER ckan
EXPOSE 5000

ENV ckan_harvest_fork='alphagov'
ENV ckan_harvest_sha='f52605c9a4f8ccaa0f5e83937c59ce9bf58cbc06'

ENV ckan_dcat_fork='alphagov'
ENV ckan_dcat_sha='be3b809fa7431c8d81508c01853e81ce6a5dfd84'

ENV ckan_spatial_sha='bac67ccb236b718d226ef5ac7844723222d3b5c5'
ENV ckan_spatial_fork='alphagov'

RUN echo "pip install DGU extensions..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat" && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial" && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    # install ckanext-datagovuk
    pip install $pipopt -r requirements.txt && \
    pip install $pipopt -e . && \

    # need these dependencies for harvester run-test to target harvest sources
    pip install $pipopt -U factory-boy==2.12.0 mock==2.0.0 pytest==4.6.5 && \
    # need to pin pyyaml to correctly pick up config settings
    # install pyOpenSSL to work with certs
    pip install $pipopt -U pyyaml==5.3.1 pyOpenSSL==23.1.0

RUN ckan config-tool $CKAN_INI "ckan.i18n_directory=$CKAN_VENV/src/ckanext-datagovuk/ckanext/datagovuk"

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR $CKAN_VENV/src/ckan/
