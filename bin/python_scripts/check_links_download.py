import sys

from lib.s3 import CkanOutputBucket


def main() -> int:
    bucket = CkanOutputBucket()
    # check_links/ should match the path in the s3 ckan-output bucket
    for file_path in bucket.get_s3_ls(path="check_links/"):
        # /check_links should match the mount path for check-links-output-nginx-deployment.yaml in govuk-dgu-charts repo
        bucket.download_from_s3(file_path, target_dir="/check_links")
        print(f"downloaded {file_path} from S3 bucket {bucket.bucket.name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
