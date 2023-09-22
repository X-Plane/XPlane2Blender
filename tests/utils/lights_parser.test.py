import inspect
import shutil
import pathlib
#from pathlib import Path

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser
from io_xplane2blender.xplane_utils.xplane_lights_txt_parser import LightsTxtFileParsingError
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(os.path.abspath(__file__))

REAL_LIGHTS_TXT_PATH = pathlib.Path(xplane_constants.ADDON_RESOURCES_FOLDER, "lights.txt")
BACKUP_LIGHTS_TXT_PATH = pathlib.Path(xplane_constants.ADDON_RESOURCES_FOLDER, "lights.txt.bak")
FAKE_LIGHTS_TXTS_FOLDER = pathlib.Path(__dirname__, "test_lights_txts")


class _ReplaceLightsFile:
    def __init__(self, *, temporary_lights_txt_path:pathlib.Path=None, temporary_lights_txt_content:str=None)->None:
        assert temporary_lights_txt_path or isinstance(temporary_lights_txt_content, str), "Must have non empty temporary_lights_txt_path or temporary_lights_txt_content"
        self.temporary_lights_txt_path = temporary_lights_txt_path
        self.temporary_lights_txt_content = temporary_lights_txt_content

    def __enter__(self)->None:
        try:
            os.replace(REAL_LIGHTS_TXT_PATH, BACKUP_LIGHTS_TXT_PATH)
        except FileNotFoundError:
            raise
        else:
            if self.temporary_lights_txt_path:
                shutil.copyfile(self.temporary_lights_txt_path, REAL_LIGHTS_TXT_PATH)
            elif self.temporary_lights_txt_content:
                with open(REAL_LIGHTS_TXT_PATH, 'w') as f:
                    f.write(self.temporary_lights_txt_content)

    def __exit__(self, type, value, traceback)->None:
        os.replace(BACKUP_LIGHTS_TXT_PATH, REAL_LIGHTS_TXT_PATH)
        return False


