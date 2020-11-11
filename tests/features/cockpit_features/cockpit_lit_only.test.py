import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestCockpitLitOnly(XPlaneTestCase):
    def test_Scene_1100(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_1100"]

        filename = "test_05_cockpit_lit_only_no_export_wrong_version"
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ATTR_cockpit_lit_only"},
            filename,
        )

    def test_Scene_1110(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_1110"]

        out = self.exportExportableRoot("test_02_cockpit_lit_only_wrong_type_error"[5:])
        # Scenery cannot have panel
        self.assertLoggerErrors(1)

        for filename in [
            "test_01_cockpit_lit_only_exported",
            "test_03_cockpit_lit_only_no_export_regions",
            "test_04_cockpit_lit_no_export_panel_mode_default",
            "test_07_cockpit_lit_only_resets",
        ]:
            with self.subTest(f"Testing fixture {filename}", filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                    {"ATTR_cockpit_lit_only"},
                    filename,
                )

    def test_Scene_default_version(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_default_version"]
        filename = "test_06_cockpit_lit_only_exported"
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ATTR_cockpit_lit_only"},
            filename,
        )


runTestCases([TestCockpitLitOnly])
