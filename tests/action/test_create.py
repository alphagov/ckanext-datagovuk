from io import BytesIO, StringIO
import os
from datetime import date, datetime
from mock import (call, patch, Mock)
import pytest
import unittest

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.datagovuk.action.create as create
from ckan.plugins.toolkit import ValidationError


@pytest.fixture()
def mock_field_storage():
    file_stream = StringIO("12345")
    file_stream.seek(3)
    return create.FakeFieldStorage("test_filename.txt", file_stream)


class TestFakeFieldStorage:
    def test_always_sets_the_name_to_upload(self, mock_field_storage):
        assert mock_field_storage.name == "upload"

    def test_stores_the_provided_filename(self, mock_field_storage):
        assert mock_field_storage.filename == "test_filename.txt"

    def test_stores_the_provided_file_or_stream_and_rewinds_it(self, mock_field_storage):
        assert mock_field_storage.file.read() == "12345"


class TestResourceCreate:
    context = {
        "session": Mock(),
    }


class TestWhenNotExcelFile(TestResourceCreate):
    data_dict = {
        "url": "file.jpg",
    }


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_with_original_args(self, original_function):
        create.resource_create(self.context, self.data_dict)
        original_function.assert_called_once_with(self.context, self.data_dict)


class TestWhenExcelButNotOrganogram(TestResourceCreate):
    data_dict = {
        "package_id": "1234",
        "url": "file.xls",
    }

    pkg_dict = {
        "schema-vocabulary": "not-an-organogram-id",
    }


    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_with_original_args(self, original_function):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        original_function.assert_called_once_with(self.context, self.data_dict)


@pytest.fixture
def mock_data():
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xls")
    TestWhenValidOrganogramXlsFile.data_dict = {
        "package_id": "1234",
        "url": "valid-organogram.xls",
        "upload": create.FakeFieldStorage("valid-organogram.xls", open(fixture_path, 'r'))
    }

    TestWhenValidOrganogramXlsFile.pkg_dict = {
        "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
    }


