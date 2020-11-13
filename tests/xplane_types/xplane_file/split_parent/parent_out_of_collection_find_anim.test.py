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


class TestParentOutOfCollectionFindAnim(XPlaneTestCase):
    def _runAssert(self)->None:
        filename = inspect.stack()[1].function
        self.assertExportableRootExportEqualsFixture(
            bpy.data.collections[filename[5:] + "_animation"],
            os.path.join(__dirname__, "fixtures", filename + "_animation" + ".obj"),
            filterLines,
            filename + "_animation",
        )
        self.assertExportableRootExportEqualsFixture(
            bpy.data.collections[filename[5:] + "_mesh"],
            os.path.join(__dirname__, "fixtures", filename + "_mesh" + ".obj"),
            filterLines,
            filename + "_mesh",
        )

    def test_AAA(self)->None:
        self._runAssert()

    def test_AAn(self)->None:
        self._runAssert()

    def test_AnA(self)->None:
        self._runAssert()

    def test_Ann(self)->None:
        self._runAssert()

    def test_nAA(self)->None:
        self._runAssert()

    def test_nAn(self)->None:
        self._runAssert()

    def test_nnA(self)->None:
        self._runAssert()


#TI Same class name above, we only support one TestCase in runTestCases
runTestCases([TestParentOutOfCollectionFindAnim])
