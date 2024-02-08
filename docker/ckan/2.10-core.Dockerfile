# See CKAN docs on installation from Docker Compose on usage
FROM ubuntu:focal

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_ALL=en_US.UTF-8       
RUN apt-get update && \
    apt-get install --no-install-recommends -y locales && \
    sed -i "/$LC_ALL/s/^# //g" /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=${LC_ALL}

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
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
        libgeos++-dev \ 
        libgeos-3.8.0 \
        libgeos-c1v5 \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt update \ 
    && apt install -y python3.10 python3.10-venv python3.10-dev 

# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    python3.10 -m venv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan


# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH}  

# Set pip args
ENV pipopt='--exists-action=b --force-reinstall'

# ckan 2.10

ENV ckan_sha='ac558d6d1751054247ad2bfbb9e531e4b138b457'
ENV ckan_fork='ckan'

# Setup CKAN - need to install prometheus-flask-exporter as part of CKAN for ckanext-datagovuk assets to be made available

RUN pip install -U pip && \
    pip install $pipopt -U cython pycryptodome==3.20 && \
    pip install $pipopt -U prometheus-flask-exporter==0.20.3 && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt) && \
    curl "https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt" > requirements.txt && \
    pip install --upgrade --no-cache-dir -r requirements.txt && \
    pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan" && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini
