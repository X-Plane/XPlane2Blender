import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_constants, xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)


class TestGlobalProperties(XPlaneTestCase):
    def test_cockpit_region(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        root = scene.objects["OBJCockpitRegionKnown"]
        self.assertTrue(root.xplane.layer.export_type == xplane_constants.EXPORT_TYPE_COCKPIT)
        self.assertTrue(root.xplane.layer.cockpit_regions == "1")

        cockpit_region = root.xplane.layer.cockpit_region[0]
        self.assertTrue((cockpit_region.left, cockpit_region.top, 2 ** cockpit_region.width, 2 ** cockpit_region.height) == (0, 0, 32, 32))

    def test_global_limit(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        root = scene.objects["OBJGlobalProperties"]
        self.assertTrue(root.xplane.layer.require_surface == xplane_constants.REQUIRE_SURFACE_DRY)

    def test_requires_wet(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        scene = bpy.context.scene
        root = scene.objects["OBJRequiresWet"]
        self.assertTrue(root.xplane.layer.require_surface == xplane_constants.REQUIRE_SURFACE_WET)

runTestCases([TestGlobalProperties])
