import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestUpdateCastShadowTableOutput(XPlaneTestCase):
    def test_updater_logger_output(self):
        lines = list(filter(lambda line: line.startswith("ERROR") or line.startswith("test"), [line.body for line in bpy.data.texts["Updater Log"].lines]))
        self.assertIn("non_scenery", ''.join(lines))
        for mat_name in filter(lambda line: line.startswith("ERROR: Material"), lines):
            self.assertRegex(mat_name, "ERROR: Material '\w+(shared_table|unique)")
        for layer_name in filter(lambda line: line.startswith("test"), lines):
            self.assertRegex(layer_name, "test_.*mixed_(on|off|non_scenery_type)")


runTestCases([TestUpdateCastShadowTableOutput])
