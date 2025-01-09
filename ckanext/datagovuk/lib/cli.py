import click
import csv
import os
import subprocess
import sys
import sqlalchemy
from datetime import datetime, timedelta
import json
import pysolr

from functools import wraps

from ckan import logic
from ckan import model
from ckan.lib.mailer import create_reset_key
from ckan.lib.search.index import PackageSearchIndex
import ckan.plugins.toolkit as tk

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester
from ckanext.harvest.logic.action.create import harvest_job_create, harvest_source_create
from ckanext.harvest.logic.schema import harvest_source_schema
from ckanext.harvest.model import define_harvester_tables
from ckanext.harvest.plugin import _create_harvest_source_object


def get_commands():
    return [datagovuk]


@click.group()
def datagovuk():
    """ Datagovuk test data creation and removal.
    """
    pass


def pass_context(f):
    @wraps(f)
    @click.pass_context
    def decorated(*args, **kwargs):
        flask_app = args[0].meta["flask_app"]
        with flask_app.test_request_context():
            return f(*args, **kwargs)
    return decorated


@datagovuk.command()
@pass_context
def create_dgu_test_data(context):
    '''Creates the test data so that CKAN API functional tests can run

        Set your environment varibales:
            CKAN_INI - location of CKAN ini file 
            CKAN_TEST_SYSADMIN_NAME and CKAN_TEST_SYSADMIN_PASSWORD

        ckan -c $CKAN_INI datagovuk create-dgu-test-data
    '''
    def add_empty_field(dataset_id, fieldname, model):
        field = model.PackageExtra(package_id=dataset_id, key=fieldname, value="")
        model.Session.add(field)

    if not all(os.environ.get(i) for i in ('CKAN_TEST_SYSADMIN_NAME', 'CKAN_TEST_SYSADMIN_PASSWORD', 'CKAN_INI')):
        print('One of these env vars not set: CKAN_INI, CKAN_TEST_SYSADMIN_NAME or CKAN_TEST_SYSADMIN_PASSWORD')
        return

    print('====== Creating DGU test data')
    engine = sqlalchemy.create_engine(tk.config.get('sqlalchemy.url'))
    model.init_model(engine)

    sysadmin_user = model.User.get(os.environ.get('CKAN_TEST_SYSADMIN_NAME'))
    if not sysadmin_user:
        print('=== Creating test sysadmin')
        sysadmin_user = model.User(
            name=os.environ.get('CKAN_TEST_SYSADMIN_NAME'),
            password=os.environ.get('CKAN_TEST_SYSADMIN_PASSWORD')
        )
        sysadmin_user.sysadmin = True
        model.Session.add(sysadmin_user)
        model.repo.commit_and_remove()

    publisher = model.Group.get('example-publisher-1')
    if not publisher:
        print('=== Creating example publisher 1')
        model.Session.flush()

        publisher = model.Group(
            name=u"example-publisher-1",
            title=u"Example Publisher #1",
            type=u"organization"
        )
        publisher.is_organization = True
        model.Session.add(publisher)
        model.repo.commit_and_remove()

        category = model.GroupExtra(group_id=publisher.id, key="category", value="charity-ngo")
        model.Session.add(category)
        model.repo.commit_and_remove()

        print('=== Creating example publisher 1 member')
        model.Session.flush()

        default = model.User.get('default')
        if not default:
            default = model.User(
                name="default",
                password="test1234"
            )
            model.Session.add(default)
            model.repo.commit_and_remove()

        member = model.Member(
            group=publisher,
            group_id=publisher.id,
            table_id=default.id,
            table_name="user",
            capacity="editor",
            state="active"
        )
        model.Session.add(member)
        model.repo.commit_and_remove()

        print('=== Creating default dataset')
        model.Session.flush()

        dataset = model.Package(
            name=u"test-dataset",
            title=u"Test dataset",
            notes=u"Test dataset for default user",
            owner_org=publisher.id,
            creator_user_id=default.id,
            state="active"
        )
        model.Session.add(dataset)
        model.repo.commit_and_remove()

    if not model.Package.by_name(u"example-harvest-1"):
        print('=== Creating harvest source')

        source_dict = {
            "title": "Example Harvest #1",
            "name": "example-harvest-1",
            "url": tk.config.get('ckan.mock_harvest_source'),
            "source_type": "ckan",
            'owner_org': publisher.id,
            "notes": "An example harvest source",
            "frequency": "MANUAL",
            "activ": True,
            "config": None,
            "run": True
        }
        context = {
            "model": model,
            "session": model.Session,
            "user": sysadmin_user.name,
            "ignore_auth": True,
            "schema": harvest_source_schema(),
            "message": "Create DGU example harvest source",
            "return_id_only": True
        }

        harvest_source_id = harvest_source_create(context, source_dict)

        if harvest_source_id:
            print("=== Creating harvest job")
            harvest_job_create(context, {"source_id": harvest_source_id, "run": False})

            print("=== Running harvest job")
            command = "ckan -c $CKAN_INI harvester run-test example-harvest-1"
            run_command(command)

            model.Session.flush()

            print("=== Updating the example dataset to be in line with how DGU processes it")
            dataset = model.Package.get("example-dataset-number-one")

            contact_name = model.PackageExtra(package_id=dataset.id, key="contact-name", value="Example User")
            model.Session.add(contact_name)

            empty_fields = [
                "contact-email",
                "contact-phone",
                "schema-vocabulary",
                "codelist",
                "licence-custom",
                "foi-web",
                "foi-name",
                "foi-email",
                "foi-phone",
                "theme-primary"
            ]

            for key in empty_fields:
                field = model.PackageExtra(package_id=dataset.id, key=key, value="")
                model.Session.add(field)

            delete_fields = [
                "guid", "responsible-party", "taxonomy_url"
            ]
            for key in delete_fields:
                field = model.Session.query(model.PackageExtra).filter(
                    model.PackageExtra.package_id == dataset.id, model.PackageExtra.key == key
                ).first()
                if field:
                    field.delete()

            model.repo.commit_and_remove()

            print("=== Running search index rebuild")
            command = 'ckan search-index rebuild %s' % dataset.name
            run_command(command)

    publisher2 = model.Group.get('example-publisher-2')
    if not publisher2:
        print('=== Creating example publisher 2')
        model.Session.flush()

        publisher2 = model.Group(
            name=u"example-publisher-2",
            title=u"Example Publisher #2",
            type="organization"
        )
        publisher2.is_organization = True
        model.Session.add(publisher2)
        model.repo.commit_and_remove()

    print("=== To use with CKAN functional tests in ckan-vars.conf set OWNER_ORG=%s" % publisher.id)
    print("====== DGU test data created")


