"""Tests for DGU monkey patches of CKAN."""
from mock import patch
from webob.multidict import MultiDict

from ckan import model
import ckan.lib.cli
from ckan.tests.lib.test_cli import paster
from ckan.tests import factories, helpers
from ckanext.datagovuk.tests.db_test import DBTest


class TestLogin(DBTest):
    def test_validate_password__ok(self):
        user_dict = factories.User(password='helloworld')
        user = model.User.get(user_dict['id'])

        self.assertTrue(user.validate_password('helloworld'))

    def test_validate_password__wrong_password(self):
        user_dict = factories.User(password='helloworld')
        user = model.User.get(user_dict['id'])

        self.assertFalse(user.validate_password('goodbyeworld'))

    def test_validate_password__drupal_ok(self):
        # Drupal hash
        # co@prod2 ~ () $ cd /var/www/drupal/dgud7/current; drush php-eval "include_once DRUPAL_ROOT . '/includes/password.inc'; include_once DRUPAL_ROOT . '/includes/bootstrap.inc'; echo user_hash_password('pass');"
        # $S$D2B6/Pd7ZJNIs9XL4X0QjY2mC4nwZz9pIYe8P3TXzuE9c2dLIytw
        user_dict = factories.User()
        drupal_hash = '$S$D2B6/Pd7ZJNIs9XL4X0QjY2mC4nwZz9pIYe8P3TXzuE9c2dLIytw'
        model.Session.execute(
            'update public.user set password = :pw where id = :id',
            {'pw': drupal_hash, 'id': user_dict['id']})
        model.Session.commit()
        model.Session.remove()

        user = model.User.get(user_dict['id'])
        self.assertTrue(user.validate_password('pass'))


class TestSetPass(DBTest):
    def setup(self):
        helpers.reset_db()

    @patch('ckan.lib.cli.UserCmd.password_prompt', return_value='newpassword')
    @patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
    def test_setpass_sends_email_alert_to_user(self, mock_mailer, mock_password_prompt):
        user_dict = factories.User(password='hello123')

        user_cmd = ckan.lib.cli.UserCmd('test')
        user_cmd.args =['setpass', user_dict['name']]

        user_cmd.setpass()

        assert mock_mailer.called
        args, kwargs = mock_mailer.call_args
        assert args[0].id == user_dict['id']
        assert args[0].email == user_dict['email']
        assert args[1] == 'Your data.gov.uk publisher password has changed'
        assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"


class TestPackageSearchQuery:
    @patch('ckan.lib.search.query.PackageSearchQuery.original_run',
        return_value={"count": 1, "results": [{"key": "value"}]})
    @patch('ckanext.datagovuk.ckan_patches.logger.warn')
    def test_package_search_run_does_not_block_unmatched_tags(self, mock_logger, mock_package_search_query):
        query = ckan.lib.search.query.PackageSearchQuery()

        q = {
               'q': '+capacity:public',
                'fl': 'groups', 'facet.field': ['groups', 'owner_org'],
                'facet.limit': -1, 'rows': 1
            }

        response = query.run(q)
        assert mock_package_search_query.called
        assert response == {'count': 1, 'results': [{"key": "value"}]}

        assert not mock_logger.called

    @patch('ckan.lib.search.query.PackageSearchQuery.original_run',
        return_value={"count": 1, "results": [{"key": "value"}]})
    @patch('ckanext.datagovuk.ckan_patches.logger.warn')
    def test_package_search_run_blocks_matched_tags(self, mock_logger, mock_package_search_query):
        query = ckan.lib.search.query.PackageSearchQuery()

        q = MultiDict(
            [
                ('fl', u'{!xmlparser v=\'<!DOCTYPE a SYSTEM "http://test:1000/xxe"><a></a>\'}'),
                ('q', u'extras_harvest_source_id:["" TO *]and dataset_type:dataset'), 
                ('fq', '+capacity:public')
            ]
        )

        response = query.run(q)
        assert response == {'count': 0, 'results': []}

        assert mock_logger.called
        assert mock_logger.call_args[0][0] == 'DGU search blocked: %r'
        assert mock_logger.call_args[0][1] == u'{!xmlparser v=\'<!DOCTYPE a SYSTEM "http://test:1000/xxe"><a></a>\'}'

        assert not mock_package_search_query.called

    @patch('ckan.lib.search.query.PackageSearchQuery.original_run',
        return_value={"count": 1, "results": [{"key": "value"}]})
    @patch('ckanext.datagovuk.ckan_patches.logger.warn')
    def test_package_search_run_blocks_matched_tags_uppercase(self, mock_logger, mock_package_search_query):
        query = ckan.lib.search.query.PackageSearchQuery()

        q = MultiDict(
            [
                ('fl', u'{!XMLPARSER v=\'<!DOCTYPE a SYSTEM "http://test:1000/xxe"><a></a>\'}'),
                ('q', u'extras_harvest_source_id:["" TO *]and dataset_type:dataset'), 
                ('fq', '+capacity:public')
            ]
        )

        response = query.run(q)
        assert response == {'count': 0, 'results': []}

        assert mock_logger.called
        assert mock_logger.call_args[0][0] == 'DGU search blocked: %r'
        assert mock_logger.call_args[0][1] == u'{!XMLPARSER v=\'<!DOCTYPE a SYSTEM "http://test:1000/xxe"><a></a>\'}'

        assert not mock_package_search_query.called

    @patch('ckan.lib.search.query.PackageSearchQuery.original_run',
        return_value={"count": 1, "results": [{"key": "value"}]})
    @patch('ckanext.datagovuk.ckan_patches.logger.warn')
    def test_package_search_run_does_not_block_partially_matched_tags(self, mock_logger, mock_package_search_query):
        query = ckan.lib.search.query.PackageSearchQuery()

        q = MultiDict(
            [
                ('fl', u'{!xmlparser}'),
                ('q', u'extras_harvest_source_id:["" TO *]and dataset_type:dataset'),
                ('fq', '+capacity:public')
            ]
        )

        response = query.run(q)
        assert mock_package_search_query.called
        assert response == {'count': 1, 'results': [{"key": "value"}]}

        assert not mock_logger.called
