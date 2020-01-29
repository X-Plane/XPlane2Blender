import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.xplane_types.xplane_bone import XPlaneBone
from io_xplane2blender.xplane_types.xplane_object import XPlaneObject
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestRecursiveCollectionEdgeCases(XPlaneTestCase):
    def test_Exportable_no_convert_makes_bones(self)->None:
        obs = bpy.data.objects
        xp_file = xplane_file.createFileFromBlenderRootObject(bpy.data.collections["Exportable_no_convert_makes_bones"])
        fixture_xp_file = xplane_file.XPlaneFile("Fixture XPlaneFile", bpy.data.collections["Exportable_no_convert_makes_bones"].xplane.layer)

        fixture_root_bone =           XPlaneBone(fixture_xp_file, None, None, None)
        bezier_curve_bone =           XPlaneBone(fixture_xp_file, obs["BezierCurve_doesnt_convert"],        None, None, fixture_root_bone)
        speaker_doesnt_convert_bone = XPlaneBone(fixture_xp_file, obs["Speaker_doesnt_convert"],            None, None, bezier_curve_bone)
        suzanne_does_convert_bone =   XPlaneBone(fixture_xp_file, obs["Suzanne_does_convert"], None, XPlaneObject(obs["Suzanne_does_convert"]), speaker_doesnt_convert_bone)
        self.assertXPlaneBoneTreeEqual(xp_file.rootBone, fixture_root_bone)

    def test_Exportable_out_of_collection_no_error(self):
        # Specifically we should have none of these things
        def filterLines(line):
            return isinstance(line[0],str) and\
                    ("POINT_COUNTS" in line[0] or\
                     "VT" in line[0] or\
                     "TRIS" in line[0])
        out = self.exportExportableRoot(bpy.data.collections["Exportable_out_of_collection_no_error"])
        self.assertLoggerErrors(0)
        filename = inspect.stack()[0].function
        self.assertFileOutputEqualsFixture(
            out,
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines
        )

    def test_Exportable_child_out_of_scene_warn_and_ignore(self):
        filename = inspect.stack()[0].function
        def filterLines(line):
            return isinstance(line[0],str) and\
                    ("TRIS" in line[0])
        self.assertExportableRootExportEqualsFixture(
            bpy.data.objects[filename[5:]],
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


runTestCases([TestRecursiveCollectionEdgeCases])
