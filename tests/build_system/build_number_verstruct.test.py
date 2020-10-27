import os
import sys
from shutil import *

import bpy
from bpy.app import build_type

from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_helpers import VerStruct

__dirname__ = os.path.dirname(__file__)


class TestBuildNumberVerStruct(XPlaneTestCase):
    current = xplane_helpers.VerStruct.current()
    history = bpy.context.scene.xplane.xplane2blender_ver_history

    def test_constructor_defaults_correct(self):
        ver_s = VerStruct()

        self.assertEqual(
            ver_s.addon_version,
            (0, 0, 0),
            "addon_version %s does not match it's default %s"
            % (ver_s.addon_version, (0, 0, 0)),
        )
        self.assertEqual(
            ver_s.build_type,
            xplane_constants.BUILD_TYPE_DEV,
            "build_type %s does not match it's default %s"
            % (ver_s.build_type, xplane_constants.BUILD_TYPE_DEV),
        )
        self.assertEqual(
            ver_s.build_type_version,
            0,
            "build_type_version %s does not match it's default %s"
            % (ver_s.build_type_version, 0),
        )
        self.assertEqual(
            ver_s.data_model_version,
            0,
            "data_model_version %s does not match it's default %s"
            % (ver_s.data_model_version, 0),
        )
        self.assertEqual(
            ver_s.build_number,
            xplane_constants.BUILD_NUMBER_NONE,
            "build_number %s does not match it's default %s"
            % (ver_s.build_number, xplane_constants.BUILD_NUMBER_NONE),
        )

    def test_repr_makes_struct_in_eval(self):
        ver_s = VerStruct.current()

        try:
            VerStruct(*eval(repr(ver_s)))
        except Exception as e:
            assert (
                False
            ), f"repr of VerStruct was unable to turn back into a VerStruct: {repr(ver_s)}"

    def test_xplane2blender_str(self):
        parsed_str = str(VerStruct.parse_version("3.4.0"))
        self.assertEqual(
            "3.4.0-leg.0+0.NO_BUILD_NUMBR",
            parsed_str,
            "VerStruct.__str__ does not format string into proper form %s" % parsed_str,
        )

    def test_invalid_ver_addition(self):
        orig_history_len = len(self.history)
        new_entry = VerStruct.add_to_version_history(
            bpy.context.scene, VerStruct((-1, -1, -1), "INVALID", -1, -1, "INVALID")
        )
        self.assertIsNone(new_entry, "Invalid entry was allowed into version history")
        self.assertEqual(
            orig_history_len,
            len(self.history),
            "History was not returned to original length after invalid addition",
        )

    def test_valid_ver_addition(self):
        orig_history_len = len(self.history)
        new_entry = VerStruct.add_to_version_history(bpy.context.scene, self.current)
        self.assertIsNotNone(
            new_entry, "Valid entry was not allowed into version history"
        )
        self.assertNotEqual(
            orig_history_len,
            orig_history_len + 1,
            "History length was not incremented by one after valid addition",
        )

    def test_make_new_build_number(self):
        ver_s = VerStruct.current()
        ver_s.build_number = VerStruct.make_new_build_number()
        self.assertTrue(
            ver_s.is_valid(),
            "VerStruct.make_new_build_number does not generate vaild build numbers",
        )

    def test_parse_version(self):
        incorrect_versions_legacy = [
            "random_letters qwerasdfzxcv",
            "340",
            "03.4.0",
            "3.4.0.",
            "(3.4.0)",
            "3_20_20",
        ]

        for test_v in incorrect_versions_legacy:
            try:
                self.assertFalse(
                    VerStruct.parse_version(test_v) != None,
                    "VerStruct.parse_version allowed bad legacy style version %s through"
                    % test_v,
                )
            except Exception as e:
                pass

        incorrect_versions_modern = [
            "3.4.0.beta.1",  # Bad separator
            "3.4.0-alpha.-1",  # Int, but not < 0
            "3.4.0-rc",  # Missing revision number
            "3.4.0-rc.1-1.20170906153430",  # Bad separator
            "3.4.0-rc.1+1.YYYYMMDDHHMMSS",  # Parsing the description, not the contents
            "3.4.0-rc.1+1.2017",  # Build string is numbers, but not long enough
        ]

        for test_v in incorrect_versions_modern:
            try:
                self.assertFalse(
                    VerStruct.parse_version(test_v) != None,
                    "VerStruct.parse_version allowed bad modern style version %s through"
                    % test_v,
                )
            except Exception as e:
                pass

        correct_versions_legacy = [
            (
                "3.2.0",
                VerStruct(
                    addon_version=(3, 2, 0),
                    build_type=xplane_constants.BUILD_TYPE_LEGACY,
                ),
            ),
            (
                "3.20.0",
                VerStruct(
                    addon_version=(3, 20, 0),
                    build_type=xplane_constants.BUILD_TYPE_LEGACY,
                ),
            ),  # Keep 20->2 in xplane_updater.py
            (
                "3.3.13",
                VerStruct(
                    addon_version=(3, 3, 13),
                    build_type=xplane_constants.BUILD_TYPE_LEGACY,
                ),
            ),
        ]

        for test_v, test_v_res in correct_versions_legacy:
            v_res = VerStruct.parse_version(test_v)
            self.assertIsNotNone(
                v_res,
                "VerStruct.parse_version did not allow valid legacy style version %s through"
                % test_v,
            )
            self.assertEqual(
                test_v_res,
                v_res,
                "Test string %s did not parse to expected data %s"
                % (test_v, str(v_res)),
            )

        correct_versions_modern = [
            (
                "3.4.0-rc.5+1.20170914160830",
                VerStruct(
                    addon_version=(3, 4, 0),
                    build_type=xplane_constants.BUILD_TYPE_RC,
                    build_type_version=5,
                    data_model_version=1,
                    build_number="20170914160830",
                ),
            )
        ]

        for test_v, test_v_res in correct_versions_modern:
            v_res = VerStruct.parse_version(test_v)
            self.assertIsNotNone(
                v_res,
                "VerStruct.parse_version did not allow valid modern style version %s through"
                % test_v,
            )
            self.assertEqual(
                test_v_res,
                v_res,
                "Test string %s did not parse to expected data %s"
                % (test_v, str(v_res)),
            )

    def test_rich_compare(self):
        # The following are made up and may not represent reality or the history
        # of XPlane2Blender's development
        legacy = VerStruct.parse_version("3.3.12")
        beta_4 = VerStruct.parse_version("3.4.0")
        beta_5 = VerStruct.parse_version("3.4.0-beta.5+1.NO_BUILD_NUMBR")
        rc_1_rebuild_1 = VerStruct.parse_version("3.4.0-rc.1+1.20170923121212")
        rc_1_rebuild_2 = VerStruct.parse_version("3.4.0-rc.1+1.20170924121212")
        rc_1 = VerStruct.parse_version("3.4.0-rc.1+1.NO_BUILD_NUMBR")
        rc_2 = VerStruct.parse_version("3.4.0-rc.2+2.20170922121212")
        rc_2_rebuild = VerStruct.parse_version(
            "3.4.0-rc.2+3.20170921121212"
        )  # Here the data model version has increased but was built a day before. Represents checkign out a previous commit and building from it

        ver_future_dev = VerStruct.parse_version("3.4.1-dev.0+3.NO_BUILD_NUMBR")
        ver_future_alpha = VerStruct.parse_version("3.4.1-alpha.1+3.20170925121212")

        self.assertTrue(
            legacy
            < beta_4
            < beta_5
            < rc_1_rebuild_1
            <= rc_1_rebuild_2
            <= rc_1
            < rc_2
            <= rc_2_rebuild
            < ver_future_dev
            < ver_future_alpha,
            "VerStruct.__lt__ not implemented correctly",
        )
        self.assertTrue(
            ver_future_alpha
            > ver_future_dev
            > rc_2_rebuild
            >= rc_2
            > rc_1
            >= rc_1_rebuild_2
            >= rc_1_rebuild_1
            > beta_5
            > beta_4
            > legacy,
            "VerStruct.__gt__ not implemented correctly",
        )

        legacy_copy = VerStruct.parse_version("3.3.12")
        self.assertEqual(
            legacy, legacy_copy, "VerStruct.__eq__ not implemented correctly"
        )
        self.assertNotEqual(
            legacy, beta_4, "VerStruct.__ne__ not implemented correctly"
        )


runTestCases([TestBuildNumberVerStruct])
