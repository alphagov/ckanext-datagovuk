# CKAN release rehearsal

## Copy CKAN databases

### Guides

- https://trello.com/c/APwmjzvc/116-copy-database-run-dgu-migration-and-patch-for-ckan-27-in-integration
- https://docs.publishing.service.gov.uk/manual/data-gov-uk-migrating-ckan.html

### Step by step

Make sure you have the following:
1. The AWS DB admin password from govuk-secrets
2. The full AWS hostname of the CKAN machine you want to restore to e.g. `ip-10-1-4-229.eu-west-1.compute.internal.integration`

ckan $
  govuk_puppet --test # Establish a baseline
  sudo service puppet stop
  sudo service ckan stop
  sudo rm -rf /data/vhost/ckan/shared/venv/
jenkins https://deploy.integration.publishing.service.gov.uk/job/Deploy_App/
  redeploy CKAN
ckan $
  sudo service puppet stop
  sudo service ckan stop
db_admin $
  rm -rf ckanext-datagovuk
  git clone https://github.com/alphagov/ckanext-datagovuk --branch bytemark-migration
  eval $(ssh-agent); ssh-add
  ./ckanext-datagovuk/bin/import-ckan-db.sh # approx 2 hours, use a screen
ckan $
  # sudo remove plugins line (90) from /var/ckan/ckan.ini
  cd /var/apps/ckan/
  sudo -u deploy govuk_setenv ckan venv/bin/paster --plugin=ckan db upgrade -c /var/ckan/ckan.ini # 2 to 8 hours, use a screen
  govuk_puppet --test # Restore correct CKAN config
  sudo service puppet stop
  sudo service ckan stop
  sudo -u deploy govuk_setenv ckan venv/bin/paster --plugin=ckan db upgrade -c /var/ckan/ckan.ini
  govuk_puppet --test
  sudo service puppet restart # may need to edit the puppet config to `yes` if you're told it can't restart
  sudo service ckan restart

To reindex Solr, there are three ways to do this:
1. Full reindex which destroys the existing index and creates a new index, default behaviour if no options are specified (WARNING: removes all existing data and takes several days to complete).
2. Add only missing datasets using option `-m` (approximately 15 seconds per dataset).
3. Update all records in the index, but do not delete the old index using option `-r` (this allows the website to continue running whilst the reindex takes place).

ckan $
  cd /var/apps/ckan
  sudo -u deploy govuk_setenv ckan venv/bin/paster search-index rebuild [OPTIONS] -c /var/ckan/ckan.ini

### Copying legacy organograms

local $
  aws sts assume-role --role-arn <role_arn> --serial-number <mfa_arn> --token-code <mfa_token> --role-session-name "$(whoami)-$(date +%d-%m-%y_%H-%M)" --duration-seconds 28800 --profile gds
bytemark $
  export AWS_SECRET_ACCESS_KEY=<from previous output>
  export AWS_ACCESS_KEY_ID=<from previous output>
  export AWS_SESSION_TOKEN="<from previous output>"
  aws s3 sync /var/www/files/drupal/dgud7/organogram s3://datagovuk-production-ckan-organogram/legacy/organogram # 3 mins if full upload, 10 seconds if no-op
  exit # Clear your environment variables and flush bash history to disk
bytemark $
  vi ~/.bash_history # remove your secrets
aws console:
  Check the box next to the `legacy` directory and click Actions -> Make public.  This will take a few minutes.
