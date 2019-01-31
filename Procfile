web: unicornherder --gunicorn-bin ./venv/bin/gunicorn -p /var/run/ckan/unicornherder.pid -- --paste ${CKAN_INI} --timeout ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKER_PROCESSES} --log-file /var/log/ckan/app.out.log --error-logfile /var/log/ckan/app.err.log
celery_priority: ./venv/bin/paster --plugin=ckan jobs worker priority --config=${CKAN_INI}
celery_bulk: ./venv/bin/paster --plugin=ckan jobs worker bulk --config=${CKAN_INI}
harvester_gather_consumer: ./venv/bin/paster --plugin=ckanext-harvest harvester gather_consumer --config=${CKAN_INI}
harvester_fetch_consumer: ./venv/bin/paster --plugin=ckanext-harvest harvester fetch_consumer --config=${CKAN_INI}
