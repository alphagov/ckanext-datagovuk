# See CKAN docs on installation from Docker Compose on usage
FROM ubuntu:focal AS base
MAINTAINER Open Knowledge

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_ALL=en_US.UTF-8       
RUN apt-get update
RUN apt-get install --no-install-recommends -y locales
RUN sed -i "/$LC_ALL/s/^# //g" /etc/locale.gen
RUN dpkg-reconfigure --frontend=noninteractive locales 
RUN update-locale LANG=${LC_ALL}

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        python3.8 \
        python3-dev \
        python3-pip \
        python3-venv \
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
    python3 -m venv $CKAN_VENV && \
    # ln -s $CKAN_VENV/bin/pip3 /usr/local/bin/ckan-pip3 &&\
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

# ckan 2.9.7

ENV ckan_sha='0d714b258668ee78a0b19182c53b34689629df37'
ENV ckan_fork='ckan'

# Setup CKAN

RUN pip install -U pip && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt) && \
    pip install --upgrade --no-cache-dir -r https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt && \
    pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan" && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini && \
    chmod +x /pycsw-entrypoint.sh && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

FROM base AS prod

WORKDIR $CKAN_VENV/src

ENTRYPOINT ["/pycsw-entrypoint.sh"]

USER ckan
EXPOSE 5000

ENV ckan_spatial_sha='9f9a418c103b697e3ebef309802b7fb62cbf6344'
ENV ckan_spatial_fork='alphagov'

ENV ckan_harvest_fork='ckan'
ENV ckan_harvest_sha='cb0a7034410f217b2274585cb61783582832c8d5'

RUN echo "pip install spatial extension..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

## 2.6.1 pycsw
ENV pycsw_sha='7fc81b42bfdc5b81250c24887fd6a66032a6b06e'
RUN pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw/$pycsw_sha/requirements.txt) && \
    pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_sha#egg=pycsw" && \
    pycsw_src="$(/usr/bin/env python -m site | grep pycsw | sed "s:[ |,|']::g")" && \
    (cd $pycsw_src && /usr/bin/env python setup.py build)

# need to pin pyyaml to correctly pick up config settings
# pin sqlalchemy to use SessionExtensions
RUN pip install $pipopt -U pyyaml==5.3.1 sqlalchemy==1.3.23
    
RUN ckan config-tool $CKAN_INI "ckan.plugins = harvest ckan_harvester spatial_metadata spatial_query spatial_harvest_metadata_api gemini_csw_harvester gemini_waf_harvester gemini_doc_harvester"
