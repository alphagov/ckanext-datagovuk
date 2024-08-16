FROM --platform=$TARGETPLATFORM ghcr.io/alphagov/ckan:2.10.4-b-core

COPY production.ini $CKAN_CONFIG/production.ini
# Set CKAN_INI
ENV CKAN_INI=$CKAN_CONFIG/production.ini

RUN chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

ENV ckan_harvest_fork='ckan'
ENV ckan_harvest_sha='9fb44f79809a1c04dfeb0e1ca2540c5ff3cacef4'

ENV ckan_dcat_fork='ckan'
ENV ckan_dcat_sha='618928be5a211babafc45103a72b6aab4642e964'

ENV ckan_spatial_sha='c9c742a16295fc898b604b58de2e1bb4b3966d50'
ENV ckan_spatial_fork='alphagov'

RUN echo "pip install DGU extensions..." && \

    pip install $pipopt -U $(curl -s "https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt") && \
    pip install $pipopt -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat" && \

    # save spatial-requirements.txt locally before installing dependencies to work around pip error
    curl -s "https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt" > spatial-requirements.txt && \
    pip install $pipopt -r spatial-requirements.txt && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial" && \

    pip install $pipopt -U $(curl -s "https://raw.githubusercontent.com/$ckan_harvest_fork/ckanext-harvest/$ckan_harvest_sha/requirements.txt") && \
    pip install $pipopt -U "git+https://github.com/$ckan_harvest_fork/ckanext-harvest.git@$ckan_harvest_sha#egg=ckanext-harvest" && \

    # need these dependencies for harvester run-test to target harvest sources
    pip install $pipopt -U factory-boy==3.3.0 mock==2.0.0 pytest==7.4.3 && \

    # need to pin pyyaml to correctly pick up config settings
    pip install $pipopt -U pyyaml==6.0.1

EXPOSE 5000
