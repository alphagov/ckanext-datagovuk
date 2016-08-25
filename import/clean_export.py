"""
As the export from DGU does not insert directly back into a clean CKAN, we need to
clean up the export by removing fields that confuse CKAN.

You can run this script by passing the "-s datasets.jsonl.gz" parameter and it will
generate a new jsonl.gz in the same folder as the source file.
"""
import argparse
import json
import os
import sys
import gzip

def process(source, output):
    with gzip.open(source, 'rb') as input_f, gzip.open(output, 'wb') as output_f:
        lines = input_f.readlines()
        for line in lines:
            new_entry = clean_and_write(line)
            output_f.write(new_entry + "\n")

def clean_and_write(entry):
    dataset = json.loads(entry)

    for val in ['individual_resources', 'additional_resources', 'timeseries_resources',
                'tags', 'schema', 'codelist']:
        if val in dataset:
            del dataset[val]

    return json.dumps(dataset)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleanup the DGU export')
    parser.add_argument('--source', '-s', dest='source',
                        help='Specify the location of the source file')
    parser.add_argument('--output', '-o', dest='output',
                        help='Specify the location of the output file')

    args = parser.parse_args()
    if not args.source or not args.output:
        print "Both source and output files are required\n"
        print parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.source):
        print "Source file {0} could not be found\n".format(args.source)
        print parser.print_help()
        sys.exit(1)

    process(args.source, args.output)

