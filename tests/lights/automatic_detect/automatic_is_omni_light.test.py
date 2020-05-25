import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_utils.xplane_lights_txt_parser import get_parsed_light, parse_lights_file
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestAutomaticIsOmniLight(XPlaneTestCase):
    @unittest.skip("Not ready")
    def test_is_omni_lights(self)->None:
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM_", "LIGHT_"},
            filename,
        )

    @unittest.skip("Not ready")
    def test_is_non_omni_lights(self)->None:
        filename = inspect.stack()[0].function
        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "LIGHT"},
            filename,
        )

    def test_is_omni_api(self)->None:
        parse_lights_file()
        def _test(name):
            self.assertTrue(get_parsed_light(name).best_overload().is_omni(), msg=f"Light Name {name} is not omni")

        _test("heli_morse_beacon")
        spot_params_bb = get_parsed_light("spot_params_bb").best_overload()
        spot_params_bb["WIDTH"] = 1
        self.assertTrue(spot_params_bb.is_omni(), msg=f"Light Name 'spot_params_bb' is not omni")
        _test("airplane_strobe_omni")
        # No WIDTH parameter. TODO: Is this right to test?
        _test("airplane_beacon_rotate")
        _test("inset_appch_rabbit_o_sp")


    def test_is_non_omni_api(self)->None:
        parse_lights_file()
        def _test(name):
            self.assertFalse(get_parsed_light(name).best_overload().is_omni(), msg=f"Light Name {name} is omni")
        _test("taillight")
        _test("apron_light_E")
        p= get_parsed_light("helipad_flood_sp")
        helipad_flood_sp = p.best_overload()
        helipad_flood_sp["WIDTH"] = 0.23
        self.assertFalse(helipad_flood_sp.is_omni(), msg=f"Light Name 'helipad_flood_sp' is omni")

        _test("amb_cool_fl_1_sp")
        _test("airplane_generic_core")
        _test("inset_appch_rabbit_u_sp")

runTestCases([TestAutomaticIsOmniLight])
