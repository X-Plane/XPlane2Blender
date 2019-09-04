import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_constants, xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WORKFLOW_DEFAULT_ROOT_NAME, WorkflowType

__dirname__ = os.path.dirname(__file__)


class TestGlobalPropertiesRegular(XPlaneTestCase):
    def test_global_properties_regular(self):
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.SCENERY.name, workflow_type=WorkflowType.REGULAR.name)
        scene = bpy.context.scene
        root = scene.objects[WORKFLOW_DEFAULT_ROOT_NAME + "_01"]
        layer = root.xplane.layer
        self.assertTrue(layer.slope_limit is True)
        self.assertTrue((layer.slope_limit_min_pitch,
                         layer.slope_limit_max_pitch,
                         layer.slope_limit_min_roll,
                         layer.slope_limit_max_roll) == (-90, 90, -90, 90))

        self.assertTrue(root.xplane.layer.tilted is True)
        self.assertTrue(root.xplane.layer.layer_group == xplane_constants.LAYER_GROUP_TAXIWAYS)
        self.assertTrue(root.xplane.layer.layer_group_offset == -2)
        self.assertTrue(root.xplane.layer.require_surface == xplane_constants.REQUIRE_SURFACE_DRY)
        cockpit_region = root.xplane.layer.cockpit_region[0]
        self.assertTrue(root.xplane.layer.cockpit_regions == "1")
        self.assertTrue((cockpit_region.left, cockpit_region.top, 2 ** cockpit_region.width, 2 ** cockpit_region.height) == (0, 0, 32, 32))

        self.assertTrue(root.xplane.layer.export_type == xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY)
        self.assertTrue(root.xplane.layer.lod_draped == 1000.0)
        self.assertTrue(root.xplane.layer.layer_group_draped == xplane_constants.LAYER_GROUP_BEACHES)
        self.assertTrue(root.xplane.layer.layer_group_draped_offset == 5)


runTestCases([TestGlobalPropertiesRegular])
