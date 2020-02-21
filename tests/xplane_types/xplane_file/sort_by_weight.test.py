import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender.xplane_types.xplane_bone import XPlaneBone
from io_xplane2blender.xplane_types.xplane_object import XPlaneObject
from io_xplane2blender.xplane_types.xplane_empty import XPlaneEmpty
from io_xplane2blender.xplane_types.xplane_primitive import XPlanePrimitive
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestSortByWeight(XPlaneTestCase):
    def test_sort_by_weight_objects(self)->None:
        obs = bpy.data.objects
        xp_file = self.createXPlaneFileFromPotentialRoot(obs["sort_by_weight_objects"])
        fixture_xp_file = xplane_file.XPlaneFile("Fixture XPlaneFile", obs["sort_by_weight_objects"].xplane.layer)

        xp_root_bone = xp_file.rootBone
        # This is all the work that _recurse does for us. Aren't we thankful!
        # The order here matters! XPlaneBone changes fixture_root_bone's children!
        fixture_root_bone = XPlaneBone(fixture_xp_file, obs["sort_by_weight_objects"], None, XPlaneEmpty(obs["sort_by_weight_objects"]), None)

        sphere_root_bone =     XPlaneBone(fixture_xp_file, obs["Sphere_1"],    None, XPlanePrimitive(obs["Sphere_1"]),    fixture_root_bone)
        plane_root_bone =      XPlaneBone(fixture_xp_file, obs["Plane_2"],     None, XPlanePrimitive(obs["Plane_2"]),     fixture_root_bone)
        cube_root_bone =       XPlaneBone(fixture_xp_file, obs["Cube_6"],      None, XPlanePrimitive(obs["Cube_6"]),      fixture_root_bone)
        circle_root_bone =     XPlaneBone(fixture_xp_file, obs["Circle_8"],    None, XPlanePrimitive(obs["Circle_8"]),    fixture_root_bone)
        icosphere_root_bone =  XPlaneBone(fixture_xp_file, obs["Icosphere_9"], None, XPlanePrimitive(obs["Icosphere_9"]), fixture_root_bone)
        armature_root_bone =   XPlaneBone(fixture_xp_file, obs["Armature_99"], None, XPlaneObject(obs["Armature_99"]),    fixture_root_bone)

        bone_root_bone =  XPlaneBone(fixture_xp_file, obs["Armature_99"], obs["Armature_99"].data.bones[0], None, armature_root_bone)

        torus_root_bone = XPlaneBone(fixture_xp_file, obs["Torus_99_but_no_override_0"], None, XPlanePrimitive(obs["Torus_99_but_no_override_0"]), bone_root_bone)
        cone_root_bone =  XPlaneBone(fixture_xp_file, obs["Cone_3"],                 None, XPlanePrimitive(obs["Cone_3"]),                 bone_root_bone)

        self.assertXPlaneBoneTreeEqual(xp_root_bone, fixture_root_bone)

runTestCases([TestSortByWeight])
