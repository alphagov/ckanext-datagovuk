import argparse
from os import listdir
from os.path import isfile, join
import sys

from lib.s3 import CkanOutputBucket


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set the location of the reports on s3 and the mount path",
    )
    parser.add_argument(
        "--s3-dir",
        default=".",
        help="s3 directory for CSV report and reindex list (default: root of bucket directory). ",
    )
    parser.add_argument(
        "--mount-path",
        default=".",
        help="mount path for CSV report and reindex list (default: current directory). ",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_files = [f for f in listdir(args.mount_path) if isfile(join(args.mount_path, f))]
    print(f"Report files: {report_files}")

    bucket = CkanOutputBucket()
    
    s3_files = [f.split('/')[-1] for f in bucket.get_s3_ls(path=args.s3_dir)]
    print(f"S3 files: {s3_files}")
    
    new_files = list(set(s3_files) - set(report_files))
    print(f"New files: {new_files}")
    
    return 1 if new_files else 0

if __name__ == "__main__":
    sys.exit(main())
