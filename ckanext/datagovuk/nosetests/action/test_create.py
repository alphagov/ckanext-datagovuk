from io import BytesIO
import os
from datetime import date, datetime
from mock import (call, patch, Mock)
import unittest

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.datagovuk.action.create as create
from ckan.plugins.toolkit import ValidationError

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
        self.context = {
            "session": Mock(),
        }


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


class TestWhenValidOrganogramXlsFile(TestResourceCreate):
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xls")
    fake_resource_create_list = []

    def setUp(self):
        self.data_dict = {
            "package_id": "1234",
            "url": "valid-organogram.xls",
            "upload": create.FakeFieldStorage("valid-organogram.xls", open(self.fixture_path))
        }

        self.pkg_dict = {
            "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
        }

        super(self.__class__, self).setUp()


    @classmethod
    def teardown_class(self):
        helpers.reset_db()

    def fake_resource_create(self, *args):
        TestWhenValidOrganogramXlsFile.fake_resource_create_list.append(args[0])

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.get_action")
    @patch("ckanext.datagovuk.action.create.mimetypes.guess_type")
    @patch("ckanext.datagovuk.action.create.resource_create_core", side_effect=fake_resource_create)
    def test_create_resource_uploads_resource_with_same_timestamp(
        self, mock_resource_create, mock_guess_type, mock_get_action, mock_upload
    ):
        mock_resource_create.mock_resource_create_list = []
        mock_guess_type.return_value = ['application/vnd.ms-excel']

        class MockAction:
            def __init__(self, *args):
                pass

            def get(self, _):
                return '538b857a-64ba-490e-8440-0e32094a28a7'

        mock_get_action.return_value = MockAction

        params = {
            'package_id': factories.Dataset()['id'],
            'url': 'http://data',
            'name': 'A nice resource',
            'upload': self.data_dict
        }

        create.resource_create(self.context, self.data_dict)

        assert mock_resource_create.call_args_list[0][0][1]['timestamp'] == \
            mock_resource_create.call_args_list[1][0][1]['timestamp']
        assert TestWhenValidOrganogramXlsFile.fake_resource_create_list[0]['timestamp'] == \
            TestWhenValidOrganogramXlsFile.fake_resource_create_list[1]['timestamp']

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function_with_original_args(self, original_function, mock_upload):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        for args, _kwargs in original_function.call_args_list:
            self.assertNotEqual(args, (self.context, self.data_dict))

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_twice_with_new_args(self, original_function, mock_upload):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        self.assertEqual(len(original_function.call_args_list), 2)

        senior_args, _kwargs = original_function.call_args_list[0]
        self._assert_resource_created(
            senior_args,
            "Organogram (Senior)",
            "organogram-senior.csv",
        )

        junior_args, _kwargs = original_function.call_args_list[1]
        self._assert_resource_created(
            junior_args,
            "Organogram (Junior)",
            "organogram-junior.csv",
        )

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_returns_the_first_created_resource(self, original_function, mock_upload):
        original_function.side_effect = ["First resource", "Second resource"]

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            created_resource = create.resource_create(self.context, self.data_dict)

        self.assertEqual(created_resource, "First resource")

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_twice_with_given_date(self, original_function, mock_upload):
        self.data_dict = {
            "package_id": "1234",
            "url": "valid-organogram.xls",
            "upload": create.FakeFieldStorage("valid-organogram.xls", open(self.fixture_path)),
            "datafile-date": "2019-05-23"
        }

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        self.assertEqual(len(original_function.call_args_list), 2)

        senior_args, _kwargs = original_function.call_args_list[0]
        self._assert_resource_created(
            senior_args,
            "Organogram (Senior)",
            "organogram-senior.csv",
            "2019-05-23"
        )

        junior_args, _kwargs = original_function.call_args_list[1]
        self._assert_resource_created(
            junior_args,
            "Organogram (Junior)",
            "organogram-junior.csv",
            "2019-05-23"
        )

    def _assert_resource_created(self, args, name, filename, datafile_date=None):
        self.assertEqual(args[0], self.context)

        resource_dict = args[1]
        if not datafile_date:
            today = date.today()
            datafile_date = today.strftime("%Y-%m-%d")

        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

        self.assertEqual(resource_dict["name"], '{} {}'.format(datafile_date, name))
        self.assertEqual(resource_dict["url"], filename)
        self.assertEqual(resource_dict["timestamp"], timestamp_str)

        field_storage = resource_dict["upload"]
        self.assertEqual(field_storage.filename, filename)

        csv = field_storage.file.readlines()
        self.assertGreater(len(csv), 1)


