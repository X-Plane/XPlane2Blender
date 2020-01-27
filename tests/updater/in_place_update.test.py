import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestInPlaceUpdate(XPlaneTestCase):
    def test_anim_type_to_anim_type(self):
        from io_xplane2blender.xplane_types import xplane_primitive
        from io_xplane2blender import xplane_constants

        filename = inspect.stack()[0][3]
        obj = bpy.data.objects[filename.replace("test_","")]
        self.assertEqual(obj.xplane.datarefs[0].anim_type, xplane_constants.ANIM_TYPE_TRANSFORM)
        self.assertEqual(obj.xplane.datarefs[1].anim_type, xplane_constants.ANIM_TYPE_TRANSFORM)
        self.assertEqual(obj.xplane.datarefs[2].anim_type, xplane_constants.ANIM_TYPE_TRANSFORM)
        self.assertEqual(obj.xplane.datarefs[3].anim_type, xplane_constants.ANIM_TYPE_SHOW)
        self.assertEqual(obj.xplane.datarefs[4].anim_type, xplane_constants.ANIM_TYPE_HIDE)

runTestCases([TestInPlaceUpdate])
