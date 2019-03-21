import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

#def filterLines(line):
    #return isinstance(line[0],str) and\

class TestConvertLights(XPlaneTestCase):
    def test_magnet_cases(self):
        from io_xplane2blender.xplane_types import xplane_light
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
        #access object using bpy.data.objects
        # use constructor for xplane_type, use methods
        #out = self.exportLayer(0)

        #self.assertLoggerErrors(1)

        # Note, I would recommend layout out your layers, tests, and names so they are all in order.
        # It makes everything much easier
        #
        #filename = inspect.stack()[0].function

        #self.assertLayerExportEqualsFixture(
        #    0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
        #    filename,
        #    filterLines
        #)

runTestCases([TestConvertLights])
