21st April 2026

Command to run on the solr pod to delete a redundant organisations index, dgu_organisations,  as it was replaced with dgu_organisations_2:

`curl "http://localhost:8983/solr/ckan/update?commit=true" -H "Content-Type: text/xml" --data-binary '<delete><query>site_id:dgu_organisations</query></delete>'`


Verify that it has succeeded with the following command:

`curl "http://localhost:8983/solr/ckan/select?q=site_id:dgu_organisations"`
