# -*- coding: utf-8 -*-
import os.path
import string
from pprint import pprint

import pandas as pd
from numpy import nan
import unittest

import ckanext.datagovuk.lib.organogram_xls_splitter as organogram_xls_splitter
from ckanext.datagovuk.lib.organogram_xls_splitter import (
    main, load_xls_and_get_errors, in_sheet_validation_senior_columns,
    load_references, load_senior,
    )

TEST_XLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                               '../data'))

class TestMain(unittest.TestCase):
    maxDiff = None

    def test_sample_senior_valid(self):
        lines = run_etl_on_file_and_return_csv_lines(
            TEST_XLS_DIR + '/sample-valid.xls', date='2016-09-30',
            senior_or_junior='senior')
        self.assertEqual(u'"Post Unique Reference","Name","Grade (or equivalent)","Job Title","Job/Team Function","Parent Department","Organisation","Unit","Contact Phone","Contact E-mail","Reports to Senior Post","Salary Cost of Reports (\xa3)","FTE","Actual Pay Floor (\xa3)","Actual Pay Ceiling (\xa3)","","Professional/Occupational Group","Notes","Valid?"', lines[0])
        self.assertEqual(u'"CEO","Bob Smith","SCS2","Chief Executive","Chief executive","Department for Culture, Media and Sport","Culture Agency","Culture Agency Unit","0300 123 1234","bob.smith@dau.org.uk","XX","1000345","1.00","120000","124999","","","","1"', lines[1])

    def test_sample_junior_valid(self):
        lines = run_etl_on_file_and_return_csv_lines(
            TEST_XLS_DIR + '/sample-valid.xls', date='2016-09-30',
            senior_or_junior='junior')
        self.assertEqual(u'"Parent Department","Organisation","Unit","Reporting Senior Post","Grade","Payscale Minimum (\xa3)","Payscale Maximum (\xa3)","Generic Job Title","Number of Posts in FTE","Professional/Occupational Group"', lines[0])
        self.assertEqual(u'"Department for Culture, Media and Sport","Culture Agency","Culture Agency Unit","CEO","Band A","13564","17594","CAU Assistant","1.00","Operational Delivery"', lines[1])

    def test_sample_senior_invalid(self):
        self.assertRaises(
            EtlError, run_etl_on_file_and_return_csv_lines,
            TEST_XLS_DIR + '/sample-invalid-senior.xls', date='2016-09-30')

    def test_sample_junior_invalid(self):
        self.assertRaises(
            EtlError, run_etl_on_file_and_return_csv_lines,
            TEST_XLS_DIR + '/sample-invalid-junior.xls', date='2016-09-30')


class TestErrorMessages(unittest.TestCase):
    maxDiff = None

    def test_sample_senior_invalid(self):
        senior, junior, errors, warnings, will_display = load_xls_and_get_errors(
            TEST_XLS_DIR + '/sample-invalid-senior.xls')
        self.assertEqual(['Sheet "(final data) senior-staff" cell S4: Invalid row, as indicated by the red colour in cell S4.'],
            errors)

    def test_sample_junior_invalid(self):
        senior, junior, errors, warnings, will_display = load_xls_and_get_errors(
            TEST_XLS_DIR + '/sample-invalid-junior.xls')
        self.assertEqual([
            'Sheet "(final data) junior-staff" cell K3 etc: Multiple invalid rows. They are indicated by the red colour in column K. Rows affected: 3, 10, 15.',
            'Sheet "(final data) junior-staff" cell D15: You must not leave this cell blank - all junior posts must report to a senior post.',
            'Sheet "(final data) junior-staff" cell D9: Post reporting to senior post "OLD" that is Eliminated',
            'Sheet "(final data) junior-staff" cell D10: Post reporting to unknown senior post "MADEUP"'
            ], errors)


