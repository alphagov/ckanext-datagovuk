-- To trigger the update in Publish the modified date needs to be later than the one in the Publish DB

BEGIN TRANSACTION;

UPDATE package SET metadata_modified = '2020-01-22' WHERE id IN (
    SELECT package_id FROM package_extra
    WHERE key = 'contact-email' AND
    value = 'data.info@environment-agency.gov.uk'
);

UPDATE package_extra SET value = 'DSPcustomerforum@environment-agency.gov.uk' 
WHERE key = 'contact-email' AND value = 'data.info@environment-agency.gov.uk';

COMMIT;
