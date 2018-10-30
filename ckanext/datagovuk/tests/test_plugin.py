"""Tests for plugin.py."""
from ckanext.datagovuk.plugin import DatagovukPlugin
import ckanext.datagovuk.action.create as create
import ckanext.datagovuk.action.get as get
from nose.tools import assert_equal

def test_plugin_action_mapping():
    action_mapping = DatagovukPlugin().get_actions()

    assert_equal(action_mapping['resource_create'], create.resource_create)
    assert_equal(action_mapping['user_create'], create.user_create)
    assert_equal(action_mapping['user_auth'], get.user_auth)
