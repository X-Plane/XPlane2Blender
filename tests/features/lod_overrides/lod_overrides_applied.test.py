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
             and ("ATTR_LOD" in line[0]
                  or "TRIS" in line[0]))


class TestLodOverridesApplied(XPlaneTestCase):
    def test_AllIgnored(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_IncludeAndIgnore(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_NestedDuplicateOverrides(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_NonSequentialOverrides(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_NoOverridesTakesParents(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_OverridesAppliedToAllChildren(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_OverridesCombined(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )


runTestCases([TestLodOverridesApplied])
