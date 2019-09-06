import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import DEFAULT_MATERIAL_NAME, ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestPanelTextureSplits(XPlaneTestCase):
    def test_split_groups_made(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        new_panel_objects = {
            bpy.data.objects["TEX_ON_HAS_PANEL_0"], #_cockpit's new panel faces
            bpy.data.objects["TEX_ON_HAS_PANEL.001_0"], #_panel_ok's new panel faces
        }

        new_split_objects = {
            bpy.data.objects["TEX_ON_HAS_PANEL_1"], #_cockpit's other panel faces
            bpy.data.objects["TEX_ON_HAS_PANEL.001_1"], #_panel_ok's other panel faces
        }

        for panel_object in new_panel_objects:
            self.assertTrue(panel_object.material_slots[0].material.xplane.panel, msg="{}'s material {} doesn't have Panel enabled".format(panel_object.name, panel_object.material_slots[0].material.name))
            self.assertEqual(len(panel_object.data.polygons), 2)

        for other_split_object in new_split_objects:
            self.assertFalse(other_split_object.material_slots[0].material.xplane.panel, msg="{}'s material {} has Panel enabled".format(other_split_object.name, other_split_object.material_slots[0].material.name))
            self.assertEqual(len(other_split_object.data.polygons), 2, msg="{} had {} faces".format(other_split_object.name, len(other_split_object.data.polygons)))

        for other in filter(lambda ob: ob.type == "MESH", set(bpy.data.objects) - new_panel_objects - new_split_objects):
            self.assertFalse(other.material_slots[0].material.xplane.panel)
            self.assertEqual(len(other.data.polygons), 4, msg="{} had {} faces".format(other.name, len(other.data.polygons)))


runTestCases([TestPanelTextureSplits])
