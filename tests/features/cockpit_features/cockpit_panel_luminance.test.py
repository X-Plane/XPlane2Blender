from pathlib import Path
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent

class TestCockpitFeatureLuminance(XPlaneTestCase):
    def test_cockpit_feature_luminance(self)->None:
        filenames = [
            "test_panel_luminance_cockpit.obj",
            "test_panel_luminance_cockpit_device.obj",
            "test_panel_luminance_cockpit_regions.obj",
        ]
        for filepath in (__dirname__/Path("fixtures", filename) for filename in filenames):
            self.assertExportableRootExportEqualsFixture(
                filepath.stem[5:],
                filepath,
                {"ATTR_cockpit", "ATTR_no_cockpit"},
                filepath.name,
            )

runTestCases([TestCockpitFeatureLuminance])
