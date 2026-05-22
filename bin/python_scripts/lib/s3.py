import boto3
import os
import re


class CkanOutputBucket(object):
    def __init__(self):
        bucket_name = os.environ.get('CKAN_OUTPUT_BUCKET_NAME')
        if not bucket_name:
            raise Exception("CKAN_OUTPUT_BUCKET_NAME environment variable is not set")

        s3 = boto3.resource('s3')
        self.bucket = s3.Bucket(bucket_name)

    def get_s3_ls(self, path=None):
        filenames = []
        for obj in self.bucket.objects.all():
            if path and not re.match(path, obj.key):
                continue
            filenames.append(obj.key)
        return filenames

    def upload_to_s3(self, path, s3_path=None):
        if s3_path:
            s3_path = s3_path + "/" + path.split("/")[-1]
        else:
            s3_path = path.split("/")[-1]
        self.bucket.upload_file(path, s3_path)


    def download_from_s3(self, s3_path):
        self.bucket.download_file(s3_path)
