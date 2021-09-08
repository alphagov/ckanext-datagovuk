UPDATE resource 
SET extras = '{"datafile-date": "", "resource-type": "data-link"}',
last_modified = '2021-09-08' where id IN
(SELECT id FROM resource WERE state = 'active' AND extras LIKE '%filename%');