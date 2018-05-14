# Importing existing data

These steps import existing data into this CKAN from the existing data.gov.uk.

1. ssh into the vagrant box of this repo:

       vagrant ssh

2. Ensure the local db is empty. These commands should both return []:

       ckanapi action package_list -r http://127.0.0.1:8080
       ckanapi action organization_list -r http://127.0.0.1:8080

   And this one should only return the "dgu" user:

       ckanapi action user_list -r http://127.0.0.1:8080

   If you need to wipe the db:

       # DANGER
       sudo service apache2 restart && sudo -u postgres dropdb ckan
       sudo -u postgres createdb ckan -E UTF-8 -T template_postgis -O dgu
       paster --plugin=ckan db init -c /etc/ckan/ckan.ini

3. Get data from remote CKAN to local files.

```
mkdir ~/dumps
cd ~/dumps
curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.v2.jsonl.gz -o datasets.jsonl.gz
rsync -L --progress co@co-prod3.dh.bytemark.co.uk:/var/lib/ckan/ckan/dumps_with_private_data/users.jsonl.gz users.jsonl.gz
rsync -L --progress co@co-prod3.dh.bytemark.co.uk:/var/lib/ckan/ckan/dumps_with_private_data/data.gov.uk-ckan-meta-data-latest.organizations.jsonl.gz organizations.jsonl.gz
rsync -L --progress co@co-prod3.dh.bytemark.co.uk:/var/lib/ckan/ckan/dumps_with_private_data/drupal_users_table.csv.gz drupal_users_table.csv.gz

# Alternatively get the organizations without the editor/admins:
# curl https://data.gov.uk/data/dumps/data.gov.uk-ckan-meta-data-latest.organizations.jsonl.gz -o organizations.jsonl.gz

# (Or create the dumps manually:
#   ckanapi dump organizations --all -O organizations.jsonl.gz -z -p 4  -r https://test.data.gov.uk
#   ckanapi dump datasets --all -O datasets.jsonl.gz -z  -p 4  -r https://test.data.gov.uk
#   ckanapi dump users --all -O users.jsonl.gz -z  -p 4 -c $CKAN_INI
# )

```

4. Migrate the user and organisation data into a file ready for the next step(takes 10s):

       python /vagrant/import/migrate_users.py users.jsonl.gz drupal_users_table.csv.gz users_migrated.jsonl.gz organizations.jsonl.gz organizations_migrated.jsonl.gz

   Alternatively add the production flag to use Drupal password hashes (else they are randomised):

       python /vagrant/import/migrate_users.py users.jsonl.gz drupal_users_table.csv.gz users_migrated.jsonl.gz organizations.jsonl.gz organizations_migrated.jsonl.gz --production

*. Optional - upgrade ckanapi so that it summarizes load errors

       sudo /usr/lib/venv/bin/pip uninstall ckanapi
       cd ~
       git clone git@github.com:ckan/ckanapi.git
       sudo /usr/lib/venv/bin/pip install -e ckanapi
       cd ckanapi
       git pull origin print-result-stats
       cd ~/dumps

5. Load the user data (takes an hour or so):

       ckanapi load users -I users_migrated.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

6. Load the organization data (takes a few minutes):

       ckanapi load organizations -I organizations.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini

7. Migrate the dataset data (takes one minute):

       python /vagrant/import/migrate_datasets.py -s datasets.jsonl.gz -o datasets_migrated.jsonl.gz

8. Import the dataset data (takes 4.5 hours on an EC2 t2.medium):

       ckanapi load datasets -I datasets_migrated.jsonl.gz -z -p 3 -c /etc/ckan/ckan.ini
