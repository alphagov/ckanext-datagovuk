# See CKAN docs on installation from Docker Compose on usage
FROM --platform=$TARGETPLATFORM ubuntu:focal

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
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH}  

# Set pip args
ENV pipopt='--exists-action=b --force-reinstall'

# alphagov 2.9.9-fix-email_login

ENV ckan_sha='b6414dc6374c322e2748dad2464bbc872c8de162'
ENV ckan_fork='alphagov'

# Setup CKAN - need to install prometheus-flask-exporter as part of CKAN for ckanext-datagovuk assets to be made available

RUN pip install -U pip && \
    pip install $pipopt -U prometheus-flask-exporter==0.20.3 && \
    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirement-setuptools.txt) && \
    # pin zope to 5.0.0 as causing issues - github.com/pypa/setuptools/issues/2017
    curl "https://raw.githubusercontent.com/$ckan_fork/ckan/$ckan_sha/requirements.txt" > requirements.txt && \
    sed -i 's/zope.interface==4.3.2/zope.interface==5.0.0/g' ./requirements.txt && \
    pip install --upgrade --no-cache-dir -r requirements.txt && \
    pip install $pipopt -Ue "git+https://github.com/$ckan_fork/ckan.git@$ckan_sha#egg=ckan" && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini
