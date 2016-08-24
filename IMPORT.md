# Importing existing data

To import existing data into this CKAN from DGU, you should take the following steps.

1. Ensure that you have a working CKAN install with a CKAN Virtualenv available

2. Connect and activate the Virtualenv

3. If you have not installed it before, ```sudo /usr/lib/ckan/bin/pip install ckanapi```

4. You will also need an apikey from the source server to download users.

5. Ensure the following command returns []
   ```ckanapi action package_list -r http://127.0.0.1:8080```

6. Dump data from remote CKAN to local files. This takes a long time.

```
cd ~
mkdir dumps
cd dumps
ckanapi dump organizations --all -O organizations.jsonl.gz -z -p 4  -r https://test.data.gov.uk
ckanapi dump datasets --all -O datasets.jsonl.gz -z  -p 4  -r https://test.data.gov.uk

# Following command does not complete :(  
# ckanapi dump users --all -O users -z  -p 4  -r https://test.data.gov.uk

ckanapi load organizations -I organizations.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

# Clean datasets file before importing
python /vagrant/import/clean_export.py -s datasets.jsonl.gz -o fixed_datasets.jsonl.gz
ckanapi load datasets -I fixed_datasets.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

```
