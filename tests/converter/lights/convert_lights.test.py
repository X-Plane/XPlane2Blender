import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("VLIGHT" in line[0] and
             "LIGHTS" in line[0])

class TestConvertLights(XPlaneTestCase):
    def test_dep_rgb_ignore(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
                "OBJdep_rgb_ignore", os.path.join(__dirname__, 'fixtures', filename + ".obj"),
                filename,
                filterLines
            )

    def test_dep_rgb_used(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
                "OBJdep_rgb_used", os.path.join(__dirname__, 'fixtures', filename + ".obj"),
                filename,
                filterLines
            )

    def test_ignored_cases(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)

        sun_autospot_real_name_ignored = bpy.data.objects["airplane_taxi_sp"]
        self.assertEqual(sun_autospot_real_name_ignored.data.type, "SUN")
        self.assertEqual(sun_autospot_real_name_ignored.data.xplane.type, xplane_constants.LIGHT_NON_EXPORTING)

        hemi_ignored = bpy.data.objects["my_named_hemi"]
        self.assertEqual(hemi_ignored.data.type, "HEMI")
        self.assertEqual(hemi_ignored.data.xplane.type, xplane_constants.LIGHT_NON_EXPORTING)

        pulse_spot_ignored = bpy.data.objects["pulse"]

        self.assertEqual(pulse_spot_ignored.data.type, "SPOT")
        self.assertEqual(pulse_spot_ignored.data.xplane.type, xplane_constants.LIGHT_NON_EXPORTING)

        smoke_black = bpy.data.objects["smoke_black"]
        self.assertEqual(smoke_black.data.xplane.type, xplane_constants.LIGHT_NON_EXPORTING)

        smoke_white = bpy.data.objects["smoke_white"]
        self.assertEqual(smoke_white.data.xplane.type, xplane_constants.LIGHT_NON_EXPORTING)

    def test_magnet_cases(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        def test_magnet(ob:bpy.types.Object, is_xpad:bool, is_flashlight:bool):
            self.assertEqual(ob.type, "EMPTY")
            self.assertEqual(ob.xplane.special_empty_props.magnet_props.debug_name, ob.name)
            self.assertEqual(ob.xplane.special_empty_props.magnet_props.magnet_type_is_xpad, is_xpad)
            self.assertEqual(ob.xplane.special_empty_props.magnet_props.magnet_type_is_flashlight, is_flashlight)

        test_magnet(bpy.data.objects["MAGnet"],              is_xpad=True,  is_flashlight=False)
        test_magnet(bpy.data.objects["MagnetFl@shlight"],    is_xpad=False, is_flashlight=True)
        test_magnet(bpy.data.objects["MagnetFromBoth"],      is_xpad=True,  is_flashlight=True)
        test_magnet(bpy.data.objects["magnet_empty_params"], is_xpad=False, is_flashlight=False)
        test_magnet(bpy.data.objects["magnet_strip_spaces"], is_xpad=True,  is_flashlight=False)
        self.assertEqual(bpy.data.objects["not_a_magnet"].type, "LAMP")

    def test_named_cases(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
                "OBJnamed_cases", os.path.join(__dirname__, 'fixtures', filename + ".obj"),
                filename,
                filterLines
            )

    def test_param_cases(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function

        self.assertRootObjectExportEqualsFixture(
                "OBJparam_cases", os.path.join(__dirname__, 'fixtures', filename + ".obj"),
                filename,
                filterLines
            )

    def test_could_auto_spot_cases(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        # One day we'll be able to check specific info messages in the log
        pass


runTestCases([TestConvertLights])
