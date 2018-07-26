import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_utils import xplane_datarefs_txt_parser

__dirname__ = os.path.dirname(__file__)

class TestDatarefTxtParser(XPlaneTestCase):
    # TODO: Checking strings is a terrible way to test this. Every change to the copy will have to change here too.
    # See #329 Create error codes for error messages
    def test_DataRefs_empty(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("File has no datarefs in it" in result)

    def test_DataRefs_header_completely_wrong(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("File format line is invalid" in result)

    def test_DataRefs_header_file_version_is_one(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("File version number" in result)


    def test_DataRefs_header_xp_version_is_wrong(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("File format line is invalid" in result)

    def test_DataRefs_invalid_array_type(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("must be formatted as 'datatype[index]', where datatype is a valid type and index is one or more digits" in result)

    def test_DataRefs_invalid_array_type_index_wrong(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("must be one or more digits" in result)

    def test_DataRefs_invalid_iswritable(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("must be 'y' or 'n'" in result)

    def test_DataRefs_invalid_type_wrong(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("must be an int, float, double, or byte" in result)

    def test_DataRefs_line_starts_with_whitespace(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("cannot start with whitespace" in result)

    def test_DataRefs_no_blank_second_line(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("Does not have a blank line for its second line" in result)

    def test_DataRefs_no_datarefs_in_it(self):
        filepath = os.path.join(__dirname__,"test_datarefs_txts", inspect.stack()[0][3].replace("test_","") + ".txt")
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(filepath)
        #print(result)
        self.assertTrue("File has no datarefs in it" in result)

    def test_DataRefs_missing(self):
        result = xplane_datarefs_txt_parser.parse_datarefs_txt(os.path.join(__dirname__,"test_datarefs_txts","DataRefs_missing.txt"))
        #print(result)
        self.assertEqual("No such file or directory",result) #This comes from Exception's message when the file is missing


runTestCases([TestDatarefTxtParser])
