FROM ghcr.io/alphagov/ckan:2.10

WORKDIR $CKAN_VENV/src/ckanext-datagovuk/

RUN pip install -r dev-requirements.txt

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$CKAN_VENV/src/ckan/"