SENIOR_COLUMN_HEADINGS = u'Post Unique Reference,Name,Grade (or equivalent),Job Title,Job/Team Function,Parent Department,Organisation,Unit,Contact Phone,Contact E-mail,Reports to Senior Post,Salary Cost of Reports (£),FTE,Actual Pay Floor (£),Actual Pay Ceiling (£),Total Pay (£),Professional/Occupational Group,Notes,Valid?'.split(',')

def senior_row():
    row = [
        'CEO', 'Bob Smith', 'SCS2', 'Chief Executive ',
        'Chief executive', 'Department for Culture Media and Sport',
        'Culture Agency', 'Culture Agency Unit', '0300 123 1234',
        'bob.smith@dau.org.uk', 'XX', '1000345', '1.00', '120000',
        '124999', 'N/A', None, None, None]
    return row

def senior_row_not_in_post():
    row = [
        0, 'N/D', 'SCS2', 'Not in post',
        'N/A', 'Department for Culture Media and Sport',
        'Culture Agency', 'N/A', 'N/A',
        'N/A', 'XX', '1000345', '1.00', '120000',
        '124999', 'N/A', None, None, None]
    return row

def senior_row_vacant():
    row = [
        'CEO', 'Vacant', 'SCS2', 'Chief Executive ',
        'Chief executive', 'Department for Culture Media and Sport',
        'Culture Agency', 'Culture Agency Unit', 'N/A',
        'N/A', 'XX', '1000345', '1.00', '0',
        '0', 'N/A', None, 'the post became vacant on dd/mm/yy', None]
    return row

