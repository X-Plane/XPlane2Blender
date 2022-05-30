import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

from io_xplane2blender.xplane_utils import xplane_lights_txt_parser
from io_xplane2blender.xplane_utils.xplane_lights_txt_parser import get_overload_column_info, get_parsed_light, ColumnName

__dirname__ = os.path.dirname(__file__)


class TestColumnName(XPlaneTestCase):
    def setUp(self):
        xplane_lights_txt_parser.parse_lights_file()

    def test_ColumnName_enum(self) -> None:
        # fmt: off
        self.assertEqual([
            "R",
            "G",
            "B",
            "A",
            "SIZE",
            "CELL_SIZE",
            "CELL_ROW",
            "CELL_COL",
            "DX",
            "DY",
            "DZ",
            "WIDTH",
            "FREQ",
            "PHASE",
            "AMP",
            "DAY",
            "DREF",
        ], [m.value for m in ColumnName])
        # fmt: on

    def test_param_to_canonical_column_name(self)->None:
        ptc = ColumnName.param_to_canonical_column_name

        self.assertEqual(ColumnName.A, ptc(None, "INDEX"))
        self.assertEqual(ColumnName.SIZE, ptc("airplane_landing_pm", "INTENSITY"))
        self.assertEqual(ColumnName.SIZE,ptc("flood_merc_XYZTSB", "LEGACY_SIZE", "BILLBOARD_HW"))
        self.assertEqual(ColumnName.SIZE,ptc("flood_LPS_XYZTSB", "LEGACY_SIZE", "BILLBOARD_HW"))
        self.assertEqual(ColumnName.B, ptc("airplane_nav_tail_size", "DIR_MAG"))
        self.assertEqual(ColumnName.R, ptc("airplane_nav_left_size", "DIR_MAG"))
        self.assertEqual(ColumnName.R, ptc("airplane_nav_right_size", "DIR_MAG"))
        self.assertRaises(ValueError, lambda: ptc(None, "UNUSED"))
        self.assertRaises(ValueError, lambda: ptc(None, "phase")) # Capitilization  matters

    def test_parsed_light_overload(self) -> None:
        ov = get_parsed_light("airplane_spot_bb").best_overload()
        # for a few lights, test __contains__, __getitem__, __setitem__ with

        self.assertTrue("INTENSITY" in ov)
        self.assertFalse("AMP" in ov)

        self.assertEqual(ov["INTENSITY"], "INTENSITY")
        ov["INTENSITY"] = 1000
        self.assertEqual(ov["INTENSITY"], 1000)
        self.assertEqual(ov[4], 1000)

        old_light = get_parsed_light("full_custom_halo").best_overload()
        self.assertTrue(ColumnName.A in old_light)
        self.assertTrue("A" in old_light)
        self.assertFalse(ColumnName.PHASE in old_light)
        self.assertFalse("PHASE" in old_light)

        self.assertEqual(old_light[ColumnName.A], "A")
        self.assertEqual(old_light["A"], "A")
        old_light["A"] = 100
        self.assertEqual(old_light[ColumnName.A], 100)
        old_light[ColumnName.A] = 2000
        self.assertEqual(old_light["A"], 2000)
        old_light[4] = 3000
        self.assertEqual(old_light[4], 3000)

runTestCases([TestColumnName])