class TestLightsParser(XPlaneTestCase):
    def setUp(self):
        super().setUp(useLogger=True)
        xplane_lights_txt_parser._parsed_lights_txt_content.clear()

        try:
            #print("Attempting to rename lights.txt.bak to lights.txt")
            os.replace(BACKUP_LIGHTS_TXT_PATH, REAL_LIGHTS_TXT_PATH)
            pass
        except OSError as oe:
            #print(oe)
            pass

    def _test(self, content:str, expected_errors:int)->None:
        with _ReplaceLightsFile(temporary_lights_txt_content=content):
            if expected_errors > 0:
                self.assertRaises(LightsTxtFileParsingError, xplane_lights_txt_parser.parse_lights_file)
            self.assertLoggerErrors(expected_errors)

    #--- SUCCESSFUL cases ----------------------------------------------------
    #@unittest.skip
    def test_arguments_sorted_well(self):
        with _ReplaceLightsFile(temporary_lights_txt_path=FAKE_LIGHTS_TXTS_FOLDER/"arguments_sorted_well.txt"):
            xplane_lights_txt_parser.parse_lights_file()
            self.assertLoggerErrors(0)
            parsed_light = xplane_lights_txt_parser.get_parsed_light("sorted_well")

            self.assertEqual(
                [overload.overload_type for overload in parsed_light.overloads],
                [
                    "SPILL_HW_DIR", # Most trustworthy
                    "SPILL_HW_FLA",
                    "SPILL_SW",
                    "BILLBOARD_HW",
                    "BILLBOARD_SW",
                    "SPILL_GND",
                    "SPILL_GND_REV", # Least trustworthy
                ],
            )

    #@unittest.skip
    def test_real_lights_txt_parses(self):
        xplane_lights_txt_parser.parse_lights_file()
        self.assertLoggerErrors(0)
        num_lights = len(xplane_lights_txt_parser._parsed_lights_txt_content)
        expected_lights = 479 # You'll probably need to update this every time lights.txt is replaced
        self.assertEqual(len(xplane_lights_txt_parser._parsed_lights_txt_content), expected_lights, msg=f"Found {num_lights}, expected {expected_lights}. Did you forget to update this after updating lights.txt?")

    #@unittest.skip
    def test_light_repeatable_cases_parse(self)->None:
        s = """
# Repeatable cases parse and are okay. Note that UNUSED doesn't even get used (which is fine)
LIGHT_PARAM_DEF 12 ZERO ZERO_ ZERO__ NEG_ONE NEG_ONE_ NEG_ONE__ ONE ONE_ ONE__ UNUSED UNUSED_ UNUSED__
#            R    G     B      A       SIZE           DX        DY  DZ   WIDTH FREQ   PHASE
BILLBOARD_HW ZERO ZERO_ ZERO__ NEG_ONE NEG_ONE_ 1 1 1 NEG_ONE__ ONE ONE_ ONE__ UNUSED_ UNUSED__ NOOP
"""
        self._test(s, 0)

    #@unittest.skip
    def test_light_nonstandard_params_parse(self)->None:
        s = """
LIGHT_PARAM_DEF INTENSITY DIR_MAG LEGACY_SIZE
BILLBOARD_HW 1 0 0 1   1      1 0 6      1 0 0    .5    0    0    0    0
"""
        self._test(s, 0)
    #-------------------------------------------------------------------------

    #--- GENERAL SPEC PROBLEMS -----------------------------------------------
    #@unittest.skip
    def test_no_lights_file(self)->None:
        os.replace(REAL_LIGHTS_TXT_PATH, BACKUP_LIGHTS_TXT_PATH)
        self.assertRaises(FileNotFoundError, xplane_lights_txt_parser.parse_lights_file)
        self.assertLoggerErrors(1)
        os.replace(BACKUP_LIGHTS_TXT_PATH, REAL_LIGHTS_TXT_PATH)


    # WHOLE FILE
    #@unittest.skip
    def test_file_empty(self)->None:
        with _ReplaceLightsFile(temporary_lights_txt_path=FAKE_LIGHTS_TXTS_FOLDER/"lights_empty.txt"):
            self.assertRaises(LightsTxtFileParsingError,xplane_lights_txt_parser.parse_lights_file)
            self.assertLoggerErrors(1)

    #@unittest.skip
    def test_no_valid_records(self)->None:
        s = """
A
850
LIGHT_SPECS

TEXTURE 1000_lights_close.dds
TEXTURE 1000_lights_distant2.dds
#TEXTURE 1000_lights_precip.dds
#TEXTURE 1000_lights_fog.dds

X_DIVISIONS 16
Y_DIVISIONS 8
"""
        self._test(s,1)

    #@unittest.skip
    def test_comments_ignored(self)->None:
        # If comments are not well ignored, then this will define a light "commented out"
        with _ReplaceLightsFile(temporary_lights_txt_path=FAKE_LIGHTS_TXTS_FOLDER/"lights_comments_ignored.txt"):
            xplane_lights_txt_parser.parse_lights_file()
            self.assertRaises(KeyError, xplane_lights_txt_parser.get_parsed_light,"commented_out")

    #@unittest.skip
    def test_light_name_is_invalid(self)->None:
        s = """
BILLBOARD_HW	$		1	1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
BILLBOARD_HW	Ë		1	1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
"""
        self._test(s, 3)

    #@unittest.skip
    def test_unknown_record_types(self)->None:
        s = """
# - LIGHT_PARAM_DEFnotreal, error
# - SPILL_GND_REVnotreal, error
# - a number
# - a light name
# - billboard_hw
# the rest ignored meaning we have no valid lights once again
LIGHT_PARAM_DEFnotreal 1 A
1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
taillight		1	1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
billboard_hw	taillight		1	1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
SPILL_GND_REVnotreal	taillight		1	1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0	0
# CONE_SW/HW is no longer supported
CONE_SW			airplane_landing			1.0	0.99	0.95	0	12	2 6 0 	0	-0.15	-0.9	5					sim/graphics/animation/lights/airplane_landing_light_spill
CONE_HW			RoadBridgeDeck_var1			0.994	0.855	0.664	0.8	5	2 6 0 	0	-1	0	10
"""
        self._test(s,3)

    #@unittest.skip
    def test_incomplete_record_type(self):
        s = """
# In this, we have 4 problem lights,
# LIGHT_PARAM_DEF without a params list (but a valid light name), and one that shares a light name with its next
# record
# Then two cases of only the record type
LIGHT_PARAM_DEF R
BILLBOARD_SW R
LIGHT_PARAM_DEF
BILLBOARD_HW
"""
        self._test(s, 5)
    #-------------------------------------------------------------------------

    #--- OVERLOAD specific problems  -----------------------------------------
    #@unittest.skip
    def test_arguments_not_standard_notation(self):
        s = """
SPILL_GND		bad_numbers		-.	+1	.3	NaN
SPILL_GND_REV	bad_numbers		1.e50	inf	-inf	1e-46
"""
        self._test(s, 8)

    #@unittest.skip
    def test_arguments_len_doesnt_match_type(self):
        s = """
# Valid lights, but, parser must sort these overloads by trustworthyness
BILLBOARD_HW	too_few_args		1	1	1	1.3	1	6	6	0	0.5	0.86	-0.4	0	0	0
BILLBOARD_SW	too_few_args		1	1	1.0	1.2	1	1	0	0	0	0	1	NOOP
SPILL_GND		too_few_args		1	4	4
SPILL_GND_REV	too_few_args		1	0	2
SPILL_HW_FLA	too_few_args		1	1	0.2	1.0	0.5	0.0	20	1
SPILL_HW_DIR	too_few_args		0.05	0	0.8	3	0	-0.5	0.86	0.7	0
SPILL_SW	too_few_args		1.0	2.0	1.0	2.0	0	0	0	1	NOOP

BILLBOARD_HW    too_many_args     1	1	1	1	1.4	1	6	3	0	0	0	1	0	0	0	1 1
BILLBOARD_SW    too_many_args     1 1   1   1   1.0 1.2 1   1   0   0   0   0   1   NOOP
SPILL_GND       too_many_args     1 1   1   4   4
SPILL_GND_REV   too_many_args     1 1   1   0   2
SPILL_HW_FLA    too_many_args     1 1   1   1   0.2 1.0 0.5 0.0 20  1
SPILL_HW_DIR    too_many_args     1 0.4 0.05    0   0.8 3   0   -0.5    0.86    0.7 0
SPILL_SW    too_many_args     1 0.0 1.0 2.0 1.0 2.0 0   0   0   1   NOOP
"""
        self._test(s, 15)

    #@unittest.skip
    def test_arguments_noop_and_dref_not_in_correct_column(self):
        s = """
BILLBOARD_SW	test_lamp0		1	1	1	1.0	1.2	1	1	0	0	0	0	NOOP 1
BILLBOARD_SW	test_lamp0		1	1	1	1.0	1.2	1	1	0	0	0	0	sim/whatever 1
"""
        self._test(s, 4)

    #@unittest.skip
    def test_parameterization_arg_in_non_param_light(self):
        s = """
# No LIGHT_PARAM_DEF to go with!
BILLBOARD_SW	test_lamp0		R	G	B	1.0	1.2	1	1	0	0	0	0	1 NOOP
"""
        self._test(s,5)

    #@unittest.skip
    def test_unknown_parameterization_arg_in_param_light(self):
        s = """
LIGHT_PARAM_DEF unknown_param_in_param_light_overload 1 SIZE
SPILL_GND unknown_param_in_param_light_overload R 1 1 1
SPILL_GND unknown_param_in_param_light_overload UNUSED 1 1 1
"""
        self._test(s, 4)

    #@unittest.skip
    def test_parameterization_arg_in_wrong_column(self):
        s = """
# Here 1 is used for every argument that CAN be parameterized and UNUSED for all the ones that shouldn't
# UNUSED still counts as a parameter, even though the value will be arbitrary and ignored by tools and X-Plane
# I could have picked some other valid name like R, but, that would be confusing.
LIGHT_PARAM_DEF parameterization_arg_in_wrong_column 1 UNUSED
BILLBOARD_HW parameterization_arg_in_wrong_column 1 1 1 UNUSED 1 UNUSED UNUSED UNUSED 1 1 1 1 1 1 UNUSED UNUSED
BILLBOARD_SW parameterization_arg_in_wrong_column 1 1 1 1 1 UNUSED UNUSED UNUSED 1 1 1 1 UNUSED
SPILL_GND parameterization_arg_in_wrong_column 1 UNUSED UNUSED UNUSED
SPILL_GND_REV parameterization_arg_in_wrong_column 1 UNUSED UNUSED UNUSED
SPILL_HW_DIR parameterization_arg_in_wrong_column 1 1 1 1 1 1 1 1 1 UNUSED
SPILL_HW_FLA parameterization_arg_in_wrong_column 1 1 1 1 1 1 1 UNUSED UNUSED
SPILL_SW parameterization_arg_in_wrong_column 1 1 1 1 1 1 1 1 1 UNUSED
"""
        self._test(s, 22)
    #-------------------------------------------------------------------------

    #--- LIGHT_PARAM_DEF problems --------------------------------------------
    #@unittest.skip
    def test_light_param_count_is_not_an_int(self):
        s = """
# mistake made! for got the number 5
LIGHT_PARAM_DEF	param_count_not_an_int_missing		R
BILLBOARD_SW	param_count_not_an_int_missing		R	1	1	1	1	1	6	5	0	0	-0.8	0.2	NOOP

# Can't have .12 of a float!
LIGHT_PARAM_DEF	param_count_not_an_int_is_float	10.12	R
BILLBOARD_SW	param_count_not_an_int_is_float		1	1	1	1	1	1	6	5	0	0	-0.8	0.2	NOOP
    """
        self._test(s, 4)

    #@unittest.skip
    def test_light_param_has_duplicate_params(self):
        s = """
LIGHT_PARAM_DEF param_list_has_duplicates_normal_params 2 SIZE SIZE
SPILL_GND       param_list_has_duplicates_normal_params SIZE 1 1 1

LIGHT_PARAM_DEF param_list_has_duplicates_repeatable_params 2 UNUSED UNUSED
SPILL_GND       param_list_has_duplicates_repeatable_params UNUSED 1 1 1
"""

        self._test(s,  7)

    #@unittest.skip
    def test_duplicate_light_param_defs(self):
        s = """
LIGHT_PARAM_DEF back_to_back_light_param_defs 1 UNUSED
LIGHT_PARAM_DEF back_to_back_light_param_defs 1 UNUSED
SPILL_GND       back_to_back_light_param_defs 1 1 1 1

LIGHT_PARAM_DEF repeated_after_overloads 1 UNUSED
SPILL_GND       repeated_after_overloads .5 1 1 1

LIGHT_PARAM_DEF repeated_after_overloads 1 UNUSED
SPILL_GND_REV   repeated_after_overloads .5 1 1 1
"""
        self._test(s,5)

    #@unittest.skip
    def test_unknown_param_names(self):
        s = """
# size should be upper case
LIGHT_PARAM_DEF unknown_param_names 4 NOT_REAL size .5 10
SPILL_GND       unknown_param_names 1 1 1 1
"""
        self._test(s, 1)

    #@unittest.skip
    def test_has_light_param_def_but_no_overloads(self):
        s = """
LIGHT_PARAM_DEF has_def_but_no_overloads 3 R G B
LIGHT_PARAM_DEF has_def_but_no_valid_overloads 3 R G B
SPILL_GND       has_def_but_no_valid_overloads 1 1 1 1 1 1 1 1 1
    """
        self._test(s,4)


runTestCases([TestLightsParser])
