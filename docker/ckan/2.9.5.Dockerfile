FROM ghcr.io/alphagov/ckan:2.9.5-base

RUN echo "pip install DGU extensions..." && \

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
