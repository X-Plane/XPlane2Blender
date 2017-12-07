import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestSupersetUpdateNoOverwrite(XPlaneTestCase):
    def test_manip_type_to_manip_type_v1110(self):
        from io_xplane2blender.xplane_types import xplane_primitive
        from io_xplane2blender import xplane_constants

        filename = inspect.stack()[0][3]
        obj = bpy.data.objects[filename.replace("test_","")]
        self.assertTrue(obj.xplane.manip.type_v1110 == xplane_constants.MANIP_COMMAND_SWITCH_UP_DOWN2)

runTestCases([TestSupersetUpdateNoOverwrite])
