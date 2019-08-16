web: unicornherder --gunicorn-bin ./venv/bin/gunicorn -p /var/run/ckan/unicornherder.pid -- --paste ${CKAN_INI} --timeout ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKER_PROCESSES} --log-file /var/log/ckan/app.out.log --error-logfile /var/log/ckan/app.err.log
pycsw_web: unicornherder --gunicorn-bin ./venv/bin/gunicorn -p /var/run/ckan/pycsw_unicornherder.pid -- ckanext.datagovuk.pycsw_wsgi --bind localhost:${PYCSW_PORT} --timeout ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKER_PROCESSES} --log-file /var/log/ckan/pycsw.out.log --error-logfile /var/log/ckan/pycsw.err.log

harvester_gather_consumer: ./venv/bin/paster --plugin=ckanext-harvest harvester gather_consumer --config=${CKAN_INI}
harvester_fetch_consumer: ./venv/bin/paster --plugin=ckanext-harvest harvester fetch_consumer --config=${CKAN_INI}
