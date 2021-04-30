import inspect
import os
import sys
from typing import Tuple
from pathlib import Path

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent


class TestCockpitHudAndGlass(XPlaneTestCase):
    def test_good_hud_glass_cases(self)->None:
        filenames = [
            "test_good_HUD_and_glass.obj",
            "test_good_HUD_and_glass_also.obj",
        ]
        for filepath in [
            (__dirname__ / Path("fixtures", filename)) for filename in filenames
        ]:
            with self.subTest(filename=filepath.name):
                self.assertExportableRootExportEqualsFixture(
                    filepath.stem[5:],
                    filepath,
                    {"ATTR_hud", "ATTR_cockpit"},
                    filepath.name,
                )

    def test_ignored_hud_glass_cases(self)->None:
        filenames = [
            'test_ignored_HUD_used_in_inst_scenery.obj',
            'test_ignored_HUD_used_in_scenery.obj',
            'test_ignored_viewing_glass_used_in_inst_scenery.obj',
            'test_ignored_viewing_glass_used_in_scenery.obj',
        ]
        for filepath in [
            (__dirname__ / Path("fixtures", filename)) for filename in filenames
        ]:
            with self.subTest(filename=filepath.name):
                self.assertExportableRootExportEqualsFixture(
                    filepath.stem[5:],
                    filepath,
                    {"ATTR_hud", "ATTR_cockpit"},
                    filepath.name,
                )

runTestCases([TestCockpitHudAndGlass])
