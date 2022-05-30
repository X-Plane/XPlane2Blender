#TI To use
#TI 1. Copy and rename to match your blend files name - "name.test.py"
#TI 2. Delete all lines that begin with #TI, like this one
#TI    (otherwise it will NOT pass code review)
#TI 3. Rename as needed, following conventions
#TI
#TI Guidelines for .test.blend files
#TI (Developed after many many many tests made)
#TI - An active text window with text block called "Unit Test Overview" should be shown featuring an outline of what the test is for and what the names, data, etc means
#TI - The textblock "Unit Test Overview" should start with the header "Unit Test Overview", followed by a blank line and text starting after 4 spaces
#TI - The textblock should be manually word wrapped so the contents don't change when you adjust the size of the window
#TI - Layers are alphabetical, start with "test", and take their names from object names
#TI - Use "01_","02_", etc to enforce alphabetical layer order, rather than abusing a thesaurus
#TI - The console should also be open with the code "bpy.ops.export.xplane_obj()" typed. It should be the focused window allowing a person to open the .blend file and press enter
#TI - Scene > Advanced Settings > Debug (and Object > Advanced Options > Debug for every OBJ Setting) turned on
#TI - In Blender file, select some useful object to immediatly see, or select the last object in the outliner
#TI (Nearly entirely arbitrary: consistency is generally useful someday)
import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent

class TestBlendFileNameCamelCaseNoPunctuation(XPlaneTestCase):
    #TI as per unittest requirements, all test methods must start with "test_"
    def test_fixture_or_layer_name_snake_case(self)->None:
        #TI Example of switching scenes. If using multiple scenes in a test
        #TI every test must start with specifying the scene, as these can run
        #TI in any order
        #bpy.context.window.scene = bpy.data.scenes["Scene_"]

        #TI Example of whitebox/API testing using an xplane_type
        #TI Import some io_xplane2blender module, call __init__/use API and test results
        #TI from io_xplane2blender.xplane_types import xplane_example
        #TI example = xplane_ex.XPlaneExampleType("My Name")
        #TI self.assertTrue(example.isValid())
        #from io_xplane2blender.xplane_types import xplane_

        #TI Testing the results of an export without a fixture
        #TI out is the content for the .obj file
        #out = self.exportExportableRoot("")

        #TI Example of expecting a failure
        #TI (Note: This doesn't test specific errors)
        #TI logger is cleared afterward
        #self.assertLoggerErrors(1)

        #TI Unless necessary, keep OBJ, object, and test method (and order) names consistent
        #TI It is so much easier to understand and debug a test that way!
        #TI There is even an operator in the Plugin Dev section to help

        #TI This allows you to use the method name to match the file name
        #filepath = __dirname__/Path("fixtures", Path(f"{inspect.stack()[0].function}.obj"))

        #TI or, with a set of OBJ directives
        #TI include the ".obj" suffix
        #filenames = [
                #]
        #for filepath in (__dirname__/Path("fixtures", filename) for filename in filenames):
            # with self.subTest(filename=filepath.name):
            #    self.assertExportableRootExportEqualsFixture(
            #        filepath.stem[5:],
            #        filepath,
            #        {},
            #        filepath.name,
            #    )

#TI Same class name above, we only support one TestCase in runTestCases
runTestCases([TestBlendFileNameCamelCaseNoPunctuation])
