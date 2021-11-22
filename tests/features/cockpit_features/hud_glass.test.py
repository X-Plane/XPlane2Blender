import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent

class TestHudGlass(XPlaneTestCase):
    def test_hud_glass(self)->None:
        filenames = [
            "test_hud_glass_and_reset.obj",
            "test_hud_glass_panel_device.obj",
            "test_hud_glass_panel_emissive.obj",
            "test_hud_glass_panel_regions.obj",
            "test_hud_glass_panel_texture.obj",
        ]

        for filepath in (__dirname__/Path("fixtures", filename) for filename in filenames):
            with self.subTest(filename=filepath.name):
                self.assertExportableRootExportEqualsFixture(
                    filepath.stem[5:],
                    filepath,
                    {},
                    filepath.name,
                )

runTestCases([TestHudGlass])
