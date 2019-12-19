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
            and ("VT" in line[0]
                 or "TRIS" in line[0]))

class TestMultipleExportWorks(XPlaneTestCase):
    def test_multiple_export_works_simple(self)->None:
        filename = inspect.stack()[0].function

        for i in range(1,4):
            self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename + str(i),
                filterLines
            )

    def test_multiple_export_works_uv_map(self)->None:
        filename = inspect.stack()[0].function

        for i in range(1,4):
            self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename + str(i),
                filterLines
            )

    def test_multiple_export_works_anim_bone(self)->None:
        filename = inspect.stack()[0].function

        for i in range(1,4):
            self.assertRootObjectExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", filename + ".obj"),
                filename + str(i),
                filterLines
            )

runTestCases([TestMultipleExportWorks])
