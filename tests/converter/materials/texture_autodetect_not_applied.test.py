import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestTextureAutodetectNotApplied(XPlaneTestCase):
    def test_all_roots_have_no_autodetect(self)->None:
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        for root in filter(lambda o: o.xplane.isExportableRoot, bpy.data.objects):
            self.assertTrue(root.xplane.layer.autodetectTextures)
            self.assertEqual(root.xplane.layer.texture, "")
            self.assertEqual(root.xplane.layer.texture_normal, "")
            self.assertEqual(root.xplane.layer.texture_lit, "")
            self.assertEqual(root.xplane.layer.texture_lit, "")
            self.assertEqual(root.xplane.layer.texture_draped, "")
            self.assertEqual(root.xplane.layer.texture_draped_normal, "")


runTestCases([TestTextureAutodetectNotApplied])
