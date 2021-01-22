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


class TestLightLevelPhotometric(XPlaneTestCase):
    def test_feature_exports(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_v1200"]

        files = [
            "test_exports_photometric_correctly",
            "test_exports_mixed_ll_correctly",
        ]
        for filepath in [
            Path(__dirname__, "fixtures", f"{filename}.obj") for filename in files
        ]:
            with self.subTest(filepath=filepath):
                self.assertExportableRootExportEqualsFixture(
                    filepath.stem[5:],
                    filepath,
                    {"ATTR_light_level"},
                    filepath.name,
                )

    def test_wrong_export_types(self):
        for root_name in [
            "error_photometric_in_instanced_scenery",
        ]:
            with self.subTest(root_name=root_name):
                out = self.exportExportableRoot(root_name)
                self.assertLoggerErrors(1)

    def test_exports_with_photometric_ignored(self) -> None:
        bpy.context.window.scene = bpy.data.scenes["Scene_v1100"]
        filename = inspect.stack()[0].function
        filepath = Path(__dirname__, "fixtures", f"{filename}.obj")
        self.assertExportableRootExportEqualsFixture(
            filepath.stem[5:],
            filepath,
            {"ATTR_light_level"},
            filepath.name,
        )


runTestCases([TestLightLevelPhotometric])
