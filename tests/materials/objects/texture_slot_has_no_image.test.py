import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestTextureSlotHasNoImage(XPlaneTestCase):
    def test_texture_slot_has_no_image(self):
        out  = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestTextureSlotHasNoImage])
