-- run this command to set duplicate datasets to a deleted state
-- then select the ids matching metadata_modified = '2023-02-27' 
-- and save the output to be processed by running the python script located under bin/python_scripts
-- 'python solr_reindex_target_date.py 2023-02-27 reindex deleted'
-- 
-- This command sets a package to deleted and metadata_modified to 2023-02-27 where 
-- the package title is a duplicate and is in an active state and the package id is
-- not the current harvest object

UPDATE package SET state = 'deleted',  metadata_modified = '2023-02-27' WHERE id IN
(
    SELECT DISTINCT package_id from harvest_object WHERE package_id IN 
    (
        WITH data AS (
            SELECT * FROM
            (
                SELECT package.id, package.name, package.title, COUNT(1)OVER(partition BY title) AS Cnt
                FROM package
                WHERE package.state = 'active'
            )a
            Where Cnt > 1
        ) 
        SELECT id FROM data
    ) AND package_id IN
    (
        WITH a (package_id) AS (
            SELECT package_id FROM harvest_object WHERE current = false
        ), 
        b (package_id) AS (
            SELECT package_id FROM harvest_object WHERE current = true
        )
        SELECT DISTINCT package_id FROM a, package 
        WHERE package_id <> '' AND package_id = package.id AND state = 'active'
        EXCEPT all
        SELECT package_id FROM b
    )
);