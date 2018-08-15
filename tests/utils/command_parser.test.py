import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_utils import xplane_commands_txt_parser

__dirname__ = os.path.dirname(__file__)

class TestCommandsTxtParser(XPlaneTestCase):

    # TODO: Checking strings is a terrible way to test this. Every change to the copy will have to change here too.
    # See #329 Create error codes for error messages
    def test_Commands_empty_line(self):
        filepath = os.path.join(__dirname__, "test_commands_txts",  inspect.stack()[0][3].replace("test_", "") + ".txt")
        result = xplane_commands_txt_parser.parse_commands_txt(filepath)
        #print(result)
        self.assertTrue("Line 3 cannot start with whitespace or be empty" in result)

    def test_Commands_line_starts_with_whitespace(self):
        filepath = os.path.join(__dirname__, "test_commands_txts",  inspect.stack()[0][3].replace("test_", "") + ".txt")
        result = xplane_commands_txt_parser.parse_commands_txt(filepath)
        #print(result)
        self.assertTrue("cannot start with whitespace or be empty" in result)

    def test_Commands_no_desc_line_has_trailing_whitespace(self):
        filepath = os.path.join(__dirname__, "test_commands_txts",  inspect.stack()[0][3].replace("test_", "") + ".txt")
        result = xplane_commands_txt_parser.parse_commands_txt(filepath)
        #print(result)
        self.assertTrue("cannot end with whitespace" in result)

    def test_Commands_desc_line_has_trailing_whitespace(self):
        filepath = os.path.join(__dirname__, "test_commands_txts",  inspect.stack()[0][3].replace("test_", "") + ".txt")
        result = xplane_commands_txt_parser.parse_commands_txt(filepath)
        self.assertTrue("cannot end with whitespace" in result)


    def test_Commands_no_description_passes(self):
        #Tests if ``sim/mycommand`` without whitespace and description,
        #because the one in resources has a description for all of them
        filepath = os.path.join(__dirname__, "test_commands_txts", inspect.stack()[0][3].replace("test_", "") + ".txt")
        result = xplane_commands_txt_parser.parse_commands_txt(filepath)
        #3 because it could be easy to it work once on accident
        self.assertEqual(len(result),3) 

    def test_Commands_missing(self):
        result = xplane_commands_txt_parser.parse_commands_txt(
            os.path.join(__dirname__, "test_commands_txts", "Commands_missing.txt"))
        #print(result)
        self.assertEqual("No such file or directory", result) #This comes from Exception's message when the file is missing

    def test_Commands_in_resource_passes(self):
        #We should be able to parse the Commands.txt we ship with!
        #Tests that resource and our code.
        
        result = xplane_commands_txt_parser.parse_commands_txt(
            os.path.join(__dirname__, "..", "..", "io_xplane2blender", "resources", "Commands.txt"))
        self.assertIsInstance(result, list)
        # Anytime we update Commands.txt we'll update this number.
        # A little annoying? Sure, but we'll get it exactly right
        self.assertEqual(len(result), 1914)

runTestCases([TestCommandsTxtParser])
