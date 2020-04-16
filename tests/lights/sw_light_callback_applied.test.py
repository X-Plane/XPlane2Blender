import bpy
import mathutils

import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser

__dirname__ = os.path.dirname(__file__)

class TestSwLightCallbackApplied(XPlaneTestCase):
    def test_sw_light_callback_applied(self):
        xplaneFile = self.createXPlaneFileFromPotentialRoot("Layer 1")

        force_omni = xplaneFile._bl_obj_name_to_bone["do_force_omni"].xplaneObject
        self.assertEqual(force_omni.record_completed["WIDTH"], 1.0)

        noop = xplaneFile._bl_obj_name_to_bone["do_noop"].xplaneObject
        self.assertEqual(noop.record_completed.arguments,
                         [0.95, 0.82, 0.72, 0.0, 7.0, 0.0, 0.0, -1.0, 0.95,
                          'sim/graphics/animation/lights/airplane_generic_light_spill'])

        rgb_to_dxyz_w_calc = xplaneFile._bl_obj_name_to_bone["do_rgb_to_dxyz_w_calc"].xplaneObject
        vec = mathutils.Vector((rgb_to_dxyz_w_calc.record_completed["DX"],
                                rgb_to_dxyz_w_calc.record_completed["DY"],
                                rgb_to_dxyz_w_calc.record_completed["DZ"]))
        self.assertTrue(.999999995 <= vec.magnitude <= 1.00000005)

        self.assertLessEqual(rgb_to_dxyz_w_calc.record_completed["WIDTH"], 1)
        self.assertEqual([rgb_to_dxyz_w_calc.record_completed["R"],
                          rgb_to_dxyz_w_calc.record_completed["G"],
                          rgb_to_dxyz_w_calc.record_completed["B"]],
                         [1, 1, 1])


runTestCases([TestSwLightCallbackApplied])
