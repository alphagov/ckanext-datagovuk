# Importing existing data

To import existing data into this CKAN from DGU, you should take the following steps.

1. ssh into the vagrant box of this repo:

    vagrant ssh

2. Activate the Virtualenv:

    . /usr/lib/ckan/bin/activate

3. You will also need an apikey from the source server to download users.

4. Ensure the local db is empty - returns [] for these:

       ckanapi action package_list -r http://127.0.0.1:8080
       ckanapi action organization_list -r http://127.0.0.1:8080

   And this should only have the "dgu" user:

       ckanapi action user_list -r http://127.0.0.1:8080

   If you need to wipe the db:

       # DANGER
       sudo service apache2 restart && sudo -u postgres dropdb ckan
       sudo -u postgres createdb ckan -E UTF-8 -T template_postgis -O dgu
       paster --plugin=ckan db init -c /etc/ckan/ckan.ini

5. Get data from remote CKAN to local files. This takes a long time.

```
mkdir ~/dumps
cd ~/dumps
curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.v2.jsonl.gz -o datasets.jsonl.gz
curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.organizations.jsonl.gz -o organizations.jsonl.gz

# (Or create the dumps manually:
#   ckanapi dump organizations --all -O organizations.jsonl.gz -z -p 4  -r https://test.data.gov.uk
#   ckanapi dump datasets --all -O datasets.jsonl.gz -z  -p 4  -r https://test.data.gov.uk
# )

# Following command does not complete :(
# ckanapi dump users --all -O users -z  -p 4  -r https://test.data.gov.uk
```

6. Load the organization data into this box's CKAN:

    ckanapi load organizations -I organizations.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

7. Migrate the dataset data and then import:

    python /vagrant/import/migrate_datasets.py -s datasets.jsonl.gz -o datasets_migrated.jsonl.gz
    ckanapi load datasets -I datasets_migrated.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

