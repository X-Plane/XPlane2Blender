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

    def test_failing_cases(self) -> None:
        out = self.exportExportableRoot(
            "device_fails_no_buses",
        )
        self.assertLoggerErrors(1)


runTestCases([TestCockpitDevice])