@pytest.mark.usefixtures("clean_db")
class TestWhenValidOrganogramXlsFile(TestResourceCreate):
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xls")
    fake_resource_create_list = []

    def fake_resource_create(self, *args):
        TestWhenValidOrganogramXlsFile.fake_resource_create_list.append(args[0])

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.get_action")
    @patch("ckanext.datagovuk.action.create.mimetypes.guess_type")
    @patch("ckanext.datagovuk.action.create.resource_create_core", side_effect=fake_resource_create)
    def test_create_resource_uploads_resource_with_same_timestamp(
        self, mock_resource_create, mock_guess_type, mock_get_action, mock_upload, mock_data
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
            assert args != (self.context, self.data_dict)

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_calls_the_original_function_twice_with_new_args(self, original_function, mock_upload):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        assert len(original_function.call_args_list) == 2

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

        assert created_resource == "First resource"

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

        assert len(original_function.call_args_list) == 2

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
        assert args[0] == self.context

        resource_dict = args[1]
        if not datafile_date:
            today = date.today()
            datafile_date = today.strftime("%Y-%m-%d")

        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

        assert resource_dict["name"] == '{} {}'.format(datafile_date, name)
        assert resource_dict["url"] == filename
        assert resource_dict["timestamp"] == timestamp_str

        field_storage = resource_dict["upload"]
        assert field_storage.filename == filename

        csv = field_storage.file.readlines()
        assert len(csv) > 1


@pytest.fixture
def mock_xlsx_data():
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xlsx")
    TestWhenValidOrganogramXlsxFile.data_dict = {
        "package_id": "1234",
        "url": "valid-organogram.xls",
        "upload": create.FakeFieldStorage("valid-organogram.xlsx", open(fixture_path, 'r'))
    }

    TestWhenValidOrganogramXlsxFile.pkg_dict = {
        "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
    }


class TestWhenValidOrganogramXlsxFile(TestResourceCreate):
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-valid.xlsx")

    @patch("ckanext.datagovuk.action.create.upload_resource_to_s3")
    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function_with_original_args(self, original_function, mock_upload, mock_xlsx_data):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict
            create.resource_create(self.context, self.data_dict)

        for args, _kwargs in original_function.call_args_list:
            assert args != (self.context, self.data_dict)

    def _assert_resource_created(self, args, name, filename, datafile_date=None):
        assert args[0] == self.context

        resource_dict = args[1]
        if not datafile_date:
            today = date.today()
            datafile_date = today.strftime("%Y-%m-%d")

        timestamp = datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")

        assert resource_dict["name"] == '{} {}'.format(datafile_date, name)
        assert resource_dict["url"] == filename
        assert resource_dict["timestamp"] == timestamp_str

        field_storage = resource_dict["upload"]
        assert field_storage.filename == filename

        csv = field_storage.file.readlines()
        assert len(csv) > 1


@pytest.fixture
def mock_invalid_senior():
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-invalid-senior.xls")

    TestWithInvalidSeniorsInOrganogramExcelFile.data_dict = {
        "package_id": "1234",
        "url": "invalid-organogram.xls",
        "upload": create.FakeFieldStorage("invalid-organogram.xls", open(fixture_path))
    }

    TestWithInvalidSeniorsInOrganogramExcelFile.pkg_dict = {
        "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
    }


class TestWithInvalidSeniorsInOrganogramExcelFile:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.context = {
            "session": Mock(),
        }

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function(self, original_function, mock_invalid_senior):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        original_function.assert_not_called()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_rolls_back_the_session(self, _original_function, mock_invalid_senior):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        self.context["session"].rollback.assert_called_once()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_raises_a_validation_error(self, _original_function, mock_invalid_senior):
        validation_error = None

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError as e:
                validation_error = e

        assert validation_error

        expected_error = 'Sheet "(final data) senior-staff" cell S4: Invalid row, as indicated by the red colour in cell S4.'
        assert validation_error.error_dict["message"] == [expected_error]


@pytest.fixture
def mock_invalid_junior():
    fixture_path = os.path.join(os.path.dirname(__file__), "../data/sample-invalid-junior.xls")

    TestWithInvalidJuniorsInOrganogramExcelFile.data_dict = {
        "package_id": "1234",
        "url": "invalid-organogram.xls",
        "upload": create.FakeFieldStorage("invalid-organogram.xls", open(fixture_path))
    }

    TestWithInvalidJuniorsInOrganogramExcelFile.pkg_dict = {
        "schema-vocabulary": "538b857a-64ba-490e-8440-0e32094a28a7",
    }


class TestWithInvalidJuniorsInOrganogramExcelFile:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.context = {
            "session": Mock(),
        }

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_does_not_call_the_original_function(self, original_function, mock_invalid_junior):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass

        original_function.assert_not_called()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_rolls_back_the_session(self, _original_function, mock_invalid_junior):
        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError:
                pass
        self.context["session"].rollback.assert_called_once()

    @patch("ckanext.datagovuk.action.create.resource_create_core")
    def test_raises_a_validation_error(self, _original_function, mock_invalid_junior):
        validation_error = None

        with patch("ckanext.datagovuk.action.create.get_action") as mock_get_action:
            mock_get_action.return_value = lambda *_args: self.pkg_dict

            try:
                create.resource_create(self.context, self.data_dict)
            except ValidationError as e:
                validation_error = e

        assert validation_error

        expected_errors = [
            'Sheet "(final data) junior-staff" cell K3 etc: Multiple invalid rows. They are indicated by the red colour in column K. Rows affected: 3, 10, 15.',
            'Sheet "(final data) junior-staff" cell D15: You must not leave this cell blank - all junior posts must report to a senior post.',
            'Sheet "(final data) junior-staff" cell D9: Post reporting to senior post "OLD" that is Eliminated',
            'Sheet "(final data) junior-staff" cell D10: Post reporting to unknown senior post "MADEUP"',
        ]
        assert set(validation_error.error_dict["message"]) == set(expected_errors)
