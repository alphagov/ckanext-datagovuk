import os
import sys

# this is so the `lib` package as a top-level package (e.g. `from lib.s3 import
# CkanOutputBucket` works in check_links.py, the same way the scripts are run 
# from this directory) works in pytest, otherwise we get import error when 
# running tests
sys.path.insert(0, os.path.dirname(__file__))
