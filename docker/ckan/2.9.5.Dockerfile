FROM ghcr.io/alphagov/ckan:2.9.5-base

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

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
    pip install $pipopt -U pyyaml==5.4 pyOpenSSL==23.1.0

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR $CKAN_VENV/src/ckan/

ENTRYPOINT ["/ckan-entrypoint.sh"]
