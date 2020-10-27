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

        out = self.exportExportableRoot("05_cockpit_lit_only_no_export_wrong_version")
        self.assertNotIn("ATTR_cockpit_lit_only", out)

    def test_Scene_1110(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_1110"]

        out = self.exportExportableRoot("01_cockpit_lit_only_exported")
        self.assertIn("ATTR_cockpit_lit_only", out)
        for root in [
            c
            for c in bpy.context.scene.collection.children
            if not c.name.startswith("01")
        ]:
            with self.subTest(f"Exporting {root.name}", root=root):
                out = self.exportExportableRoot(root)
                self.assertNotIn("ATTR_cockpit_lit_only", out)

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
