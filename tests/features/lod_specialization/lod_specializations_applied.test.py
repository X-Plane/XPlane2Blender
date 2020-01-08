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
             and ("OBJ_DIRECTIVE" in line[0]
                  or "ATTR_LOD" in line[0]
                  or "TRIS" in line[0]))


class TestLodSpecializationsApplied(XPlaneTestCase):
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

    def test_NestedDuplicateSpecialization(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_NonSequentialSpecializationOverride(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_NoSpecializationTakesParents(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_SpecializationAppliedToAllChildren(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )

    def test_SpecializationOverride(self)->None:
        filename = inspect.stack()[0].function
        self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename,
                filterLines
            )


runTestCases([TestLodSpecializationsApplied])
