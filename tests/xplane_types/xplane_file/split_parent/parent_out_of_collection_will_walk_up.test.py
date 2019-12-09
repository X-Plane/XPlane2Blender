import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line:Tuple[str])->bool:
    return (isinstance(line[0],str)
            and ("ANIM_" in line[0]
                 or "TRIS" in line[0]))

class TestParentOutOfCollectionWillWalkUp(XPlaneTestCase):
    def test_ExpCollWalkToColl(self)->None:
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_ExpCollWalkToExpColl(self)->None:
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_ExpCollWalkToMasterCollection(self)->None:
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_ExpCollWalkToRoot(self)->None:
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_ParentOutOfScene(self)->None:
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
            bpy.data.collections[filename[5:]],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )


runTestCases([TestParentOutOfCollectionWillWalkUp])