@datagovuk.command()
@pass_context
def remove_dgu_test_data(context):
    '''Removes the DGU test data

        Set your environment varibales:
            CKAN_INI - location of CKAN ini file 
            CKAN_TEST_SYSADMIN_NAME

        ckan -c $CKAN_INI datagovuk remove-dgu-test-data
    '''
    if not all(os.environ.get(i) for i in ('CKAN_TEST_SYSADMIN_NAME', 'CKAN_INI')):
        print('CKAN_TEST_SYSADMIN_NAME or CKAN_INI env var not set')
        return

    print('====== Removing DGU test data')

    engine = sqlalchemy.create_engine(tk.config.get('sqlalchemy.url'))
    model.init_model(engine)

    command = "ckan -c $CKAN_INI harvester source clear example-harvest-1"
    run_command(command)

    command = "ckan -c $CKAN_INI harvester source remove example-harvest-1"
    run_command(command)

    sql = '''
    DELETE FROM package_extra_revision WHERE package_id in (SELECT id FROM package WHERE name='example-harvest-1'); 
    DELETE FROM package_extra WHERE package_id IN (SELECT id FROM package WHERE name='example-harvest-1');
    DELETE FROM package_revision WHERE name = 'example-harvest-1';
    DELETE FROM package WHERE name = 'example-harvest-1';
    DELETE FROM package WHERE name = 'test-dataset';
    DELETE FROM harvest_object WHERE harvest_source_id IN (SELECT id FROM harvest_source WHERE title = 'Example Harvest #1');
    DELETE FROM harvest_job WHERE source_id IN (SELECT id FROM harvest_source WHERE title = 'Example Harvest #1');
    DELETE FROM harvest_source WHERE title = 'Example Harvest #1';
    DELETE FROM member_revision WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
    DELETE FROM member WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
    DELETE FROM group_extra_revision WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
    DELETE FROM group_extra WHERE group_id IN (SELECT id FROM "group" WHERE name = 'example-publisher-1');
    DELETE FROM group_revision WHERE name = 'example-publisher-1';
    DELETE FROM "group" WHERE name = 'example-publisher-1';
    DELETE FROM group_revision WHERE name = 'example-publisher-2';
    DELETE FROM "group" WHERE name = 'example-publisher-2';
    DELETE FROM "user" WHERE name = 'default';
    DELETE FROM "user" WHERE name = :testadmin_name;
    '''

    model.Session.execute(sql, {"testadmin_name": os.environ.get('CKAN_TEST_SYSADMIN_NAME')})
    model.repo.commit_and_remove()

    command = 'ckan search-index clear example-publisher-1'
    run_command(command)

    command = 'ckan search-index clear example-publisher-2'
    run_command(command)

    print("====== DGU test data removed")


