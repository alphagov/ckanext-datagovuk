FROM govuk/python:3.7.15 AS base

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
RUN apt-get update
RUN apt-get install --no-install-recommends -y locales
RUN echo "LANG=en_US.utf8" > /etc/default/locale 

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
ENV CKAN_CONFIG /config
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    python3.7 -m venv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH}  

# copy setup_pycsw.sh, pycsw.cfg & production.ini
COPY bin/setup_pycsw.sh /pycsw-entrypoint.sh
COPY docker/pycsw/pycsw.cfg $CKAN_CONFIG/pycsw.cfg
COPY production.ini $CKAN_CONFIG/production.ini

# Setup additional env vars
ENV pipopt='--exists-action=b --force-reinstall'
ENV CKAN_INI $CKAN_CONFIG/production.ini
ENV PYCSW_CONFIG=/config/pycsw.cfg
ENV CKAN_DB_HOST db

# ckan 2.9.3

ENV ckan_sha='22613024e9a7303cb85438bd64ca67d168db5436'
ENV ckan_fork='alphagov'

# Setup CKAN

RUN pip install -U pip && \
    pip install $pipopt -U prometheus-flask-exporter==0.20.3 && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt) && \
    # pin zope to 5.0.0 as causing issues - github.com/pypa/setuptools/issues/2017
    curl "https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt" > requirements.txt && \
    sed -i 's/zope.interface==4.3.2/zope.interface==5.0.0/g' ./requirements.txt && \
    pip install --upgrade --no-cache-dir -r requirements.txt && \
    pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan" && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini && \
    chmod +x /pycsw-entrypoint.sh && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

FROM base AS prod

RUN locale-gen en_US.UTF-8

WORKDIR $CKAN_VENV/src

ENTRYPOINT ["/pycsw-entrypoint.sh"]

USER ckan
EXPOSE 5000

ENV ckan_spatial_sha='3199c378ac8f868834f9793cd1654aac47aa1378'
ENV ckan_spatial_fork='alphagov'

ENV ckan_harvest_fork='alphagov'
ENV ckan_harvest_sha='f52605c9a4f8ccaa0f5e83937c59ce9bf58cbc06'

RUN echo "Cython==0.29.35" >> constraints.txt && \
    export PIP_CONSTRAINT="$(pwd)/constraints.txt"

RUN echo "pip install spatial extension..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/pip-requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    # save spatial-requirements.txt locally before installing dependencies to work around pip error
    curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/pip-requirements.txt > spatial-requirements.txt && \
    pip install $pipopt -r spatial-requirements.txt && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

## 2.4.0 pycsw
ENV pycsw_sha='64464c817248d8ff948d957dd11b955cb8cdd490'
RUN pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw/$pycsw_sha/requirements.txt) && \
    pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_sha#egg=pycsw" && \
    (cd pycsw && python setup.py build)

# need to pin pyyaml to correctly pick up config settings
# pin sqlalchemy to use SessionExtensions
RUN pip install $pipopt -U pyyaml==5.3.1 sqlalchemy==1.3.24 Shapely==1.8.5 gunicorn==21.2.0

# upgrade pyopenssl
RUN pip install pyopenssl --upgrade

RUN ckan config-tool $CKAN_INI "ckan.plugins = harvest ckan_harvester spatial_metadata spatial_query spatial_harvest_metadata_api gemini_csw_harvester gemini_waf_harvester gemini_doc_harvester"

# to run the PyCSW wsgi set the WORKDIR to pycsw/pycsw
WORKDIR "$CKAN_VENV/src/pycsw/pycsw"
