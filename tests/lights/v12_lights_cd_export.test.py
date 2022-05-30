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


class TestV12LightsCDExport(XPlaneTestCase):
    def test_v12_lights_have_candela(self) -> None:
        filenames = [
            "test_v12_lights_have_candela_bb_omni",
            "test_v12_lights_have_candela_bb_sp",
            "test_v12_lights_have_candela_pm_omni",
            "test_v12_lights_have_candela_pm_sp",
        ]
        for filepath in [
            Path(__dirname__, "fixtures", f"{filename}.obj") for filename in filenames
        ]:
            with self.subTest(filepath=filepath):

                self.assertExportableRootExportEqualsFixture(
                    filepath.stem[5:], filepath, {"LIGHT"}, filepath.name,
                )


runTestCases([TestV12LightsCDExport])
