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
ENV CKAN_CONFIG /etc/ckan
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

# copy production.ini
ADD . $CKAN_VENV/src/ckanext-datagovuk/
RUN cp -v $CKAN_VENV/src/ckanext-datagovuk/production.ini $CKAN_CONFIG/production.ini

# Setup additional env vars
ENV pipopt='--exists-action=b --force-reinstall'
ENV CKAN_INI $CKAN_CONFIG/production.ini

# ckan 2.9.7

ENV ckan_sha='0d714b258668ee78a0b19182c53b34689629df37'
ENV ckan_fork='ckan'

# Setup CKAN

RUN pip install -U pip && \
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

ENV ckan_harvest_fork='ckan'
ENV ckan_harvest_sha='cb0a7034410f217b2274585cb61783582832c8d5'

ENV ckan_dcat_fork='ckan'
ENV ckan_dcat_sha='618928be5a211babafc45103a72b6aab4642e964'

ENV ckan_spatial_sha='9f9a418c103b697e3ebef309802b7fb62cbf6344'
ENV ckan_spatial_fork='alphagov'

RUN echo "pip install DGU extensions..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat" && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial" && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    # install ckanext-datagovuk
    pip install $pipopt -r requirements.txt && \
    pip install $pipopt -e . && \

    # need these dependencies for harvester run-test to target harvest sources
    pip install $pipopt -U factory-boy==2.12.0 mock==2.0.0 pytest==4.6.5 && \
    # need to pin pyyaml to correctly pick up config settings
    pip install $pipopt -U pyyaml==5.3.1

RUN ckan config-tool $CKAN_INI "ckan.i18n_directory=$CKAN_VENV/src/ckanext-datagovuk/ckanext/datagovuk"
