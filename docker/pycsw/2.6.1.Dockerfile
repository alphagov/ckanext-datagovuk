# See CKAN docs on installation from Docker Compose on usage
FROM ubuntu:jammy AS base

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_CTYPE=en_US.UTF-8
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
        python3-dev \
        python3-pip \
        python3-venv \
        python3.10-venv \
        python3.10-dev \
        python3-wheel \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libmagic-dev \
        libssl-dev \
        libffi-dev \
        postgresql-client \
        build-essential \
        git-core \
        gunicorn \
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
    python3.10 -m venv $CKAN_VENV && \
    # ln -s $CKAN_VENV/bin/pip3 /usr/local/bin/ckan-pip3 &&\
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH}  

COPY bin/setup_pycsw.sh /pycsw-entrypoint.sh
COPY docker/pycsw/pycsw.cfg $CKAN_CONFIG/pycsw.cfg
COPY ckan.ini $CKAN_CONFIG/ckan.ini

# Setup additional env vars
ENV pipopt='--exists-action=b --force-reinstall'
ENV CKAN_INI $CKAN_CONFIG/ckan.ini
ENV PYCSW_CONFIG=/config/pycsw.cfg
ENV CKAN_DB_HOST db

# ckan 2.10

ENV ckan_sha='ac558d6d1751054247ad2bfbb9e531e4b138b457'
ENV ckan_fork='ckan'

# Setup CKAN

RUN pip install -U pip && \
    pip install $pipopt -U cython && \
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

WORKDIR $CKAN_VENV/src

USER ckan
EXPOSE 5000

ENV ckan_spatial_sha='bc345f92b55b44b75c1d44050dd988eab46e0b21'
ENV ckan_spatial_fork='alphagov'

ENV ckan_harvest_fork='ckan'
ENV ckan_harvest_sha='9fb44f79809a1c04dfeb0e1ca2540c5ff3cacef4'

## 2.6.1 pycsw
ENV pycsw_sha='7fc81b42bfdc5b81250c24887fd6a66032a6b06e'
RUN echo "pip install pycsw..." && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/geopython/pycsw/$pycsw_sha/requirements.txt) && \
    pip install $pipopt -Ue "git+https://github.com/geopython/pycsw.git@$pycsw_sha#egg=pycsw" && \
    (cd pycsw && python setup.py build)

RUN echo "pip install spatial extension..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    # save spatial-requirements.txt locally before installing dependencies to work around pip error
    curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt > spatial-requirements.txt && \
    pip install $pipopt -r spatial-requirements.txt && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial"

# install gunicorn to enable running it in the virtualenv
RUN pip install $pipopt -U gunicorn==21.2.0
    
RUN ckan config-tool $CKAN_INI "ckan.plugins = harvest ckan_harvester spatial_metadata spatial_query spatial_harvest_metadata_api gemini_csw_harvester gemini_waf_harvester gemini_doc_harvester"

ENTRYPOINT ["/pycsw-entrypoint.sh"]

WORKDIR $CKAN_VENV/src/pycsw/pycsw
