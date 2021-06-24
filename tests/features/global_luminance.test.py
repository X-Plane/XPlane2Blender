from pathlib import Path
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestGlobalLuminance(XPlaneTestCase):
    def test_global_luminance(self)->None:
        roots = [
            "has_global_luminance_6000_air",
            "has_global_luminance_6000_cp",
            "has_global_luminance_6000_inst_scen",
            "has_global_luminance_6000_scen",
        ]
        for root in [bpy.data.collections[name] for name in roots]:
            # We're actually testing all against 1 fixture here
            filepath = Path(__dirname__, "fixtures", "test_has_global_luminance_6000.obj")
            self.assertExportableRootExportEqualsFixture(
                root.name,
                filepath,
                {"GLOBAL_luminance"},
                filepath.name,
            )

runTestCases([TestGlobalLuminance])
