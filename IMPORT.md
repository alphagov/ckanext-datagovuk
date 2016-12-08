# Importing existing data

These steps import existing data into this CKAN from the existing data.gov.uk:

1. ssh into the vagrant box of this repo:

       vagrant ssh

2. You will also need an apikey from the source server to download users.

3. Ensure the local db is empty. These commands should both return []:

       ckanapi action package_list -r http://127.0.0.1:8080
       ckanapi action organization_list -r http://127.0.0.1:8080

   And this one should only return the "dgu" user:

       ckanapi action user_list -r http://127.0.0.1:8080

   If you need to wipe the db:

       # DANGER
       sudo service apache2 restart && sudo -u postgres dropdb ckan
       sudo -u postgres createdb ckan -E UTF-8 -T template_postgis -O dgu
       paster --plugin=ckan db init -c /etc/ckan/ckan.ini

4. Get data from remote CKAN to local files.

```
mkdir ~/dumps
cd ~/dumps
curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.v2.jsonl.gz -o datasets.jsonl.gz
rsync -L --progress co@co-prod2.dh.bytemark.co.uk:/var/lib/ckan/ckan/dumps_with_private_data/users.jsonl.gz users.jsonl.gz
rsync -L --progress co@co-prod2.dh.bytemark.co.uk:/var/lib/ckan/ckan/dumps_with_private_data/data.gov.uk-ckan-meta-data-latest.organizations.jsonl.gz organizations.jsonl.gz

# Alternatively get the organizations without the editor/admins:
# curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.organizations.jsonl.gz -o organizations.jsonl.gz

# (Or create the dumps manually:
#   ckanapi dump organizations --all -O organizations.jsonl.gz -z -p 4  -r https://test.data.gov.uk
#   ckanapi dump datasets --all -O datasets.jsonl.gz -z  -p 4  -r https://test.data.gov.uk
#   ckanapi dump users --all -O users.jsonl.gz -z  -p 4 -c $CKAN_INI
# )

```

5. Load the user data (into this box's CKAN):

       ckanapi load users -I users.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

   TODO get this working - currently it complains on missing password_hash

6. Load the organization data (into this box's CKAN):

       ckanapi load organizations -I organizations.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

7. Migrate the dataset data:

       python /vagrant/import/migrate_datasets.py -s datasets.jsonl.gz -o datasets_migrated.jsonl.gz

8. Import the dataset data (this takes about an hour):

       ckanapi load datasets -I datasets_migrated.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini
