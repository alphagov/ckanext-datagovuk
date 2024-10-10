-- The harvest_object_id was not being updated properly for OS Open roads datasets
-- so reset the updated_at to before the metadata_modified_date in the harvest source to update them

BEGIN TRANSACTION;

UPDATE datasets SET updated_at = '2024-08-01' WHERE uuid IN ('65bf62c8-eae0-4475-9c16-a2e81afcbdb0', 'd34f5fb0-b40e-4641-a989-9c1f6f11348c');

COMMIT;
