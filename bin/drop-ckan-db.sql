ALTER DATABASE ckan_production CONNECTION LIMIT 0; SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ckan_production'; DROP DATABASE ckan_production;
