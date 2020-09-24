import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestLightSpillCustomAttributes(XPlaneTestCase):
    def test_light_attributes(self)->None:
        filenames = ["test_light_spill_custom_xyz",
                     "test_light_spill_custom_rgb",
                     "test_light_spill_custom_dxyz",
                     "test_light_spill_custom_size",
                     "test_light_spill_custom_semi_spot",
                     "test_light_spill_custom_semi_point",
                     "test_light_spill_custom_dref",]

        for filename in filenames:
            with self.subTest(filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", "light_spill_custom", f"{filename}.obj"),
                    {"LIGHT_SPILL_CUSTOM"},
                    filename,
                )

    def test_incompatible_light_types(self):
        filename = inspect.stack()[0].function
        out = self.exportExportableRoot(filename[5:])
        self.assertLoggerErrors(2)


runTestCases([TestLightSpillCustomAttributes])
