import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestCockpitRegions(XPlaneTestCase):
    def test_cockpit_regions(self) -> None:
        for filename in [
            "test_cockpit_regions_used_aircraft",
            "test_cockpit_regions_used_cockpit",
        ]:
            with self.subTest(filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                    {"COCKPIT_REGION", "ATTR_cockpit_region", "ATTR_no_cockpit"},
                    filename,
                )


runTestCases([TestCockpitRegions])
