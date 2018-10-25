import unittest
from mock import patch
import ckanext.datagovuk.action.create as create
from io import BytesIO

class TestFakeFieldStorage(unittest.TestCase):
    def setUp(self):
        file_stream = BytesIO("12345")
        file_stream.seek(3)
        self.field_storage = create.FakeFieldStorage("test_filename.txt", file_stream)

    def test_always_sets_the_name_to_upload(self):
        self.assertEqual(self.field_storage.name, "upload")

    def test_stores_the_provided_filename(self):
        self.assertEqual(self.field_storage.filename, "test_filename.txt")

    def test_stores_the_provided_file_or_stream_and_rewinds_it(self):
        self.assertEqual(self.field_storage.file.read(), "12345")


class TestResourceCreate(unittest.TestCase):
    def setUp(self):
        self.context = {}


class TestWhenNotExcelFile(TestResourceCreate):
    def setUp(self):
        self.data_dict = {
            "url": "file.jpg",
        }

        super(self.__class__, self).setUp()


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_with_original_args(self, original_function):
        create.resource_create(self.context, self.data_dict)
        original_function.assert_called_once_with(self.context, self.data_dict)


class TestWhenExcelButNotOrganogram(TestResourceCreate):
    def setUp(self):
        self.data_dict = {
            "package_id": "1234",
            "url": "file.xls",
        }

        self.pkg_dict = {
            "schema-vocabulary": "not-an-organogram-id",
        }

        super(self.__class__, self).setUp()


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_with_original_args(self, original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)
            original_function.assert_called_once_with(self.context, self.data_dict)
