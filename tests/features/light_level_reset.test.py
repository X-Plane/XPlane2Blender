import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestLightLevelReset(XPlaneTestCase):
    def test_light_level_reset_directives(self) -> None:
        for filename in ["test_" + c.name for c in bpy.data.collections]:
            with self.subTest(filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                    {"ATTR_light_level", "TRIS"},
                    filename,
                )


runTestCases([TestLightLevelReset])
