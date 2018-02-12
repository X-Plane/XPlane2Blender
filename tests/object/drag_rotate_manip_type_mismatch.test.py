import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestDragRotateManipTypeMismatch(XPlaneTestCase):
    def test_1_general_error_list(self):
        out  = self.exportLayer(0)
        self.assertLoggerErrors(1)
    def test_2_switch_drag_rotate_w_detent_to_drag_rotate(self):
        out  = self.exportLayer(1)
        self.assertLoggerErrors(1)
    def test_3_switch_drag_rotate_to_drag_rotate_w_detent(self):
        out  = self.exportLayer(2)
        self.assertLoggerErrors(1)

runTestCases([TestDragRotateManipTypeMismatch])
