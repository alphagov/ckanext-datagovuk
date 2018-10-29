"""Tests for plugin.py."""
from ckanext.datagovuk.plugin import DatagovukPlugin
from ckanext.datagovuk.action import create, get
import unittest


class TestPlugin(unittest.TestCase):
    def test_plugin_action_mapping(self):
        action_mapping = DatagovukPlugin().get_actions()

        self.assertEqual(action_mapping['resource_create'], create.resource_create)
        self.assertEqual(action_mapping['user_create'], create.user_create)
        self.assertEqual(action_mapping['user_auth'], get.user_auth)
