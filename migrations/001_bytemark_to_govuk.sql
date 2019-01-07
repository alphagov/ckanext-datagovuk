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

-- Remove the tags and num_tags
DELETE FROM package_tag CASCADE;
DELETE FROM tag;

-- Remove the organogram viewer resources (links)

UPDATE resource SET state = 'deleted' WHERE description = 'Organogram viewer';

-- Users

-- Remove non-publishing users
DELETE FROM "user" CASCADE WHERE id NOT IN (SELECT DISTINCT user_id FROM user_object_role WHERE role = 'admin' OR role = 'editor') AND sysadmin <> 't';

-- Demote all sysadmins
UPDATE "user" SET sysadmin = 'f';

-- Remove the user's Drupal ID from their username and set their actual username
UPDATE "user" SET name = fullname WHERE fullname IS NOT NULL;

-- Harvest sources

-- Update the source type to match new CKAN
UPDATE harvest_source SET type = 'single-doc' WHERE type = 'gemini-single';
UPDATE harvest_source SET type = 'csw' WHERE type = 'gemini-csw';
UPDATE harvest_source SET type = 'waf' WHERE type = 'gemini-waf';
UPDATE harvest_source SET type = 'dcat_json' WHERE type = 'data_json';

-- Change the DKAN harvester to use the data.json format
UPDATE harvest_source SET url = CONCAT(url, '/data.json'), type = 'dcat_json' WHERE type = 'dkan';