@datagovuk.command()
@pass_context
def remove_ckan_admin(context):
    '''Removes the CKAN_SYSADMIN_NAME user 
       WARNING - This should be only executed on a dev stack

        Set your environment varibales:
            CKAN_INI - location of CKAN ini file 
            CKAN_SYSADMIN_NAME

        ckan -c $CKAN_INI datagovuk remove-ckan-admin
    '''
    if not all(os.environ.get(i) for i in ('CKAN_SYSADMIN_NAME', 'CKAN_INI')):
        print('CKAN_SYSADMIN_NAME or CKAN_INI env var not set')
        return

    print('====== Removing CKAN_SYSADMIN_NAME user')

    engine = sqlalchemy.create_engine(tk.config.get('sqlalchemy.url'))
    model.init_model(engine)

    sql = '''
    DELETE FROM "user" WHERE name = :ckan_admin_name;
    '''

    model.Session.execute(sql, {"ckan_admin_name": os.environ.get('CKAN_SYSADMIN_NAME')})
    model.repo.commit_and_remove()


@datagovuk.command()
@pass_context
def reindex_recent(context):
    '''
        Reindexes recent datasets with the latest status
    '''
    REINDEX_MINUTES_BEFORE = os.environ.get('CKAN_REINDEX_MINUTES_BEFORE', 24*60)

    engine = sqlalchemy.create_engine(tk.config.get('sqlalchemy.url'))
    model.init_model(engine)

    context = {'model': model, 'session': model.Session,
                        'user': os.environ.get('CKAN_SYSADMIN_NAME')}

    reindex_start = (datetime.now() - timedelta(minutes=REINDEX_MINUTES_BEFORE)).strftime('%Y-%m-%d %H:%M')

    packages = model.Session.query(model.Package) \
                            .filter(model.Package.type == 'dataset') \
                            .filter(model.Package.state == u'active') \
                            .filter(model.Package.metadata_modified > reindex_start) \
                            .all()

    print(f'Reindexing recent datasets from {reindex_start}, {len(packages)} found')

    if not packages:
        print(f'No datasets to reindex since {reindex_start}')
        return

    package_index = PackageSearchIndex()

    defer_commit = {'defer_commit': True}
    for i, package in enumerate(packages):
        context.update({'ignore_auth': True})
        package_dict = logic.get_action('package_show')(context, {'id': package.id})
        print(f'{i+1}/{len(packages)} - Updating search index:', package_dict.get('name'))

        # Remove configuration values
        new_dict = {}

        try:
            config = json.loads(package_dict.get('config', ''))
        except ValueError:
            config = {}
        for key, value in package_dict.items():
            if key not in config:
                new_dict[key] = value

        package_index = PackageSearchIndex()
        package_index.index_package(new_dict, defer_commit=defer_commit)

    package_index.commit()

###
# Reindex organisation will only add organisations
# To update an organisation you will need to remove it first before running it:
#
# curl -g "http://$CKAN_SOLR_URL/solr/ckan/update?commit=true" \
#     -H 'Content-Type: application/json' \
#     -d '{"delete":{"query":"site_id:dgu_organisations%20AND%20name:org-name"}}'
###
@datagovuk.command()
@pass_context
def reindex_organisations(context):
    '''
        Reindex organisations
    '''
    print('=== Reindexing organisations')

    engine = sqlalchemy.create_engine(tk.config.get('sqlalchemy.url'))
    model.init_model(engine)

    orgs = model.Session.query(model.Group) \
                            .filter(model.Group.type == 'organization') \
                            .filter(model.Group.state == u'active') \
                            .order_by(model.Group.name) \
                            .all()

    solr = pysolr.Solr(os.getenv('CKAN_SOLR_URL'), always_commit=True, timeout=10)
    solr.ping()

    existing_organisations = [r.get('name') for r in solr.search("*", fq="(site_id:dgu_organisations)", rows=3000)]
    organisations = []
    counter = 0

    for org in orgs:
        if org.name in existing_organisations:
            continue

        counter += 1
        print(f'{counter} - adding organisation {org.name}')
        data = {
            "site_id": "dgu_organisations",
            "id": org.id,
            "title": org.title,
            "name": org.name,
        }

        org_extras = model.Session.query(model.GroupExtra) \
                        .filter(model.GroupExtra.group_id == org.id) \
                        .filter(model.GroupExtra.state == u'active') \
                        .all()

        for extra in org_extras:
            if extra.key in ['contact-email', 'contact-name', 'foi-name', 'foi-email', 'foi-web']:
                data[f"extras_{extra.key}"] = extra.value

        organisations.append(data)

    if organisations:
        solr.add(organisations)

    results = solr.search("*", fq="(site_id:dgu_organisations)", rows=3000)

    print(f"Added {len(organisations)} organisations, total number = {len(results)}")


def run_command(command):
    try:
        print("=== Running %s" % command)
        subprocess.check_call(command, shell=True)
    except Exception as exception:
        print("=== Error: %s" % exception)
