-- drop the tables related and related_dataset as they are preventing deletion of datasets
-- when clearing a harvest source.
-- The tables should have been dropped but because there is an escape clause they were kept 
-- and the warning message missed
-- github.com/ckan/ckan/blob/ckan-2.10.4/ckan/migration/versions/083_f98d8fa2a7f7_remove_related_items.py#L37-L39

BEGIN TRANSACTION;

DROP table related_dataset;
DROP table related;

COMMIT;
