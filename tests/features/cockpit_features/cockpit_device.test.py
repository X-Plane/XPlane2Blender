import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestCockpitDevice(XPlaneTestCase):
    def test_passing_cases(self) -> None:
        filenames = [
            "test_device_passing_auto_adjust_off",
            "test_device_passing_bitfield",
            "test_device_passing_lighting_channel",
            "test_device_passing_names",
            "test_device_mix_with_panel",
        ]

        for filename in filenames:
            with self.subTest(filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                    {"ATTR_cockpit", "ATTR_cockpit_device", "ATTR_no_cockpit", "TRIS"},
                    filename,
                )

    def test_no_bus_no_rheostat(self) -> None:
        """
        X-Plane powers a device on no bus always, and its own aircraft
        ship G1000 screens on rheostat -1
        """
        mat = bpy.data.materials["device_mat_channel_5"].xplane
        cases = [
            ("device_bus_0", False, "ATTR_cockpit_device\tGNS430_1\t0\t5\t1"),
            ("device_lighting_channel", -1, "ATTR_cockpit_device\tGNS430_1\t1\t-1\t1"),
        ]
        for prop, value, line in cases:
            with self.subTest(prop=prop):
                saved = getattr(mat, prop)
                setattr(mat, prop, value)
                try:
                    out = self.exportExportableRoot("device_passing_lighting_channel")
                finally:
                    setattr(mat, prop, saved)
                self.assertLoggerErrors(0)
                self.assertIn(line, out)


runTestCases([TestCockpitDevice])
