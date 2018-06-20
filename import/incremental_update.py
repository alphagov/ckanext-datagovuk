import argparse
import json
import os
import sys
import gzip
import iso8601

from running_stats import Stats

args = None
stats = Stats()

def process(source, output, timestamp):
    with gzip.open(source, 'rb') as input_f, \
            gzip.open(output, 'wb') as output_f:
        lines = input_f.readlines()
        for line in lines:
            dataset = json.loads(line)
            if dataset['metadata_modified'] >= timestamp:
                output_f.write(line)
                stats.add("Dataset updated", dataset["id"])
            else:
                stats.add("Dataset not updated", dataset["id"])

    print stats
    print 'Written %s' % output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleanup the DGU export')
    parser.add_argument('--source', '-s', dest='source',
                        help='Specify the location of the source file')
    parser.add_argument('--output', '-o', dest='output',
                        help='Specify the location of the output file')
    parser.add_argument('--timestamp', '-t', dest='timestamp',
                        help='Specify the timestamp of the last import')

    args = parser.parse_args()
    if not args.source or not args.output:
        print "Both source and output files are required\n"
        print parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.source):
        print "Source file {0} could not be found\n".format(args.source)
        print parser.print_help()
        sys.exit(1)

    process(args.source, args.output, args.timestamp)
