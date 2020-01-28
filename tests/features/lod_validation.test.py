import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line:Tuple[str])->bool:
    return (isinstance(line[0],str)
            and ("ATTR_LOD" in line[0]
                 or "TRIS" in line[0]))

class TestLodValidation(XPlaneTestCase):
    def _test_fail_case(self, name:str, num_errors:int=1):
        out = self.exportExportableRoot(name[5:])
        self.assertLoggerErrors(num_errors)

    def _test_passing_case(self, filename:str):
        self.assertRootObjectExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filename,
            filterLines
        )

    def test_fail_2a_additive_ordered_backwards(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_2b_additive_ordered_out_of_order(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_3a_selective_ordered_backwards(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_3b_selective_ordered_out_of_order(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename, num_errors=2)

    def test_fail_3c_selective_ordered_out_of_order_decreasing_ranges(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename,num_errors=2)

    def test_fail_4a_additive_to_selective_mixed(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_4b_selective_to_additive_mixed(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_5a_selective_far_near_equal_gap(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename, num_errors=2)

    def test_fail_5b_selective_far_near_equal_overlap(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename, num_errors=2)

    def test_fail_6a_selective_1st_near_is_0(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_7a_additive_bucket_near_is_far(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_fail_7b_selective_bucket_near_is_far(self)->None:
        filename = inspect.stack()[0].function
        self._test_fail_case(filename)

    def test_pass_1_validations_not_applied(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_2a_additive_ordered(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_3a_selective_ordered(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_4a_additive_not_mixed(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_4b_selective_not_mixed(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_5a_selective_far_near_equal(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_6a_selective_1st_near_is_0(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)

    def test_pass_7a_1st_lod_is_1st_command(self)->None:
        filename = inspect.stack()[0].function
        self._test_passing_case(filename)


runTestCases([TestLodValidation])
