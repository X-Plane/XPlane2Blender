import bpy
import mathutils

import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light
from io_xplane2blender.xplane_types import xplane_lights_txt_parser

__dirname__ = os.path.dirname(__file__)

class TestSwLightCallbackApplied(XPlaneTestCase):
    def test_sw_light_callback_applied(self):
        force_omni = xplane_light.XPlaneLight(bpy.data.objects["do_force_omni"])
        force_omni.collect()
        self.assertTrue(force_omni.lightOverload.get("WIDTH") == 1.0)

        noop = xplane_light.XPlaneLight(bpy.data.objects["do_noop"])
        noop.collect()
        self.assertTrue(noop.lightOverload.data_source.data == [0.95, 0.82, 0.72, 0.0, 7.0, 0.0, 0.0, 1.0, 0.14, 'sim/graphics/animation/lights/airplane_navigation_light_spill'])

        rgb_to_dxyz_w_calc = xplane_light.XPlaneLight(bpy.data.objects["do_rgb_to_dxyz_w_calc"])
        rgb_to_dxyz_w_calc.collect()
        
        vec = mathutils.Vector((rgb_to_dxyz_w_calc.lightOverload.get("DX"),
                                rgb_to_dxyz_w_calc.lightOverload.get("DY"),
                                rgb_to_dxyz_w_calc.lightOverload.get("DZ")))
        self.assertTrue(.999999995 <= vec.magnitude <= 1.00000005)

        self.assertTrue(rgb_to_dxyz_w_calc.lightOverload.get("WIDTH") <= 1)
        self.assertTrue(rgb_to_dxyz_w_calc.lightOverload.get("R") == 1 and\
                        rgb_to_dxyz_w_calc.lightOverload.get("G") == 1 and\
                        rgb_to_dxyz_w_calc.lightOverload.get("B") == 1)

runTestCases([TestSwLightCallbackApplied])
 
