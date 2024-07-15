-- drop the harvest_coupled_resource table as it is preventing deletion of datasets
-- when clearing a harvest source.
-- The harvest_coupled_resource table is not referenced anywhere in the ckanext-harvest or ckan repo
-- so it will be removed in order to stop the blocking of clearing harvest sources.

BEGIN TRANSACTION;

DROP table harvest_coupled_resource;

COMMIT;
