import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestBlendFileNameCamelCaseNoPunctuation(XPlaneTestCase):
    def test_DisabledInViewport(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            {"ANIM", "DONT_EXPORT_THIS", "ENDIF", "IF", "LIGHT", "LIGHT", "TRIS", "VLIGHT"},
            filename,
        )

    def test_HiddenInViewport(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            {"ANIM", "DONT_EXPORT_THIS", "ENDIF", "IF", "LIGHT", "LIGHT", "TRIS", "VLIGHT"},
            filename,
        )


#TI Same class name above, we only support one TestCase in runTestCases
runTestCases([TestBlendFileNameCamelCaseNoPunctuation])
