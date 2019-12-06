import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line:Tuple[str])->bool:
    return (isinstance(line[0],str)
             and ("ANIM" in line[0]
                  or "TRIS" in line[0]
                  ))

class TestParentOutOfCollectionWorkflows(XPlaneTestCase):
    def test_1_LandingGearCollection(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_1_WheelCollection(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_2_LandingGearExpObject(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_2_WheelCollection(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_3_ButtonCollection(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_4_ExportableCollection(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )


runTestCases([TestParentOutOfCollectionWorkflows])
