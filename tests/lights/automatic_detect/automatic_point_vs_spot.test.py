import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestAutomaticPointVsSpot(XPlaneTestCase):
    def test_automatic_point_vs_spot_error(self)->None:
        filename = inspect.stack()[0].function
        out = self.exportExportableRoot(filename[5:])
        self.assertLoggerErrors(5)

    def test_automatic_point_vs_spot_okay(self)->None:
        filename = inspect.stack()[0].function
        out = self.exportExportableRoot(filename[5:])
        self.assertLoggerErrors(0)


runTestCases([TestAutomaticPointVsSpot])
