-- Due to problems running the ckan harvester source clear command
-- run these SQL commands first before running the ckan harvester command
-- This is targeting the Marine Environmental Data Information Network (MEDIN)

BEGIN TRANSACTION;

-- delete all harvest_object_error related to harvest source
DELETE FROM harvest_object_error WHERE harvest_object_id IN (SELECT id FROM harvest_object where harvest_source_id = '885ee504-c712-4f8d-9034-1c230bcd88a6');

-- delete records in harvest_object_extra related to harvest_source
DELETE FROM harvest_object_extra WHERE harvest_object_id IN (SELECT id FROM harvest_object where harvest_source_id = '885ee504-c712-4f8d-9034-1c230bcd88a6')

-- delete all harvest_object related to harvest source
DELETE FROM harvest_object WHERE harvest_source_id = '885ee504-c712-4f8d-9034-1c230bcd88a6';

-- delete from package_extra 

DELETE FROM package_extra WHERE package_id IN (SELECT id FROM package WHERE owner_org = 'c756c8da-f176-4640-950e-9c00b9e404df' AND type = 'dataset');

-- only delete datasets that have been removed from harvest_object 

WITH data AS (
    SELECT id FROM package
    WHERE owner_org = 'c756c8da-f176-4640-950e-9c00b9e404df' AND type = 'dataset' 
)
DELETE FROM package
-- avoids conflicting datasets
WHERE owner_org = 'c756c8da-f176-4640-950e-9c00b9e404df' AND type = 'dataset' AND id NOT IN (
SELECT package_id FROM data, harvest_object
    WHERE package_id = data.id
)

COMMIT;

-- Finally, delete the datasets on solr manually as the ckan reindex all commands failed to work
/*

- exec onto the pod
kubectl exec -it service/ckan-solr -n datagovuk

- run this command to delete the solr index
curl http://localhost:8983/solr/ckan/update -H "Content-type: text/xml" --data-binary '<delete><query>organization:marine-environmental-data-information-network</query></delete>'

*/
