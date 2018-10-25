import unittest
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
