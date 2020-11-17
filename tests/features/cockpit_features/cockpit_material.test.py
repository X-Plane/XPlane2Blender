import os
import sys

import bpy

from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


class TestCockpitMaterial(XPlaneTestCase):
    def test_cockpit_export(self):

        filename = "test_cockpit_material"

        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            {"ATTR_cockpit", "ATTR_no_cockpit", "TEXTURE"},
            filename,
        )

    def test_aircraft_material(self):

        filename = "test_aircraft_material"

        self.assertLayerExportEqualsFixture(
            1,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            {"ATTR_cockpit", "ATTR_no_cockpit", "TEXTURE"},
            filename,
        )


runTestCases([TestCockpitMaterial])