class TestInSheetValidationSeniorColumns(unittest.TestCase):
    # These tests should match the behaviour of the Excel sheet. Note any
    # improvements that could be made to the validation here, and look to add
    # tighter validation in the etl, but separate to the 'in-sheet' section.

    maxDiff = None

    def test_valid(self):
        errors = in_sheet_validate_senior_row([])
        self.assertEqual(errors, [])

    def test_a_symbol(self):
        # better to have a whitelist
        errors = in_sheet_validate_senior_row_diff([('A', 'RP$FD')])
        self.assertEqual(errors, ['Sheet "sheet" cell A4: You cannot have punctuation/symbols in the "Post Unique Reference" column.'])

    def test_a_dash(self):
        # dash is the only symbol allowed
        errors = in_sheet_validate_senior_row_diff([('A', 'R1-FD')])
        self.assertEqual(errors, [])

    def test_a_xx(self):
        errors = in_sheet_validate_senior_row_diff([('A', 'AXXB')])
        self.assertEqual(errors, ['Sheet "sheet" cell A4: You cannot have "XX" in the "Post Unique Reference" column.'])

    def test_a_space(self):
        errors = in_sheet_validate_senior_row_diff([('A', 'A B')])
        self.assertEqual(errors, ['Sheet "sheet" cell A4: You cannot have spaces in the "Post Unique Reference" column.'])

    def test_a_blank(self):
        # blank value shouldn't be allowed but it is! (if there are other
        # values on the row)
        errors = in_sheet_validate_senior_row_diff([('A', None)])
        self.assertEqual(errors, [])

    def test_a_blank_row(self):
        errors = in_sheet_validate_senior_row([None] * 19)
        self.assertEqual(errors, [])

    def test_b_not_in_post_b_is_a_string(self):
        errors = in_sheet_validate_senior_row_diff([('A', '0'), ('B', 'Bob')])
        self.assertIn('Sheet "sheet" cell B4: Because the "Post Unique Reference" is "0" (individual is paid but not in post) the name must be "N/D".', errors)

    def test_b_not_in_post_b_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('A', '0'), ('B', '')])
        self.assertIn('Sheet "sheet" cell B4: Because the "Post Unique Reference" is "0" (individual is paid but not in post) the name must be "N/D".', errors)

    def test_b_not_in_post_correct(self):
        errors = in_sheet_validate_senior_row_diff([('A', 0), ('B', 'N/D')], row_base='not in post')
        self.assertEqual(errors, [])

    def test_b_is_n_a_and_pay_is_n_a(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/A'), ('P', 'N/A')])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/A" (unless "Total Pay (\xa3)" is 0).'])

    def test_b_is_n_a_and_pay_is_n_d(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/A'), ('P', 'N/D')])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/A" (unless "Total Pay (\xa3)" is 0).'])

    def test_b_is_n_a_and_pay_is_a_string(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/A'), ('P', 'fff')])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/A" (unless "Total Pay (\xa3)" is 0).'])

    def test_b_is_n_a_and_pay_is_1(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/A'), ('P', 1)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/A" (unless "Total Pay (\xa3)" is 0).'])

    def test_b_is_n_a_and_pay_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/A'), ('P', 0)])
        self.assertEqual(errors, [])

    def test_b_is_n_d_and_pay_is_n_a(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/D'), ('P', 'N/A')])
        self.assertEqual(errors, [])

    def test_b_is_n_d_and_pay_is_n_d(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/D'), ('P', 'N/D')])
        self.assertEqual(errors, [])

    def test_b_is_n_d_and_pay_is_a_string(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/D'), ('P', 'fff')])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/D" unless the "Total Pay (\xa3)" is 0 or N/A or N/D. i.e. Someone whose pay must be disclosed must also have their name disclosed (unless they are unpaid).'])

    def test_b_is_n_d_and_pay_is_1(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/D'), ('P', 1)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be "N/D" unless the "Total Pay (\xa3)" is 0 or N/A or N/D. i.e. Someone whose pay must be disclosed must also have their name disclosed (unless they are unpaid).'])

    def test_b_is_n_d_and_pay_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('B', 'N/D'), ('P', 0)])
        self.assertEqual(errors, [])

    def test_b_is_blank_and_pay_is_1(self):
        errors = in_sheet_validate_senior_row_diff([('B', ''), ('P', 0)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be blank.'])

    def test_b_is_blank_and_pay_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('B', ''), ('P', 0)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be blank.'])

    def test_b_is_blank_and_pay_is_a_string(self):
        errors = in_sheet_validate_senior_row_diff([('B', ''), ('P', 0)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be blank.'])

    def test_b_is_blank_and_pay_is_n_a(self):
        errors = in_sheet_validate_senior_row_diff([('B', ''), ('P', 0)])
        self.assertEqual(errors, [u'Sheet "sheet" cell B4: The "Name" cannot be blank.'])

    def test_c_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('C', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell C4: The "Grade (or equivalent)" cannot be blank.'])

    def test_c_is_in_the_list(self):
        errors = in_sheet_validate_senior_row_diff([('C', 'SCS1')])
        self.assertEqual(errors, [])

    def test_c_is_not_in_the_list(self):
        errors = in_sheet_validate_senior_row_diff([('C', 'King')])
        self.assertEqual(errors, [u'Sheet "sheet" cell C4: The "Grade (or equivalent)" must be from the standard list: "SCS4", "SCS3", "SCS2", "SCS1A", "SCS1", "OF-9", "OF-8", "OF-7", "OF-6".'])

    def test_d_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('D', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell D4: The "Job Title" cannot be blank.'])

    def test_d_is_not_in_post_correct(self):
        errors = in_sheet_validate_senior_row_diff([('D', 'Not in post'), ('A', 0)], row_base='not in post')
        self.assertEqual(errors, [])

    def test_d_is_not_in_post_but_id_isnt_0(self):
        errors = in_sheet_validate_senior_row_diff([('D', 'Not in post'), ('A', 'CEO')])
        self.assertIn(u'Sheet "sheet" cell D4: The "Job Title" can only be "Not in post" if the "Post Unique Reference" is "0" (individual is paid but not in post).', errors)

    def test_d_is_in_post_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('D', 'Director'), ('A', 0)])
        self.assertIn(u'Sheet "sheet" cell D4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Job Title" must be "Not in post".', errors)

    def test_d_is_in_post_but_id_is_string_0(self):
        errors = in_sheet_validate_senior_row_diff([('D', 'Director'), ('A', '0')])
        self.assertIn(u'Sheet "sheet" cell D4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Job Title" must be "Not in post".', errors)

    def test_e_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('E', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell E4: The "Job/Team Function" cannot be blank.'])

    def test_e_is_not_in_post_but_id_isnt_0(self):
        errors = in_sheet_validate_senior_row_diff([('E', 'N/A'), ('A', 'CEO')])
        self.assertIn(u'Sheet "sheet" cell E4: The "Job/Team Function" can only be "N/A" if the "Post Unique Reference" is "0" (individual is paid but not in post).', errors)

    def test_e_is_in_post_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('E', 'Director'), ('A', 0)])
        self.assertIn(u'Sheet "sheet" cell E4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Job/Team Function" must be "N/A".', errors)

    def test_e_is_in_post_but_id_is_string_0(self):
        errors = in_sheet_validate_senior_row_diff([('E', 'Director'), ('A', '0')])
        # this should work the same as the int 0 - it is a failing of the spreadsheet
        self.assertNotIn(u'Job/Team Function', '\n'.join(errors))

    def test_g_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('G', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell G4: The "Organisation" must be disclosed - it cannot be blank or "N/D".'])

    def test_g_is_nd(self):
        errors = in_sheet_validate_senior_row_diff([('G', 'N/D')])
        self.assertEqual(errors, [u'Sheet "sheet" cell G4: The "Organisation" must be disclosed - it cannot be blank or "N/D".'])

    def test_h_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('H', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell H4: The "Unit" must be disclosed - it cannot be blank or "N/D".'])

    def test_h_is_in_post_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('H', 'Culture Agency Unit'), ('A', 0)])
        self.assertIn(u'Sheet "sheet" cell H4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Unit" must be "N/A".', errors)

    def test_h_is_in_post_but_id_is_string_0(self):
        errors = in_sheet_validate_senior_row_diff([('H', 'Culture Agency Unit'), ('A', '0')])
        # this should work the same as the int 0 - it is a failing of the spreadsheet
        self.assertNotIn(u'Unit', '\n'.join(errors))

    def test_h_is_not_in_post_correct(self):
        errors = in_sheet_validate_senior_row_diff([('H', 'N/A'), ('A', 0)], row_base='not in post')
        self.assertEqual(errors, [])

    def test_i_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('I', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell I4: The "Contact Phone" must be supplied - it cannot be blank.'])

    def test_i_is_not_in_post_correct(self):
        errors = in_sheet_validate_senior_row_diff([('I', 'N/A'), ('A', 0)], row_base='not in post')
        self.assertEqual(errors, [])

    def test_i_is_in_post_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('I', 'Bob'), ('A', 0)], row_base='not in post')
        self.assertEqual(errors, [u'Sheet "sheet" cell I4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Contact Phone" must be "N/A".'])

    def test_i_vacant_correct(self):
        errors = in_sheet_validate_senior_row_diff([('I', 'N/A'), ('A', 'Vacant')], row_base='vacant')
        self.assertEqual(errors, [])

    def test_i_given_but_name_is_vacant(self):
        errors = in_sheet_validate_senior_row_diff([('I', '012345'), ('B', 'Vacant')], row_base='vacant')
        self.assertEqual(errors, [u'Sheet "sheet" cell I4: Because the "Name" is "Vacant" or "Eliminated", the "Contact Phone" must be "N/A".'])

    def test_i_given_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('I', '012345')], row_base='not in post')
        self.assertEqual(errors, [u'Sheet "sheet" cell I4: Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Contact Phone" must be "N/A".'])

    def test_i_na_but_id_is_normal(self):
        errors = in_sheet_validate_senior_row_diff([('I', 'N/A')])
        self.assertEqual(errors, [u'Sheet "sheet" cell I4: The "Contact Phone" can only be "N/A" if the "Post Unique Reference" is "0" (individual is paid but not in post) or the "Name" is "Vacant".'])

    def test_j_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('J', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell J4: The "Contact E-mail" must be supplied - it cannot be blank.'])

    def test_j_vacant_correct(self):
        errors = in_sheet_validate_senior_row_diff([('J', 'N/A')], row_base='vacant')
        self.assertEqual(errors, [])

    def test_j_na_but_in_post(self):
        errors = in_sheet_validate_senior_row_diff([('J', 'N/A')])
        self.assertEqual(errors, [u'Sheet "sheet" cell J4: The "Contact E-mail" can only be "N/A" if the "Post Unique Reference" is "0" (individual is paid but not in post).'])

    def test_j_given_but_name_is_vacant(self):
        errors = in_sheet_validate_senior_row_diff([('J', 'a@b.com')], row_base='vacant')
        self.assertEqual(errors, [])
        # should really be an error like: u'Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Contact E-mail" must be "N/A". See sheet "sheet" cell J4'])

    def test_j_given_but_id_is_0(self):
        errors = in_sheet_validate_senior_row_diff([('J', 'a@b.com')], row_base='not in post')
        self.assertEqual(errors, [])
        # should really be an error like: u'Because the "Post Unique Reference" is "0" (individual is paid but not in post), the "Contact E-mail" must be "N/A". See sheet "sheet" cell J4'])

    def test_k_is_blank(self):
        errors = in_sheet_validate_senior_row_diff([('K', '')])
        self.assertEqual(errors, [u'Sheet "sheet" cell K4: The "Reports to Senior Post" value must be supplied - it cannot be blank.'])

    def test_k_xx_correct(self):
        errors = in_sheet_validate_senior_row_diff([('K', 'XX')])
        self.assertEqual(errors, [])

    def test_k_unknown(self):
        errors = in_sheet_validate_senior_row_diff([('K', 'unknown')])
        self.assertEqual(errors, [u'Sheet "sheet" cell K4: The "Reports to Senior Post" value must match one of the values in "Post Unique Reference" (column A) or be "XX" (which is a top level post - reports to no-one in this sheet).'])

    def test_k_known_correct(self):
        errors = in_sheet_validate_senior_row_diff([('K', 'CEO')])
        self.assertEqual(errors, [])

    def test_k_known_but_wrong_case(self):
        errors = in_sheet_validate_senior_row_diff([('K', 'ceo')])
        self.assertEqual(errors, [])
        # Should be an error!

    def test_k_wildcard(self):
        errors = in_sheet_validate_senior_row_diff([('K', '*')])
        self.assertEqual(errors, [])
        # Should be an error!

def in_sheet_validate_senior_row_diff(row_updates, row_base=None):
    if row_base is None:
        row = senior_row()
    elif row_base == 'not in post':
        row = senior_row_not_in_post()
    elif row_base == 'vacant':
        row = senior_row_vacant()
    else:
        raise NotImplementedError()

    for col, value in row_updates:
        col_index = string.ascii_uppercase.index(col.upper())
        row[col_index] = value
    return in_sheet_validate_senior_row(row)

references = None

def in_sheet_validate_senior_row(row):
    df = pd.DataFrame([[''] * 19] + [[''] * 19] + [row],
                      columns=SENIOR_COLUMN_HEADINGS)
    errors = []
    validation_errors = []
    global references
    if references is None:
        references = load_references(TEST_XLS_DIR + '/sample-valid.xls',
                                     errors, validation_errors)
    assert not errors
    assert not validation_errors
    in_sheet_validation_senior_columns(df.loc[2], df, errors, 'sheet', references)
    return errors

class MockArgs(object):
    date = None
    date_from_filename = False


def run_etl_on_file(input_xls_filepath, date='2011-03-31'):
    organogram_xls_splitter.args = MockArgs()
    organogram_xls_splitter.args.date = date
    ret = main(input_xls_filepath, '/tmp/')
    if ret is None:
        raise EtlError()
    senior_filepath, junior_filepath, senior, junior = ret
    return senior_filepath, junior_filepath, senior, junior


def run_etl_on_file_and_return_csv_lines(input_xls_filepath, date='2011-03-31',
                                         senior_or_junior='both'):
    senior_filepath, junior_filepath, senior, junior = \
        run_etl_on_file(input_xls_filepath, date=date)
    if senior_or_junior == 'senior':
        return csv_read(senior_filepath)
    elif senior_or_junior == 'junior':
        return csv_read(junior_filepath)
    elif senior_or_junior == 'both':
        return csv_read(senior_filepath), csv_read(junior_filepath)

def csv_read(filepath):
    with open(filepath, 'rb') as f:
        return f.read().strip().decode('utf8').split('\n')

class EtlError(Exception):
    pass

class TestLoadSenior(unittest.TestCase):
    maxDiff = None

    def test_sample_1(self):
        errors = []
        validation_errors = []
        references = {}
        df = load_senior(TEST_XLS_DIR + '/sample-valid.xls',
                         errors, validation_errors, references)
        # need to replace nan with None because: nan != nan
        row = df.where(pd.notnull(df), None).iloc[1].to_dict()
        pprint(row)
        self.assertEqual(
            row,
            {u'': '',
             u'Actual Pay Ceiling (\xa3)': '69999',
             u'Actual Pay Floor (\xa3)': '65000',
             u'Contact E-mail': u'nigel.winters@dau.org.uk',
             u'Contact Phone': u'0300 123 1235',
             u'FTE': 1.0,
             u'Grade (or equivalent)': u'SCS1',
             u'Job Title': u'Resources Director',
             u'Job/Team Function': u'Providing professional support to managers and staff on all HR, Finance, Procurement, ICT and premises matters',
             u'Name': u'Nigel Winters',
             u'Notes': None,
             u'Organisation': u'Culture Agency',
             u'Parent Department': u'Department for Culture, Media and Sport',
             u'Post Unique Reference': 'RPCFD',
             u'Professional/Occupational Group': None,
             u'Reports to Senior Post': 'CEO',
             u'Salary Cost of Reports (\xa3)': '124843',
             u'Unit': u'Culture Agency Unit',
             u'Valid?': 1}
             )

    def test_phone_n_a(self):
        errors = []
        validation_errors = []
        references = {}
        df = load_senior(TEST_XLS_DIR + '/sample-mix.xls',
                         errors, validation_errors, references)
        row = df.where(pd.notnull(df), None).iloc[3].to_dict()
        pprint(row)
        self.assertEqual(row['Contact Phone'], 'N/A')

    def test_phone_blank(self):
        errors = []
        validation_errors = []
        references = {}
        df = load_senior(TEST_XLS_DIR + '/sample-mix.xls',
                         errors, validation_errors, references)
        row = df.where(pd.notnull(df), None).iloc[4].to_dict()
        pprint(row)
        self.assertEqual(row['Contact Phone'], None)

    def test_email_n_a(self):
        errors = []
        validation_errors = []
        references = {}
        df = load_senior(TEST_XLS_DIR + '/sample-mix.xls',
                         errors, validation_errors, references)
        row = df.where(pd.notnull(df), None).iloc[3].to_dict()
        pprint(row)
        self.assertEqual(row['Contact E-mail'], 'N/A')

    def test_email_blank(self):
        errors = []
        validation_errors = []
        references = {}
        df = load_senior(TEST_XLS_DIR + '/sample-mix.xls',
                         errors, validation_errors, references)
        row = df.where(pd.notnull(df), None).iloc[4].to_dict()
        pprint(row)
        self.assertEqual(row['Contact E-mail'], None)
