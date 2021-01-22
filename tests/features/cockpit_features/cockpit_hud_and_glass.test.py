import inspect
import os
import sys
from typing import Tuple
from pathlib import Path

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestCockpitHudAndGlass(XPlaneTestCase):
    def test_good_hud_glass_cases(self)->None:
        files = [
            "test_good_HUD_and_glass",
            "test_good_HUD_and_glass_also",
        ]
        for filename in [
            Path(__dirname__, "fixtures", f"{filename}") for filename in files
        ]:
            with self.subTest(filename=filename):
                filename = filename.name
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                    {"ATTR_hud", "ATTR_cockpit"},
                    filename,
                )

    @unittest.skip
    def test_bad_hud_glass_cases(self)->None:
        collections = [
            "test_bad_HUD_used_in_scenery",
            "test_bad_HUD_used_in_inst_scenery",
            "bad_viewing_glass_in_scenery",
            "bad_viewing_glass_in_inst_scenery",
        ]
        for collection_name in collections:
            with self.subTest(collection_name=collection_name):
                out = self.exportExportableRoot(collection_name)
                self.assertLoggerErrors(1)

runTestCases([TestCockpitHudAndGlass])
