#!/usr/bin/env bash

set -e

dumpfile=ckan-dump_$(date +"%Y-%m-%d_%H-%M-%S").pgdump

echo "Please be aware this whole process will take around 2 hours to complete and will wipe the CKAN database on this machine."
echo
read -s -p "Enter the hieradata password for 'aws_db_admin' to continue: " password
echo

export PGPASSWORD=$password

echo "Exporting the bytemark database, this will take approx 35 minutes"
ssh co@co-prod3.dh.bytemark.co.uk "pg_dump -x -O -Fc ckan > $dumpfile"

echo "Copying the export from bytemark to AWS, this will take approx 10 minutes"
scp co@co-prod3.dh.bytemark.co.uk:~/$dumpfile .

echo "Dropping the existing database"
psql postgres://aws_db_admin@postgresql-primary/postgres -f ckanext-datagovuk/bin/drop_ckan_database.sql

echo "Recreating the database via puppet"
govuk_puppet --test

echo "Importing the database, this will take approx 1 hour"
pg_restore -l $dumpfile | grep -v tag > /tmp/restore_list.txt
pg_restore -v -h postgresql-primary -U aws_db_admin -d ckan_production --schema-only -t package_tag -t tag -t package_tag_revision --role=rds_superuser --no-owner $dumpfile
pg_restore -v -h postgresql-primary -U aws_db_admin -d ckan_production -L /tmp/restore_list.txt --role=rds_superuser --no-owner $dumpfile

echo "Migrate the data to the new CKAN version"
psql postgres://aws_db_admin@postgresql-primary/ckan_production -c "reassign owned by rds_superuser to ckan;"
psql postgres://aws_db_admin@postgresql-primary/ckan_production -f ckanext-datagovuk/migrations/001_bytemark_to_govuk.sql
