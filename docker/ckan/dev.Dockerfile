FROM ghcr.io/alphagov/ckan:2.10.11-dev

# copy zscaler cert and set env vars to use it for SSL connections
# the zscaler cert should be available on your machine, otherwise follow this link to get it:
# - https://help.zscaler.com/zia/adding-custom-certificate-application-specific-trust-store
ADD zscaler.pem /usr/local/share/ca-certificates/zscaler.pem
ENV SSL_CERT_FILE="/usr/local/share/ca-certificates/zscaler.pem"
ENV REQUESTS_CA_BUNDLE="/usr/local/share/ca-certificates/zscaler.pem"

WORKDIR $SRC_DIR/ckanext-datagovuk/

RUN pip install -r dev-requirements.txt

# to run the CKAN wsgi set the WORKDIR to CKAN
WORKDIR "$SRC_DIR/ckan/"
