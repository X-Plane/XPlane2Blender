import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestBlendRatio(XPlaneTestCase):
    def test_blend_ratio(self) -> None:
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            root_object=filename[5:],
            fixturePath=os.path.join(__dirname__, "..", "fixtures", filename + ".obj"),
            filterCallback={"ATTR_no_blend", "ATTR_shadow_blend"},
            tmpFilename=filename,
        )


runTestCases([TestBlendRatio])
