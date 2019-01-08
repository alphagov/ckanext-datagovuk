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
local $
  ssh -L 8983:localhost:8983 ip-10-1-4-229.eu-west-1.compute.internal.integration # ckan AWS
  ssh -L 8984:localhost:8983 co@co-prod3.dh.bytemark.co.uk # ckan Bytemark
  open http://localhost:8983/solr/ # use this to monitor AWS solr
  open http://localhost:8984/solr/ # use this to monitor Bytemark solr
co@prod3 $
  cd /usr/share/solr/solr-4.3.1/example/solr/
  tar czvf ~/solr-snapshot.tgz collection1 # 2 mins
local $
  scp co@co-prod3.dh.bytemark.co.uk:~/solr-snapshot.tgz . # approx 5 minutes
  ssh co@co-prod3.dh.bytemark.co.uk "rm ~/solr-snapshot.tgz"
  scp solr-snapshot.tgz ip-10-1-4-229.eu-west-1.compute.internal.integration:~/ # approx 15 minutes, limit speed with `-L` if needed
ckan $
  sudo mv solr-snapshot.tgz /var/lib/solr/solr-4.3.1/example/solr/
  cd /var/lib/solr/solr-4.3.1/example/solr/
  ll # confirm all looks well
  sudo rm -rf collection1
  sudo tar xzvf solr-snapshot.tgz # 30 secs, use screen
  sudo rm solr-snapshot.tgz
  sudo chown -R solr:solr collection1
  govuk_puppet --test # restore correct solr config and enable services
http://localhost:8983/solr/
  check on core status
    if core is missing
      curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=collection1&instanceDir=collection1"
    if core is showing a red circle on "optimized"
      click "Optimize"
ckan $
  sudo service ckan restart


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