class TestWhenValidOrganogramXlsxFile(TestResourceCreate):
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xlsx")

    def setUp(self):
        self.data_dict = {
            "package_id": "1234",
            "url": "valid-organogram.xlsx",
            "upload": create.FakeFieldStorage("valid-organogram.xlsx", open(self.fixture_path))
        }

        self.pkg_dict = {
            "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
        }

        super(self.__class__, self).setUp()


    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function_with_original_args(self, original_function, mock_upload):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        for args, _kwargs in original_function.call_args_list:
            self.assertNotEqual(args, (self.context, self.data_dict))

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_twice_with_new_args(self, original_function, mock_upload):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        self.assertEqual(len(original_function.call_args_list), 2)

        senior_args, _kwargs = original_function.call_args_list[0]
        self._assert_resource_created(
            senior_args,
            "Organogram (Senior)",
            "organogram-senior.csv",
        )

        junior_args, _kwargs = original_function.call_args_list[1]
        self._assert_resource_created(
            junior_args,
            "Organogram (Junior)",
            "organogram-junior.csv",
        )

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_returns_the_first_created_resource(self, original_function, mock_upload):
        original_function.side_effect = ["First resource", "Second resource"]

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            created_resource = create.resource_create(self.context, self.data_dict)

        self.assertEqual(created_resource, "First resource")

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_twice_with_given_date(self, original_function, mock_upload):
        self.data_dict = {
            "package_id": "1234",
            "url": "valid-organogram.xlsx",
            "upload": create.FakeFieldStorage("valid-organogram.xlsx", open(self.fixture_path)),
            "datafile-date": "2019-05-23"
        }

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        self.assertEqual(len(original_function.call_args_list), 2)

        senior_args, _kwargs = original_function.call_args_list[0]
        self._assert_resource_created(
            senior_args,
            "Organogram (Senior)",
            "organogram-senior.csv",
            "2019-05-23"
        )

        junior_args, _kwargs = original_function.call_args_list[1]
        self._assert_resource_created(
            junior_args,
            "Organogram (Junior)",
            "organogram-junior.csv",
            "2019-05-23"
        )

    def _assert_resource_created(self, args, name, filename, datafile_date=None):
        self.assertEqual(args[0], self.context)

        resource_dict = args[1]
        if not datafile_date:
            today = date.today()
            datafile_date = today.strftime("%Y-%m-%d")

        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

        self.assertEqual(resource_dict["name"], '{} {}'.format(datafile_date, name))
        self.assertEqual(resource_dict["url"], filename)
        self.assertEqual(resource_dict["timestamp"], timestamp_str)

        field_storage = resource_dict["upload"]
        self.assertEqual(field_storage.filename, filename)

        csv = field_storage.file.readlines()
        self.assertGreater(len(csv), 1)

class TestWithInvalidSeniorsInOrganogramExcelFile(TestResourceCreate):
    def setUp(self):
        fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-invalid-senior.xls")

        self.data_dict = {
            "package_id": "1234",
            "url": "invalid-organogram.xls",
            "upload": create.FakeFieldStorage("invalid-organogram.xls", open(fixture_path))
        }

        self.pkg_dict = {
            "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
        }

        super(self.__class__, self).setUp()


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function(self, original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        original_function.assert_not_called()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_rolls_back_the_session(self, _original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        self.context["session"].rollback.assert_called_once()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_raises_a_validation_error(self, _original_function):
        validation_error = None

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError as e:
                validation_error = e

        self.assertNotEqual(validation_error, None)

        expected_error = 'Sheet "(final data) senior-staff" cell S4: Invalid row, as indicated by the red colour in cell S4.'
        self.assertEqual(validation_error.error_dict["message"], [expected_error])

class TestWithInvalidJuniorsInOrganogramExcelFile(TestResourceCreate):
    def setUp(self):
        fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-invalid-junior.xls")

        self.data_dict = {
            "package_id": "1234",
            "url": "invalid-organogram.xls",
            "upload": create.FakeFieldStorage("invalid-organogram.xls", open(fixture_path))
        }

        self.pkg_dict = {
            "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
        }

        super(self.__class__, self).setUp()


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function(self, original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        original_function.assert_not_called()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_rolls_back_the_session(self, _original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        self.context["session"].rollback.assert_called_once()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_raises_a_validation_error(self, _original_function):
        validation_error = None

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError as e:
                validation_error = e

        self.assertNotEqual(validation_error, None)

        expected_errors = [
            'Sheet "(final data) junior-staff" cell K3 etc: Multiple invalid rows. They are indicated by the red colour in column K. Rows affected: 3, 10, 15.',
            'Sheet "(final data) junior-staff" cell D15: You must not leave this cell blank - all junior posts must report to a senior post.',
            'Sheet "(final data) junior-staff" cell D9: Post reporting to senior post "OLD" that is Eliminated',
            'Sheet "(final data) junior-staff" cell D10: Post reporting to unknown senior post "MADEUP"',
        ]
        self.assertEqual(validation_error.error_dict["message"], expected_errors)
