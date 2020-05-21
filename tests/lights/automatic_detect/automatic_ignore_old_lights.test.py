import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestAutomaticIgnoreOldLights(XPlaneTestCase):
    def test_automatic_ignore_old_lights(self)->None:
        filename = inspect.stack()[0].function
        self.exportExportableRoot(filename[5:])
        self.assertLoggerErrors(20)


runTestCases([TestAutomaticIgnoreOldLights])
