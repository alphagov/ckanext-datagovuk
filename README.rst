
=============
ckanext-datagovuk
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!

--------
Features
--------

- Configures Sentry automatically using a `SENTRY_DSN` environment variable.

------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-datagovuk:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-datagovuk Python package into your virtual environment::

     pip install ckanext-datagovuk

3. Add ``datagovuk`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

Document any optional config settings here.

 - ``ckan.datagovuk.trim_strings_for_index_limit``: when indexing packages, string
   fields will be truncated to this length unless they are known to be under a
   text-indexed key. Solr 6 has a field limit of 32k for string fields, but note
   that our truncation is applied per-json-value, and a Solr value can contain
   multiple json values which then get squashed together to a single field value,
   so using a number under half Solr's limit is wise.


------------------------
Development Installation
------------------------

To install ckanext-datagovuk for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/alphagov/ckanext-datagovuk.git
    cd ckanext-datagovuk
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

Start by running the [docker ckan](https://github.com/alphagov/docker-ckan#development-mode) stack so that the CKAN environment is set up.

Run the tests, do::

    python -m pytest --ckan-ini=test.ini ckanext/datagovuk/tests/

-----------------
Creating test data
-----------------

In order to be able to run the [CKAN functional tests](https://github.com/alphagov/ckan-functional-tests) 
we need to create test data. 

Before running the paster command set the environment varibales:
- CKAN_INI - location of CKAN ini file, this is already set on the docker stack
- CKAN_TEST_SYSADMIN_NAME and CKAN_TEST_SYSADMIN_PASSWORD

Then run the paster command:

   ckan datagovuk create-dgu-test-data

In order to remove the test data:

   ckan datagovuk remove-dgu-test-data
