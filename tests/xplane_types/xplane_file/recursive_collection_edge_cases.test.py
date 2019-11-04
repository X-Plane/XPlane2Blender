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

#def filterLines(line:Tuple[str])->bool:
#    return (isinstance(line[0],str)
#             and ("OBJ_DIRECTIVE" in line[0])


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

    def test_Exportable_out_of_collection_error(self):
        out = self.exportRootObject(bpy.data.collections["Exportable_out_of_collection_error"])
        self.assertLoggerErrors(1)

    def test_Exportable_out_of_scene_error(self):
        out = self.exportRootObject(bpy.data.objects["Exportable_child_out_of_scene_error"])
        self.assertLoggerErrors(1)




        #TI Example of running the converter first (replace BULK with REGULAR as needed)
        #TI This should be at the start of every 2.49 test, the code knows to only run once
        #TI This makes it easier to use unittest.skip
        #bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.BULK.name)

        #TI Example of whitebox/API testing using an xplane_type
        #TI Import some io_xplane2blender module, call __init__/use API and test results
        #TI from io_xplane2blender.xplane_types import xplane_example
        #TI example = xplane_ex.XPlaneExampleType("My Name")
        #TI self.assertTrue(example.isValid())
        #from io_xplane2blender.xplane_types import xplane_

        #TI Testing the results of an export without a fixture
        #TI out is the content for the .obj file
        #out = self.exportRootObject()

        #TI Example of expecting a failure
        #TI (Note: This doesn't test specific errors)
        #self.assertLoggerErrors(1)

        #TI Unless necessary, keep OBJ, object, and test method (and order) names consistent
        #TI It is so much easier to understand and debug a test that way!
        #TI There is even an operator in the Plugin Dev section to help
        #filename = inspect.stack()[0].function

        #TI Example testing root object against fixture
        #TI We name a root object something like "01_my_root_object" and remove filename's "test_"
        #TI instead of "test_01_my_root_object" to not run into Blender's max object name length
        #self.assertRootObjectExportEqualsFixture(
        #    bpy.data.objects[filename[5:]],
        #    os.path.join(__dirname__, "fixtures", filename + ".obj"),
        #    filename,
        #    filterLines
        #)

runTestCases([TestRecursiveCollectionEdgeCases])
