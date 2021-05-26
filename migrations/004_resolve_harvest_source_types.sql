-- before running these commands on the database, dump out the existing records affected in package_extra
-- run the update commands below and then use the file to reindex with the 
-- bin/python_scripts/solr_reindex_package_ids.py

UPDATE package_extra SET value = 'gemini-waf' WHERE value = 'waf';
UPDATE package_extra SET value = 'gemini-single' WHERE value = 'single-doc';
UPDATE package_extra SET value = 'gemini-csw' WHERE value = 'csw';
