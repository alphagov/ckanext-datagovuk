FROM ghcr.io/alphagov/ckan:2.9.9-base

ENTRYPOINT ["/ckan-entrypoint.sh"]

ENV ckan_spatial_sha='91953714aad5ae993c9f5a5690bb8d51df1a10b1'

RUN echo "pip install ckanext-datagovuk..." && \

    # force reinstall of spatial
    curl -s "https://raw.githubusercontent.com/$ckan_spatial_fork/ckanext-spatial/$ckan_spatial_sha/requirements.txt" > spatial-requirements.txt && \
    pip install $pipopt -r spatial-requirements.txt && \
    pip install $pipopt -U "git+https://github.com/$ckan_spatial_fork/ckanext-spatial.git@$ckan_spatial_sha#egg=ckanext-spatial" && \

    # need to pin pyyaml to correctly pick up config settings
    pip install $pipopt -U pyyaml==5.4 && \

    # install ckanext-datagovuk
    pip install $pipopt -U -r requirements.txt && \
    pip install $pipopt -U -e . 

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
