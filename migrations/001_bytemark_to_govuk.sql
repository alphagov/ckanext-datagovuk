REASSIGN OWNED BY rds_superuser TO ckan;

-- Packages

-- Remove deprecated extras
DELETE FROM package_extra WHERE key = 'individual_resources';
DELETE FROM package_extra WHERE key = 'additional_resources';
DELETE FROM package_extra WHERE key = 'timeseries_resources';

-- Map themes to their key values
UPDATE package_extra SET value = 'business-and-economy' WHERE value = 'Business & Economy' AND key = 'theme-primary';
UPDATE package_extra SET value = 'environment' WHERE value = 'Environment' AND key = 'theme-primary';
UPDATE package_extra SET value = 'mapping' WHERE value = 'Mapping' AND key = 'theme-primary';
UPDATE package_extra SET value = 'crime-and-justice' WHERE value = 'Crime & Justice' AND key = 'theme-primary';
UPDATE package_extra SET value = 'government' WHERE value = 'Government' AND key = 'theme-primary';
UPDATE package_extra SET value = 'society' WHERE value = 'Society' AND key = 'theme-primary';
UPDATE package_extra SET value = 'defence' WHERE value = 'Defence' AND key = 'theme-primary';
UPDATE package_extra SET value = 'government-spending' WHERE value = 'Government Spending' AND key = 'theme-primary';
UPDATE package_extra SET value = 'towns-and-cities' WHERE value = 'Towns & Cities' AND key = 'theme-primary';
UPDATE package_extra SET value = 'education' WHERE value = 'Education' AND key = 'theme-primary';
UPDATE package_extra SET value = 'health' WHERE value = 'Health' AND key = 'theme-primary';
UPDATE package_extra SET value = 'transport' WHERE value = 'Transport' AND key = 'theme-primary';

-- The key for schema vocabulary has changed
UPDATE package_extra SET key = 'schema-vocabulary' WHERE key = 'schema';

-- Remove the organogram viewer resources (links)

UPDATE resource SET state = 'deleted' WHERE description = 'Organogram viewer';

-- Users

-- Remove non-publishing users
ALTER TABLE user_object_role
DROP CONSTRAINT "user_object_role_user_id_fkey",
ADD CONSTRAINT "user_object_role_user_id_fkey" FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;

ALTER TABLE package_role
DROP CONSTRAINT "package_role_user_object_role_id_fkey",
ADD CONSTRAINT "package_role_user_object_role_id_fkey" FOREIGN KEY (user_object_role_id) REFERENCES "user_object_role"(id) ON DELETE CASCADE;

ALTER TABLE group_role
DROP CONSTRAINT "group_role_user_object_role_id_fkey",
ADD CONSTRAINT "group_role_user_object_role_id_fkey" FOREIGN KEY (user_object_role_id) REFERENCES "user_object_role"(id) ON DELETE CASCADE;

ALTER TABLE system_role
DROP CONSTRAINT "system_role_user_object_role_id_fkey",
ADD CONSTRAINT "system_role_user_object_role_id_fkey" FOREIGN KEY (user_object_role_id) REFERENCES "user_object_role"(id) ON DELETE CASCADE;

DELETE FROM "user"
WHERE sysadmin <> 't'
AND id NOT IN (
  SELECT DISTINCT table_id FROM member
  WHERE table_name = 'user'
  AND capacity IN ('admin', 'editor')
);

-- Demote all sysadmins except for the 2ndline user
UPDATE "user" SET sysadmin = 'f' WHERE fullname <> '2ndline';

-- Remove the user's Drupal ID from their username and set their actual username
UPDATE "user" SET name = fullname
WHERE fullname IS NOT NULL
AND (
  state = 'active'
  OR fullname IN (
    SELECT fullname FROM "user"
    WHERE fullname IS NOT NULL
    GROUP BY fullname
    HAVING count(*) = 1
  )
);

UPDATE resource r
SET url = replace(url,
  'https://data.gov.uk/sites/default/files/',
  'https://s3-eu-west-1.amazonaws.com/datagovuk-integration-ckan-organogram/legacy/'
)
FROM package_extra pe
WHERE pe.package_id = r.package_id
AND pe.value in (
  '["538b857a-64ba-490e-8440-0e32094a28a7"]',
  '["d3c0b23f-6979-45e4-88ed-d2ab59b005d0"]'
)
AND pe.key = 'schema-vocabulary'
AND r.url LIKE 'https://data.gov.uk/sites/default/files/organogram/%'
AND r.state = 'active'
AND r.format = 'CSV';

-- Harvest sources

-- Update the source type to match new CKAN
UPDATE harvest_source SET type = 'single-doc' WHERE type = 'gemini-single';
UPDATE harvest_source SET type = 'csw' WHERE type = 'gemini-csw';
UPDATE harvest_source SET type = 'waf' WHERE type = 'gemini-waf';
UPDATE harvest_source SET type = 'dcat_json' WHERE type = 'data_json';

-- Change the DKAN harvester to use the data.json format
UPDATE harvest_source SET url = CONCAT(url, '/data.json'), type = 'dcat_json' WHERE type = 'dkan';

-- Remove a duplicated harvest source to fix a validation error
DELETE FROM harvest_object_extra WHERE harvest_object_id IN (SELECT id FROM harvest_object WHERE harvest_source_id = '2c798023-abac-4785-ad19-67bd5c1aed63');
DELETE FROM harvest_object WHERE harvest_source_id = '2c798023-abac-4785-ad19-67bd5c1aed63';
DELETE FROM harvest_job WHERE source_id = '2c798023-abac-4785-ad19-67bd5c1aed63';
DELETE FROM harvest_source WHERE id = '2c798023-abac-4785-ad19-67bd5c1aed63';

-- Remove indexes that will be rebuilt during the upgrade
DROP INDEX idx_resource_continuity_id;
DROP INDEX idx_member_continuity_id;
DROP INDEX idx_package_continuity_id;
DROP INDEX idx_package_extra_continuity_id;

