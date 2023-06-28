FROM ghcr.io/alphagov/ckan:2.9.9-base

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

ENTRYPOINT ["/ckan-entrypoint.sh"]

USER ckan
EXPOSE 5000

ENV ckan_harvest_fork='ckan'
ENV ckan_harvest_sha='cb0a7034410f217b2274585cb61783582832c8d5'

ENV ckan_dcat_fork='ckan'
ENV ckan_dcat_sha='618928be5a211babafc45103a72b6aab4642e964'

ENV ckan_spatial_sha='09e64db545ac1c79e0230a056a2351c33afa2a70'
ENV ckan_spatial_fork='alphagov'

RUN echo "pip install DGU extensions..." && \

    pip install $pipopt -U $(curl -s https://raw.githubusercontent.com/$ckan_dcat_fork/ckanext-dcat/$ckan_dcat_sha/requirements.txt) && \
    pip install $pipopt -U "git+https://github.com/$ckan_dcat_fork/ckanext-dcat.git@$ckan_dcat_sha#egg=ckanext-dcat" && \

    # save spatial-requirements.txt locally before installing dependencies to work around pip error
    curl -s https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt > spatial-requirements.txt && \
    pip install $pipopt -r spatial-requirements.txt && \
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

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR $CKAN_VENV/src/ckan/
